"""Pydantic models for PagerDuty webhooks and internal types."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AlertSeverity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    WARNING = "warning"
    INFO = "info"


class Priority(StrEnum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class PagerDutyAlert(BaseModel):
    """Parsed PagerDuty V3 webhook alert payload."""

    incident_id: str
    service_name: str
    severity: AlertSeverity
    priority: Priority | None = None
    description: str
    dedup_key: str | None = None
    runbook_url: str | None = None
    timestamp: datetime
    details: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_webhook(cls, payload: dict[str, Any]) -> "PagerDutyAlert":
        """Parse a PagerDuty V3 webhook payload into a structured alert.

        Adapt this method to match your PagerDuty webhook configuration.
        The V3 webhook format nests data under event.data.
        """
        event = payload.get("event", {})
        data = event.get("data", {})
        service = data.get("service", {})
        priority_data = data.get("priority") or {}

        severity_map = {
            "critical": AlertSeverity.CRITICAL,
            "high": AlertSeverity.HIGH,
            "warning": AlertSeverity.WARNING,
            "info": AlertSeverity.INFO,
        }

        priority_map = {
            "P1": Priority.P1,
            "P2": Priority.P2,
            "P3": Priority.P3,
            "P4": Priority.P4,
        }

        return cls(
            incident_id=data.get("id", "unknown"),
            service_name=service.get("summary", "unknown"),
            severity=severity_map.get(
                data.get("urgency", "high"), AlertSeverity.HIGH
            ),
            priority=priority_map.get(
                priority_data.get("summary", ""), None
            ),
            description=data.get("title", data.get("summary", "No description")),
            dedup_key=data.get("incident_key"),
            runbook_url=data.get("body", {}).get("details", {}).get("runbook_url"),
            timestamp=datetime.fromisoformat(
                data.get("created_at", datetime.now().isoformat())
            ),
            details=data.get("body", {}).get("details", {}),
        )


    @classmethod
    def from_gcp_webhook(
        cls,
        payload: dict[str, Any],
        services: list["ServiceEndpoint"] | None = None,
    ) -> "PagerDutyAlert":
        """Parse a GCP Cloud Monitoring webhook payload into a structured alert.

        GCP sends alerts directly to the SRE agent (no PagerDuty incident exists).
        The incident_id is prefixed with 'gcp-' to signal that there is no
        PagerDuty incident — escalation must CREATE one via Events API v2.

        If ``services`` is provided, the host from the alert is matched against
        registered service base URLs to resolve the correct service name.
        """
        incident = payload.get("incident", {})
        resource = incident.get("resource", {})
        resource_labels = resource.get("labels", {})

        # Map GCP alert state to severity
        state = incident.get("state", "open")
        severity = AlertSeverity.CRITICAL if state == "open" else AlertSeverity.INFO

        # Resolve service name by matching the alert host to service registry URLs
        host = resource_labels.get("host", "")
        service_name = "unknown"
        if host and services:
            for svc in services:
                if host in svc.base_url:
                    service_name = svc.name
                    break
        if service_name == "unknown" and host:
            # Fallback: use the full hostname prefix as service name
            service_name = host.split(".")[0]

        started_at = incident.get("started_at", 0)
        ts = (
            datetime.fromtimestamp(started_at)
            if started_at
            else datetime.now()
        )

        return cls(
            incident_id=f"gcp-{incident.get('incident_id', 'unknown')}",
            service_name=service_name,
            severity=severity,
            priority=Priority.P1 if severity == AlertSeverity.CRITICAL else Priority.P3,
            description=incident.get("summary", incident.get("condition_name", "GCP alert")),
            dedup_key=incident.get("incident_id"),
            runbook_url=None,
            timestamp=ts,
            details={
                "source": "gcp_cloud_monitoring",
                "policy_name": incident.get("policy_name", ""),
                "condition_name": incident.get("condition_name", ""),
                "resource_type": resource.get("type", ""),
                "resource_labels": resource_labels,
                "gcp_incident_url": incident.get("url", ""),
                "documentation": incident.get("documentation", {}).get("content", ""),
            },
        )


class ServiceEndpoint(BaseModel):
    """A monitored service and its /ops/* base URL."""

    name: str
    base_url: str
    critical: bool = True


class ScalingMode(StrEnum):
    APPLICATION = "application"
    CLOUD_NATIVE = "cloud_native"


class ScalingConfig(BaseModel):
    """Per-service scaling bounds and mode."""

    service_name: str
    min_instances: int = Field(ge=1)
    max_instances: int = Field(ge=1)
    mode: ScalingMode


class ToolCall(BaseModel):
    """A tool call requested by the SRE agent."""

    name: str
    input: dict[str, Any]


class ToolResult(BaseModel):
    """The result of executing a tool call."""

    tool_use_id: str
    content: str
    is_error: bool = False
