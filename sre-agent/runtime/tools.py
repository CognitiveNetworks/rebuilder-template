"""Tool definitions and executor for the SRE agent.

Each tool maps to an action the agent can request during the
agentic loop. Tools are defined as tool_use schemas and
executed by the ToolExecutor.
"""

import json
import logging
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Any

import httpx

from models import ScalingConfig
from telemetry import get_tracer

logger = logging.getLogger(__name__)


# --- Tool Definitions (tool_use format) ---

TOOL_DEFINITIONS = [
    {
        "name": "call_ops_endpoint",
        "description": (
            "Call an /ops/* endpoint on a monitored service. "
            "Use GET for diagnostic endpoints (status, health, metrics, config, "
            "dependencies, errors). Use POST for remediation endpoints (drain, "
            "cache/flush, circuits, loglevel). All remediation actions are "
            "idempotent and non-destructive."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Name of the service from the service registry.",
                },
                "endpoint": {
                    "type": "string",
                    "description": (
                        "The /ops/* endpoint path. Examples: /ops/status, "
                        "/ops/health, /ops/metrics, /ops/errors, "
                        "/ops/dependencies, /ops/config, /ops/drain, "
                        "/ops/cache/flush, /ops/circuits, /ops/loglevel"
                    ),
                },
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST"],
                    "description": "HTTP method. GET for diagnostics, POST for remediation.",
                },
                "body": {
                    "type": "object",
                    "description": "Optional JSON body for POST requests.",
                },
            },
            "required": ["service_name", "endpoint", "method"],
        },
    },
    {
        "name": "query_cloud_logs",
        "description": (
            "Query cloud provider logs for a specific service. Read-only. "
            "Use this to search for error patterns, trace requests, or "
            "correlate events across services."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Name of the service to query logs for.",
                },
                "query": {
                    "type": "string",
                    "description": (
                        "Log query string. Format depends on cloud provider: "
                        "GCP uses Cloud Logging filter syntax, "
                        "AWS uses CloudWatch Logs Insights syntax."
                    ),
                },
                "time_range_minutes": {
                    "type": "integer",
                    "description": "How far back to search, in minutes. Default 30.",
                    "default": 30,
                },
            },
            "required": ["service_name", "query"],
        },
    },
    {
        "name": "query_cloud_metrics",
        "description": (
            "Query cloud provider metrics for a managed service or resource. "
            "Read-only. Use this to check CPU, memory, connection counts, "
            "replication lag, queue depth, or other infrastructure metrics."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "resource": {
                    "type": "string",
                    "description": (
                        "The cloud resource to query. Examples: "
                        "cloud-sql/my-instance, gke/my-cluster, "
                        "rds/my-instance, elasticache/my-cluster"
                    ),
                },
                "metric": {
                    "type": "string",
                    "description": (
                        "The metric name. Examples: cpu_utilization, "
                        "memory_utilization, connection_count, "
                        "replication_lag_seconds, queue_depth"
                    ),
                },
                "time_range_minutes": {
                    "type": "integer",
                    "description": "How far back to query, in minutes. Default 15.",
                    "default": 15,
                },
            },
            "required": ["resource", "metric"],
        },
    },
    {
        "name": "escalate_pagerduty",
        "description": (
            "Escalate an incident to a human responder via PagerDuty. "
            "Use this when the agent cannot confidently resolve the issue. "
            "Include the full diagnostic summary and recommended next action."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "incident_id": {
                    "type": "string",
                    "description": "The PagerDuty incident ID to escalate.",
                },
                "escalation_message": {
                    "type": "string",
                    "description": (
                        "Summary for the human responder: what was checked, "
                        "what was found, what was tried, and recommended next action."
                    ),
                },
            },
            "required": ["incident_id", "escalation_message"],
        },
    },
    {
        "name": "acknowledge_alert",
        "description": (
            "Acknowledge a PagerDuty alert. Use this when the issue has been "
            "resolved by the agent or has self-resolved."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "incident_id": {
                    "type": "string",
                    "description": "The PagerDuty incident ID to acknowledge.",
                },
                "resolution_note": {
                    "type": "string",
                    "description": "Brief description of how the issue was resolved.",
                },
            },
            "required": ["incident_id", "resolution_note"],
        },
    },
    {
        "name": "write_incident_report",
        "description": (
            "Write an incident report to the incidents directory. "
            "Call this at the end of every alert response, whether "
            "resolved or escalated."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": (
                        "Filename for the report. Format: "
                        "YYYY-MM-DD-HH-MM-<service>-<dedup_key>.md"
                    ),
                },
                "content": {
                    "type": "string",
                    "description": "Full markdown content of the incident report.",
                },
            },
            "required": ["filename", "content"],
        },
    },
    {
        "name": "email_incident_report",
        "description": (
            "Email an incident report after writing it to disk. "
            "Call this immediately after write_incident_report to send "
            "the report to the configured recipients via email."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": {
                    "type": "string",
                    "description": (
                        "Email subject line. Format: "
                        "[P1/P2/P3/P4] Incident Report — <service> — <brief description>"
                    ),
                },
                "content": {
                    "type": "string",
                    "description": "Full markdown content of the incident report.",
                },
            },
            "required": ["subject", "content"],
        },
    },
    {
        "name": "create_pagerduty_incident",
        "description": (
            "Create a NEW PagerDuty incident to page a human responder. "
            "Use this when the alert came from GCP Cloud Monitoring (no existing "
            "PagerDuty incident) and the agent cannot resolve the issue. "
            "This is how humans get paged — only call this when escalation is needed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": (
                        "Brief summary for the PagerDuty incident. Include service name, "
                        "what's wrong, and what the agent tried."
                    ),
                },
                "severity": {
                    "type": "string",
                    "enum": ["critical", "error", "warning", "info"],
                    "description": "Incident severity level.",
                },
                "details": {
                    "type": "string",
                    "description": (
                        "Full diagnostic details: what was checked, what was found, "
                        "what was tried, and recommended next action for the human."
                    ),
                },
            },
            "required": ["summary", "severity", "details"],
        },
    },
    {
        "name": "scale_service",
        "description": (
            "Scale a service to a target instance count. Two modes: "
            "'application' calls POST /ops/scale on the service, "
            "'cloud_native' adjusts replica count via cloud provider API. "
            "The target must be within the service's configured min/max bounds. "
            "Always use an absolute target, never a relative increment."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Name of the service from the service registry.",
                },
                "target_instances": {
                    "type": "integer",
                    "minimum": 1,
                    "description": (
                        "The desired instance count. Must be between the "
                        "service's configured min and max."
                    ),
                },
                "reason": {
                    "type": "string",
                    "description": (
                        "Why scaling is needed. Logged in the incident report. "
                        "Example: 'All instances saturated due to traffic spike, "
                        "scaling from 3 to 6 instances.'"
                    ),
                },
            },
            "required": ["service_name", "target_instances", "reason"],
        },
    },
]


class ToolExecutor:
    """Executes tool calls requested by the SRE agent."""

    def __init__(
        self,
        services: dict[str, str],
        ops_auth_token: str,
        pagerduty_api_token: str,
        incidents_dir: str,
        trace_id: str = "",
        scaling_config: dict[str, ScalingConfig] | None = None,
        smtp_config: dict[str, str] | None = None,
        pagerduty_routing_key: str = "",
    ) -> None:
        self.services = services  # name -> base_url
        self.ops_auth_token = ops_auth_token
        self.pagerduty_api_token = pagerduty_api_token
        self.pagerduty_routing_key = pagerduty_routing_key
        self.incidents_dir = Path(incidents_dir)
        self.trace_id = trace_id
        self.scaling_config = scaling_config or {}
        self.smtp_config = smtp_config or {}
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def execute(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        """Execute a tool call and return the result as a string."""
        logger.info(
            "Executing tool: tool=%s trace_id=%s", tool_name, self.trace_id
        )

        handlers = {
            "call_ops_endpoint": self._call_ops_endpoint,
            "query_cloud_logs": self._query_cloud_logs,
            "query_cloud_metrics": self._query_cloud_metrics,
            "escalate_pagerduty": self._escalate_pagerduty,
            "acknowledge_alert": self._acknowledge_alert,
            "create_pagerduty_incident": self._create_pagerduty_incident,
            "write_incident_report": self._write_incident_report,
            "email_incident_report": self._email_incident_report,
            "scale_service": self._scale_service,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

        try:
            return await handler(tool_input)
        except Exception as e:
            logger.exception(
                "Tool execution failed: tool=%s trace_id=%s",
                tool_name,
                self.trace_id,
            )
            return json.dumps({"error": str(e)})

    def _base_headers(self) -> dict[str, str]:
        """Build common headers with trace ID for request correlation."""
        headers: dict[str, str] = {}
        if self.trace_id:
            headers["X-Trace-Id"] = self.trace_id
        return headers

    async def _call_ops_endpoint(self, input: dict[str, Any]) -> str:
        """Call an /ops/* endpoint on a monitored service."""
        tracer = get_tracer()
        service_name = input.get("service_name", "")
        endpoint = input.get("endpoint", "")
        method = input.get("method", "GET")

        # Validate inputs
        if not service_name or not endpoint:
            return json.dumps({"error": "service_name and endpoint are required"})

        if not endpoint.startswith("/ops/"):
            return json.dumps(
                {"error": f"Endpoint must start with /ops/: {endpoint}"}
            )

        if method not in ("GET", "POST"):
            return json.dumps(
                {"error": f"Method must be GET or POST: {method}"}
            )

        base_url = self.services.get(service_name)
        if not base_url:
            return json.dumps({"error": f"Unknown service: {service_name}"})

        url = f"{base_url.rstrip('/')}{endpoint}"
        headers = self._base_headers()
        if self.ops_auth_token:
            headers["Authorization"] = f"Bearer {self.ops_auth_token}"

        with tracer.start_as_current_span(
            "sre_agent.tool.call_ops_endpoint",
            attributes={
                "ops.service": service_name,
                "ops.endpoint": endpoint,
                "ops.method": method,
            },
        ):
            if method == "GET":
                response = await self.http_client.get(url, headers=headers)
            else:
                body = input.get("body", {})
                response = await self.http_client.post(url, headers=headers, json=body)

        content_type = response.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            body_data = response.json()
        else:
            body_data = response.text

        return json.dumps({
            "status_code": response.status_code,
            "body": body_data,
        })

    async def _query_cloud_logs(self, input: dict[str, Any]) -> str:
        """Query cloud provider logs.

        TODO: Implement for your cloud provider.
        GCP: Use Cloud Logging API (google-cloud-logging)
        AWS: Use CloudWatch Logs Insights (boto3)
        """
        return json.dumps({
            "error": "Cloud log querying not yet implemented. "
            "Implement _query_cloud_logs for your cloud provider."
        })

    async def _query_cloud_metrics(self, input: dict[str, Any]) -> str:
        """Query cloud provider metrics.

        TODO: Implement for your cloud provider.
        GCP: Use Cloud Monitoring API (google-cloud-monitoring)
        AWS: Use CloudWatch GetMetricData (boto3)
        """
        return json.dumps({
            "error": "Cloud metrics querying not yet implemented. "
            "Implement _query_cloud_metrics for your cloud provider."
        })

    async def _escalate_pagerduty(self, input: dict[str, Any]) -> str:
        """Escalate an incident via PagerDuty API.

        For GCP-sourced alerts (incident_id starts with 'gcp-'), creates a
        NEW PagerDuty incident via Events API v2 since no PD incident exists.
        For PagerDuty-sourced alerts, escalates the existing incident.
        """
        incident_id = input.get("incident_id", "")
        message = input.get("escalation_message", "")

        if not incident_id or not message:
            return json.dumps(
                {"error": "incident_id and escalation_message are required"}
            )

        # GCP-sourced alert — no PD incident exists, create one
        if incident_id.startswith("gcp-"):
            return await self._create_pagerduty_incident({
                "summary": f"[SRE Agent Escalation] {message[:200]}",
                "severity": "critical",
                "details": message,
            })

        headers = self._base_headers()
        headers["Authorization"] = f"Token token={self.pagerduty_api_token}"
        headers["Content-Type"] = "application/json"

        response = await self.http_client.post(
            f"https://api.pagerduty.com/incidents/{incident_id}/notes",
            headers=headers,
            json={
                "note": {
                    "content": f"[SRE Agent Escalation]\n\n{message}",
                }
            },
        )

        # Trigger escalation
        await self.http_client.put(
            f"https://api.pagerduty.com/incidents/{incident_id}",
            headers=headers,
            json={
                "incident": {
                    "type": "incident_reference",
                    "escalation_level": 2,
                }
            },
        )

        logger.info(
            "Escalated: incident_id=%s trace_id=%s", incident_id, self.trace_id
        )

        return json.dumps({
            "status": "escalated",
            "incident_id": incident_id,
            "note_status": response.status_code,
        })

    async def _acknowledge_alert(self, input: dict[str, Any]) -> str:
        """Acknowledge a PagerDuty incident.

        For GCP-sourced alerts (incident_id starts with 'gcp-'), no PagerDuty
        incident exists — the agent resolved it without paging anyone.
        """
        incident_id = input.get("incident_id", "")
        note = input.get("resolution_note", "")

        if not incident_id or not note:
            return json.dumps(
                {"error": "incident_id and resolution_note are required"}
            )

        # GCP-sourced alert — no PD incident to acknowledge
        if incident_id.startswith("gcp-"):
            logger.info(
                "GCP alert resolved by agent (no PD incident): incident_id=%s "
                "note=%s trace_id=%s",
                incident_id,
                note[:200],
                self.trace_id,
            )
            return json.dumps({
                "status": "resolved_by_agent",
                "incident_id": incident_id,
                "message": "GCP-sourced alert resolved without paging humans.",
            })

        headers = self._base_headers()
        headers["Authorization"] = f"Token token={self.pagerduty_api_token}"
        headers["Content-Type"] = "application/json"

        # Add resolution note
        await self.http_client.post(
            f"https://api.pagerduty.com/incidents/{incident_id}/notes",
            headers=headers,
            json={
                "note": {
                    "content": f"[SRE Agent Resolution]\n\n{note}",
                }
            },
        )

        # Acknowledge the incident
        response = await self.http_client.put(
            f"https://api.pagerduty.com/incidents/{incident_id}",
            headers=headers,
            json={
                "incident": {
                    "type": "incident_reference",
                    "status": "acknowledged",
                }
            },
        )

        logger.info(
            "Acknowledged: incident_id=%s trace_id=%s", incident_id, self.trace_id
        )

        return json.dumps({
            "status": "acknowledged",
            "incident_id": incident_id,
            "response_status": response.status_code,
        })

    async def _create_pagerduty_incident(self, input: dict[str, Any]) -> str:
        """Create a NEW PagerDuty incident via Events API v2.

        Used when the SRE agent cannot resolve an issue and needs to
        page a human. This is the only path that creates a PagerDuty
        incident — alerts from GCP go to the agent first.
        """
        summary = input.get("summary", "")
        severity = input.get("severity", "critical")
        details = input.get("details", "")

        if not summary:
            return json.dumps({"error": "summary is required"})

        if not self.pagerduty_routing_key:
            return json.dumps({
                "error": "PAGERDUTY_ROUTING_KEY not configured. "
                "Cannot create PagerDuty incidents."
            })

        payload = {
            "routing_key": self.pagerduty_routing_key,
            "event_action": "trigger",
            "dedup_key": f"sre-agent-{self.trace_id}" if self.trace_id else None,
            "payload": {
                "summary": summary,
                "severity": severity,
                "source": "sre-agent",
                "custom_details": {
                    "agent_trace_id": self.trace_id,
                    "diagnostic_details": details,
                },
            },
        }

        response = await self.http_client.post(
            "https://events.pagerduty.com/v2/enqueue",
            json=payload,
        )

        if response.status_code == 202:
            result = response.json()
            logger.info(
                "PagerDuty incident created: dedup_key=%s trace_id=%s",
                result.get("dedup_key", ""),
                self.trace_id,
            )
            return json.dumps({
                "status": "incident_created",
                "dedup_key": result.get("dedup_key", ""),
                "message": result.get("message", ""),
            })
        else:
            logger.error(
                "Failed to create PagerDuty incident: status=%d body=%s trace_id=%s",
                response.status_code,
                response.text,
                self.trace_id,
            )
            return json.dumps({
                "error": f"PagerDuty Events API returned {response.status_code}",
                "body": response.text,
            })

    async def _write_incident_report(self, input: dict[str, Any]) -> str:
        """Write an incident report to the incidents directory."""
        filename = input.get("filename", "")
        content = input.get("content", "")

        if not filename or not content:
            return json.dumps({"error": "filename and content are required"})

        # Prevent path traversal — only allow the basename
        safe_name = Path(filename).name
        if safe_name != filename:
            return json.dumps({
                "error": f"Invalid filename (path traversal rejected): {filename}"
            })

        self.incidents_dir.mkdir(parents=True, exist_ok=True)
        filepath = self.incidents_dir / safe_name
        filepath.write_text(content)

        # Log the full incident report so it's always visible in Cloud Run
        # logs (Cloud Logging) even without SMTP or persistent disk
        logger.info(
            "Incident report written: path=%s trace_id=%s",
            filepath,
            self.trace_id,
        )
        logger.info(
            "INCIDENT_REPORT: filename=%s trace_id=%s\n%s",
            safe_name,
            self.trace_id,
            content,
        )

        return json.dumps({
            "status": "written",
            "path": str(filepath),
        })

    async def _email_incident_report(self, input: dict[str, Any]) -> str:
        """Email an incident report to configured recipients via SMTP."""
        subject = input.get("subject", "")
        content = input.get("content", "")

        if not subject or not content:
            return json.dumps({"error": "subject and content are required"})

        smtp_host = self.smtp_config.get("host", "")
        smtp_port = int(self.smtp_config.get("port", "587"))
        smtp_user = self.smtp_config.get("username", "")
        smtp_pass = self.smtp_config.get("password", "")
        smtp_from = self.smtp_config.get("from", smtp_user)
        smtp_to = self.smtp_config.get("to", "")

        if not smtp_host or not smtp_to:
            return json.dumps({
                "error": "SMTP not configured. Set SMTP_HOST and SMTP_TO environment variables."
            })

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = smtp_from
        msg["To"] = smtp_to
        msg.set_content(content)

        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.starttls()
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.send_message(msg)

            logger.info(
                "Incident report emailed: to=%s subject=%s trace_id=%s",
                smtp_to,
                subject,
                self.trace_id,
            )

            return json.dumps({
                "status": "sent",
                "to": smtp_to,
                "subject": subject,
            })
        except Exception as e:
            logger.error(
                "Failed to send incident report email: error=%s trace_id=%s",
                str(e),
                self.trace_id,
            )
            return json.dumps({"error": f"Email send failed: {str(e)}"})

    async def _scale_service(self, input: dict[str, Any]) -> str:
        """Scale a service to a target instance count within configured bounds."""
        tracer = get_tracer()
        service_name = input.get("service_name", "")
        target = input.get("target_instances", 0)
        reason = input.get("reason", "")

        if not service_name or not target or not reason:
            return json.dumps(
                {"error": "service_name, target_instances, and reason are required"}
            )

        # Validate service has scaling config
        scaling = self.scaling_config.get(service_name)
        if not scaling:
            return json.dumps({
                "error": f"Service '{service_name}' does not have scaling limits "
                f"configured. Cannot scale. Escalate to a human for "
                f"capacity changes."
            })

        # Validate bounds
        if target < scaling.min_instances:
            return json.dumps({
                "error": f"Target {target} is below minimum ({scaling.min_instances}) "
                f"for service '{service_name}'."
            })
        if target > scaling.max_instances:
            return json.dumps({
                "error": f"Target {target} exceeds maximum ({scaling.max_instances}) "
                f"for service '{service_name}'. Escalate for capacity planning."
            })

        logger.info(
            "Scaling service: service=%s target=%d mode=%s reason=%s trace_id=%s",
            service_name,
            target,
            scaling.mode,
            reason,
            self.trace_id,
        )

        if scaling.mode == "application":
            # Call POST /ops/scale on the service
            base_url = self.services.get(service_name)
            if not base_url:
                return json.dumps(
                    {"error": f"Service '{service_name}' not in service registry"}
                )

            url = f"{base_url.rstrip('/')}/ops/scale"
            headers = self._base_headers()
            if self.ops_auth_token:
                headers["Authorization"] = f"Bearer {self.ops_auth_token}"

            with tracer.start_as_current_span(
                "sre_agent.tool.scale_service",
                attributes={
                    "scale.service": service_name,
                    "scale.target": target,
                    "scale.mode": "application",
                },
            ):
                response = await self.http_client.post(
                    url,
                    headers=headers,
                    json={"target_instances": target, "reason": reason},
                )

            content_type = response.headers.get("content-type", "")
            if content_type.startswith("application/json"):
                body_data = response.json()
            else:
                body_data = response.text

            return json.dumps({
                "status": "scaling_requested",
                "mode": "application",
                "service": service_name,
                "target_instances": target,
                "response_status": response.status_code,
                "response_body": body_data,
            })

        elif scaling.mode == "cloud_native":
            # TODO: Implement for your cloud provider.
            # GCP Cloud Run: Use google-cloud-run to update service instance count
            # GCP GKE: Use google-cloud-container to update deployment replicas
            # AWS ECS: Use boto3 to update service desired count
            # AWS EKS: Use boto3 to update deployment replicas
            return json.dumps({
                "error": "Cloud-native scaling not yet implemented. "
                "Implement _scale_service cloud_native mode for your "
                "cloud provider in tools.py."
            })

        return json.dumps({"error": f"Unknown scaling mode: {scaling.mode}"})

    async def close(self) -> None:
        """Clean up HTTP client."""
        await self.http_client.aclose()
