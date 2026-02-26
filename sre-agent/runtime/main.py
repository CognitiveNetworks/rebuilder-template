"""SRE Agent runtime — FastAPI webhook receiver.

Receives PagerDuty V3 webhooks, parses the alert, and runs the
agentic diagnostic loop via an OpenAI-compatible LLM API
(GitHub Models, OpenAI, Azure OpenAI, etc.).

Exposes /ops/* endpoints for its own observability, following the same
contract that all services in the platform implement.

Exposes /alerts/* endpoints for querying pending/active alerts.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request

from agent import run_agent
from config import Config
from intake import AlertIntake
from models import PagerDutyAlert
from state import RuntimeState
from telemetry import (
    agent_run_duration_histogram,
    agent_runs_completed_counter,
    agent_runs_failed_counter,
    get_tracer,
    incidents_active_updown,
    init_telemetry,
    shutdown_telemetry,
    tokens_input_counter,
    tokens_output_counter,
    tokens_per_run_histogram,
    webhooks_failed_counter,
    webhooks_ignored_counter,
    webhooks_processed_counter,
    webhooks_received_counter,
)

# --- Structured JSON Logging ---


class _JsonFormatter(logging.Formatter):
    """Emit structured JSON log lines for log aggregation systems."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Propagate trace and incident context when available
        for attr in ("trace_id", "incident_id"):
            if hasattr(record, attr):
                entry[attr] = getattr(record, attr)
        if record.exc_info and record.exc_info[0]:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry)


_handler = logging.StreamHandler()
_handler.setFormatter(_JsonFormatter())
logging.root.handlers = [_handler]
logging.root.setLevel(logging.INFO)
logger = logging.getLogger(__name__)

config = Config()
state = RuntimeState()
intake: AlertIntake | None = None

# --- Alert Queue (observability) ---
# Stores alerts by incident_id with status: processing, done, failed, escalated
_alert_queue: dict[str, dict[str, Any]] = {}


# --- Lifespan ---


@asynccontextmanager
async def lifespan(the_app: FastAPI):
    global intake  # noqa: PLW0603

    # Initialize OpenTelemetry (no-op if OTEL_EXPORTER_OTLP_ENDPOINT not set)
    init_telemetry(app=the_app)

    # Initialize alert intake pipeline
    intake = AlertIntake(
        process_fn=_process_alert,
        state=state,
        max_concurrent=config.max_concurrent_alerts,
        queue_ttl_seconds=config.alert_queue_ttl_seconds,
    )

    logger.info(
        "SRE Agent starting — %d services, max_concurrent=%d, queue_ttl=%ds",
        len(config.services),
        config.max_concurrent_alerts,
        config.alert_queue_ttl_seconds,
    )
    for svc in config.services:
        logger.info("  %s: %s (critical=%s)", svc.name, svc.base_url, svc.critical)
    yield

    # Graceful shutdown via intake pipeline
    if intake is not None:
        await intake.shutdown()

    # Fallback: wait for any active_incidents not managed by intake
    if state.active_incidents:
        logger.info(
            "Waiting for %d active incidents to complete...",
            len(state.active_incidents),
        )
        for _ in range(30):  # Wait up to 30 seconds
            if not state.active_incidents:
                break
            await asyncio.sleep(1)
        if state.active_incidents:
            logger.warning(
                "Shutting down with %d incidents still active",
                len(state.active_incidents),
            )
    shutdown_telemetry()
    logger.info("SRE Agent shutting down")


app = FastAPI(title="SRE Agent", lifespan=lifespan)


# --- Health Check ---


@app.get("/health")
async def health() -> dict[str, Any]:
    """Health check for container orchestration.

    Verifies that the service is configured and the system prompt is
    readable. For deep dependency checks, use /ops/health.
    """
    checks: dict[str, str] = {}
    healthy = True

    # Verify system prompt is readable
    prompt_path = Path(config.sre_prompt_path)
    if prompt_path.exists() and prompt_path.stat().st_size > 0:
        checks["system_prompt"] = "ok"
    else:
        checks["system_prompt"] = f"missing or empty: {config.sre_prompt_path}"
        healthy = False

    # Verify required config is present
    if config.vertex_ai:
        checks["llm_provider"] = "vertex_ai (ADC)"
    elif config.llm_api_key:
        checks["llm_provider"] = "api_key configured"
    else:
        checks["llm_provider"] = "missing"
        healthy = False

    # LLM reachability — the agent is useless without its LLM
    try:
        llm_ok = await _check_llm_reachable()
        checks["llm_api"] = "ok" if llm_ok else "unreachable"
        if not llm_ok:
            healthy = False
    except Exception as e:
        checks["llm_api"] = f"error: {e}"
        healthy = False

    pd_key = "pagerduty_api_token"
    if config.pagerduty_api_token:
        checks[pd_key] = "configured"
    else:
        checks[pd_key] = "missing"
        healthy = False

    if config.services:
        checks["service_registry"] = f"{len(config.services)} services"
    else:
        checks["service_registry"] = "empty"
        healthy = False

    status = "healthy" if healthy else "unhealthy"
    result = {"status": status, "checks": checks, "model": config.llm_model}
    if not healthy:
        raise HTTPException(status_code=503, detail=result)
    return result


# --- Webhook Endpoint ---


@app.post("/webhook")
async def receive_webhook(request: Request) -> dict[str, str]:
    """Receive a PagerDuty V3 webhook and process the alert.

    The alert flows through the intake pipeline which handles dedup,
    service serialization, priority ordering, and concurrency control.
    PagerDuty expects a 2xx response within a few seconds.
    """
    trace_id = str(uuid.uuid4())
    state.webhooks_received += 1
    webhooks_received_counter.add(1)

    # Reject if draining
    if state.draining:
        raise HTTPException(status_code=503, detail="Service is draining")

    body = await request.body()

    # Verify webhook signature if configured
    if config.pagerduty_webhook_secret:
        signature = request.headers.get("x-pagerduty-signature", "")
        if not _verify_signature(body, signature, config.pagerduty_webhook_secret):
            state.webhooks_failed += 1
            webhooks_failed_counter.add(1)
            state.recent_errors.append({
                "timestamp": time.time(),
                "type": "webhook_auth_failure",
                "message": "Invalid webhook signature",
                "trace_id": trace_id,
            })
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload: dict[str, Any] = await request.json()

    # PagerDuty sends various event types — only process incident triggers
    event_type = payload.get("event", {}).get("event_type", "")
    if event_type not in ("incident.triggered", "incident.escalated"):
        state.webhooks_ignored += 1
        webhooks_ignored_counter.add(1)
        logger.info("Ignoring event type: %s (trace_id=%s)", event_type, trace_id)
        return {"status": "ignored", "event_type": event_type}

    try:
        alert = PagerDutyAlert.from_webhook(payload)
    except Exception as exc:
        state.webhooks_failed += 1
        webhooks_failed_counter.add(1)
        state.recent_errors.append({
            "timestamp": time.time(),
            "type": "payload_parse_error",
            "message": "Failed to parse PagerDuty webhook payload",
            "trace_id": trace_id,
        })
        logger.exception(
            "Failed to parse PagerDuty webhook payload (trace_id=%s)", trace_id
        )
        raise HTTPException(status_code=400, detail="Invalid payload") from exc

    logger.info(
        "Alert received: service=%s description=%s severity=%s trace_id=%s",
        alert.service_name,
        alert.description,
        alert.severity.value,
        trace_id,
    )

    state.webhooks_processed += 1
    webhooks_processed_counter.add(1)

    # Submit to intake pipeline (dedup, queue, dispatch)
    disposition = await intake.submit(alert, trace_id)

    return {
        "status": disposition,
        "incident_id": alert.incident_id,
        "trace_id": trace_id,
    }


@app.post("/webhook/gcp")
async def receive_gcp_webhook(request: Request) -> dict[str, str]:
    """Receive a GCP Cloud Monitoring webhook alert directly.

    GCP alerts go to the SRE agent first (no PagerDuty incident).
    The agent diagnoses and only creates a PagerDuty incident if
    it cannot resolve the issue — humans are only paged on escalation.
    """
    trace_id = str(uuid.uuid4())
    state.webhooks_received += 1
    webhooks_received_counter.add(1)

    if state.draining:
        raise HTTPException(status_code=503, detail="Service is draining")

    # Verify auth token (GCP webhook_tokenauth sends it as a query param)
    auth_token = request.query_params.get("auth_token", "")
    if config.ops_auth_token and auth_token:
        if not hmac.compare_digest(auth_token, config.ops_auth_token):
            state.webhooks_failed += 1
            webhooks_failed_counter.add(1)
            raise HTTPException(status_code=401, detail="Invalid auth token")

    payload: dict[str, Any] = await request.json()

    # GCP sends state=closed when the alert resolves — ignore those
    incident_state = payload.get("incident", {}).get("state", "")
    if incident_state != "open":
        state.webhooks_ignored += 1
        webhooks_ignored_counter.add(1)
        logger.info(
            "Ignoring GCP alert with state=%s (trace_id=%s)", incident_state, trace_id
        )
        return {"status": "ignored", "state": incident_state}

    try:
        alert = PagerDutyAlert.from_gcp_webhook(payload, services=config.services)
    except Exception as exc:
        state.webhooks_failed += 1
        webhooks_failed_counter.add(1)
        state.recent_errors.append({
            "timestamp": time.time(),
            "type": "gcp_payload_parse_error",
            "message": "Failed to parse GCP Cloud Monitoring webhook payload",
            "trace_id": trace_id,
        })
        logger.exception(
            "Failed to parse GCP webhook payload (trace_id=%s)", trace_id
        )
        raise HTTPException(status_code=400, detail="Invalid payload") from exc

    logger.info(
        "GCP alert received: service=%s description=%s severity=%s trace_id=%s",
        alert.service_name,
        alert.description,
        alert.severity.value,
        trace_id,
    )

    state.webhooks_processed += 1
    webhooks_processed_counter.add(1)

    disposition = await intake.submit(alert, trace_id)

    return {
        "status": disposition,
        "incident_id": alert.incident_id,
        "trace_id": trace_id,
    }


async def _process_alert(alert: PagerDutyAlert, trace_id: str) -> None:
    """Process an alert through the agentic diagnostic loop."""
    # Store in alert queue for observability
    _alert_queue[alert.incident_id] = {
        "status": "processing",
        "incident_id": alert.incident_id,
        "service_name": alert.service_name,
        "severity": alert.severity.value,
        "priority": alert.priority.value if alert.priority else None,
        "description": alert.description,
        "timestamp": alert.timestamp.isoformat(),
        "trace_id": trace_id,
        "queued_at": time.time(),
    }

    tracer = get_tracer()
    with tracer.start_as_current_span(
        "sre_agent.process_alert",
        attributes={
            "incident.id": alert.incident_id,
            "incident.service": alert.service_name,
            "incident.severity": alert.severity.value,
        },
    ):
        # Check hourly token budget before running the agent
        if _is_hourly_budget_exhausted():
            logger.warning(
                "Hourly token budget exhausted, escalating without diagnosis: "
                "incident_id=%s trace_id=%s",
                alert.incident_id,
                trace_id,
            )
            state.agent_runs_completed += 1
            agent_runs_completed_counter.add(1)
            state.active_incidents.pop(alert.incident_id, None)
            incidents_active_updown.add(-1)
            _alert_queue[alert.incident_id]["status"] = "escalated"
            await _escalate_budget_exhausted(alert, trace_id, "hourly")
            return

        start = time.time()
        try:
            result = await run_agent(alert, config, trace_id=trace_id)
            duration = time.time() - start
            state.agent_runs_completed += 1
            agent_runs_completed_counter.add(1)
            state.run_durations.append(duration)
            agent_run_duration_histogram.record(duration)
            state.active_incidents.pop(alert.incident_id, None)
            incidents_active_updown.add(-1)

            # Record token usage
            run_tokens = result.input_tokens + result.output_tokens
            state.total_input_tokens += result.input_tokens
            state.total_output_tokens += result.output_tokens
            state.run_token_usage.append(run_tokens)
            state.hourly_token_log.append((time.time(), run_tokens))
            tokens_input_counter.add(result.input_tokens)
            tokens_output_counter.add(result.output_tokens)
            tokens_per_run_histogram.record(run_tokens)
            state.total_estimated_cost_usd += result.estimated_cost_usd

            _alert_queue[alert.incident_id]["status"] = "done"

            models_str = "+".join(result.models_used) if result.models_used else "unknown"
            logger.info(
                "Agent completed: incident_id=%s duration=%.1fs turns=%d "
                "tokens=%d (in=%d out=%d) cost=$%.4f models=%s trace_id=%s summary=%s",
                alert.incident_id,
                duration,
                result.turns,
                run_tokens,
                result.input_tokens,
                result.output_tokens,
                result.estimated_cost_usd,
                models_str,
                trace_id,
                result.summary[:200],
            )

            # Append cost footer to the most recent incident report
            _append_cost_to_report(
                alert.incident_id, result, duration, models_str
            )
        except Exception:
            duration = time.time() - start
            state.agent_runs_failed += 1
            agent_runs_failed_counter.add(1)
            state.run_durations.append(duration)
            agent_run_duration_histogram.record(duration)
            state.active_incidents.pop(alert.incident_id, None)
            incidents_active_updown.add(-1)
            _alert_queue[alert.incident_id]["status"] = "failed"
            state.recent_errors.append({
                "timestamp": time.time(),
                "type": "agent_failure",
                "message": f"Agent failed for incident {alert.incident_id}",
                "incident_id": alert.incident_id,
                "trace_id": trace_id,
            })
            logger.exception(
                "Agent failed: incident_id=%s trace_id=%s", alert.incident_id, trace_id
            )


# --- Incident Report Cost Footer ---


def _append_cost_to_report(
    incident_id: str,
    result: Any,
    duration: float,
    models_str: str,
) -> None:
    """Append an LLM cost footer to the most recent incident report file.

    The agent writes the incident report during its run, before the final
    cost is known. This appends a footer with the actual token usage and
    estimated cost after the run completes.
    """
    incidents_dir = Path(config.incidents_dir)
    if not incidents_dir.exists():
        return

    # Find the most recent .md file (the agent just wrote it)
    reports = sorted(incidents_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not reports:
        return

    latest = reports[0]
    total_tokens = result.input_tokens + result.output_tokens

    footer = (
        f"\n\n---\n"
        f"## LLM Usage\n\n"
        f"| Metric | Value |\n"
        f"|---|---|\n"
        f"| Models | {models_str} |\n"
        f"| Turns | {result.turns} |\n"
        f"| Input tokens | {result.input_tokens:,} |\n"
        f"| Output tokens | {result.output_tokens:,} |\n"
        f"| Total tokens | {total_tokens:,} |\n"
        f"| Estimated cost | ${result.estimated_cost_usd:.4f} |\n"
        f"| Duration | {duration:.1f}s |\n"
    )

    try:
        with open(latest, "a") as f:
            f.write(footer)
        # Re-read the full report (original + footer) and log it so
        # Cloud Logging has the complete version with cost data.
        full_report = latest.read_text()
        logger.info(
            "INCIDENT_REPORT_FINAL: filename=%s incident_id=%s "
            "tokens=%d cost=$%.4f models=%s\n%s",
            latest.name,
            incident_id,
            total_tokens,
            result.estimated_cost_usd,
            models_str,
            full_report,
        )
    except Exception:
        logger.warning("Failed to append cost footer to %s", latest)


# --- Token Budget Helpers ---


def _tokens_last_hour() -> int:
    """Sum tokens consumed in the last 60 minutes from the rolling log."""
    cutoff = time.time() - 3600
    return sum(tokens for ts, tokens in state.hourly_token_log if ts >= cutoff)


def _is_hourly_budget_exhausted() -> bool:
    """Check if the rolling hourly token budget has been exceeded."""
    if config.max_tokens_per_hour <= 0:
        return False
    return _tokens_last_hour() >= config.max_tokens_per_hour


async def _escalate_budget_exhausted(
    alert: PagerDutyAlert, trace_id: str, budget_type: str
) -> None:
    """Escalate an alert directly when a token budget is exhausted."""
    tokens_used = _tokens_last_hour()
    budget = config.max_tokens_per_hour

    message = (
        f"[SRE Agent — {budget_type.title()} Token Budget Exhausted]\n\n"
        f"The SRE agent's {budget_type} token budget has been exhausted "
        f"({tokens_used:,}/{budget:,} tokens). This alert was NOT diagnosed "
        f"by the agent. A human must investigate.\n\n"
        f"Service: {alert.service_name}\n"
        f"Severity: {alert.severity.value}\n"
        f"Description: {alert.description}\n"
        f"Incident ID: {alert.incident_id}"
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {
            "Authorization": f"Token token={config.pagerduty_api_token}",
            "Content-Type": "application/json",
        }
        if trace_id:
            headers["X-Trace-Id"] = trace_id

        await client.post(
            f"https://api.pagerduty.com/incidents/{alert.incident_id}/notes",
            headers=headers,
            json={"note": {"content": message}},
        )

        await client.put(
            f"https://api.pagerduty.com/incidents/{alert.incident_id}",
            headers=headers,
            json={
                "incident": {
                    "type": "incident_reference",
                    "escalation_level": 2,
                }
            },
        )

    logger.warning(
        "Budget-exhausted escalation: incident_id=%s budget_type=%s "
        "tokens_used=%d budget=%d trace_id=%s",
        alert.incident_id,
        budget_type,
        tokens_used,
        budget,
        trace_id,
    )


# --- Alert Queue API ---


@app.get("/alerts/pending")
async def alerts_pending() -> list[dict[str, Any]]:
    """List all pending alerts (not yet claimed by the agent loop)."""
    pending = [
        {
            "incident_id": a["incident_id"],
            "service_name": a["service_name"],
            "severity": a["severity"],
            "priority": a["priority"],
            "description": a["description"],
            "timestamp": a["timestamp"],
            "queued_at": a["queued_at"],
        }
        for a in _alert_queue.values()
        if a["status"] == "pending"
    ]
    # Sort by priority (P1 first) then by queued_at (oldest first)
    priority_order = {"P1": 0, "P2": 1, "P3": 2, "P4": 3, "P5": 4}
    pending.sort(key=lambda x: (
        priority_order.get(x.get("priority") or "P5", 5),
        x.get("queued_at", 0),
    ))
    return pending


@app.get("/alerts/{incident_id}")
async def alert_details(incident_id: str) -> dict[str, Any]:
    """Get full details of a specific alert."""
    alert_data = _alert_queue.get(incident_id)
    if not alert_data:
        raise HTTPException(status_code=404, detail=f"Alert not found: {incident_id}")
    return alert_data


@app.post("/alerts/{incident_id}/claim")
async def claim_alert(incident_id: str) -> dict[str, str]:
    """Claim an alert to begin diagnosis.

    Marks the alert as 'processing' so it won't be picked up again.
    """
    alert_data = _alert_queue.get(incident_id)
    if not alert_data:
        raise HTTPException(status_code=404, detail=f"Alert not found: {incident_id}")
    if alert_data["status"] != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Alert is already {alert_data['status']}",
        )
    alert_data["status"] = "processing"
    alert_data["claimed_at"] = time.time()
    logger.info("Alert claimed: incident_id=%s", incident_id)
    return {"status": "claimed", "incident_id": incident_id}


@app.post("/alerts/{incident_id}/complete")
async def complete_alert(incident_id: str) -> dict[str, str]:
    """Mark an alert as completed.

    Removes the alert from the active incidents tracking.
    """
    alert_data = _alert_queue.get(incident_id)
    if not alert_data:
        raise HTTPException(status_code=404, detail=f"Alert not found: {incident_id}")
    alert_data["status"] = "done"
    alert_data["completed_at"] = time.time()
    state.active_incidents.pop(incident_id, None)
    incidents_active_updown.add(-1)
    state.agent_runs_completed += 1
    logger.info("Alert completed: incident_id=%s", incident_id)
    return {"status": "completed", "incident_id": incident_id}


# --- /ops/* Diagnostic Endpoints (read-only) ---


@app.get("/ops/status")
async def ops_status() -> dict[str, Any]:
    """Composite health verdict: healthy, degraded, or unhealthy.

    Combines Golden Signals, error rates, and active incident count into
    a single actionable assessment. This is the first endpoint to check.
    """
    metrics = _compute_metrics()
    error_rate = metrics["errors"]["error_rate_percent"]
    active = len(state.active_incidents)
    queue_depth = intake.queue_depth if intake else 0
    prompt_ok = Path(config.sre_prompt_path).exists()

    if error_rate > 50 or not prompt_ok or state.draining:
        verdict = "unhealthy"
    elif error_rate > 10 or active > 5 or queue_depth > 10:
        verdict = "degraded"
    else:
        verdict = "healthy"

    return {
        "status": verdict,
        "golden_signals": metrics,
        "active_incidents": active,
        "draining": state.draining,
    }


@app.get("/ops/health")
async def ops_health() -> dict[str, Any]:
    """Deep health check with per-dependency status.

    Probes PagerDuty API connectivity and verifies all configuration.
    """
    deps = await _check_dependencies()
    all_ok = all(d["status"] == "ok" for d in deps.values())
    return {
        "status": "healthy" if all_ok else "degraded",
        "dependencies": deps,
    }


@app.get("/ops/metrics")
async def ops_metrics() -> dict[str, Any]:
    """Golden Signals and RED metrics snapshot."""
    return _compute_metrics()


@app.get("/ops/config")
async def ops_config() -> dict[str, Any]:
    """Sanitized running configuration. No secrets exposed."""
    return {
        "llm_model": config.llm_model,
        "llm_api_base_url": config.llm_api_base_url,
        "sre_prompt_path": config.sre_prompt_path,
        "incidents_dir": config.incidents_dir,
        "webhook_signature_verification": bool(config.pagerduty_webhook_secret),
        "pagerduty_escalation_policy_id": config.pagerduty_escalation_policy_id,
        "services": [
            {"name": s.name, "base_url": s.base_url, "critical": s.critical}
            for s in config.services
        ],
        "intake": {
            "max_concurrent_alerts": config.max_concurrent_alerts,
            "alert_queue_ttl_seconds": config.alert_queue_ttl_seconds,
        },
        "token_budget": {
            "max_tokens_per_incident": config.max_tokens_per_incident,
            "max_tokens_per_hour": config.max_tokens_per_hour,
        },
        "alert_queue": {
            "pending": sum(1 for a in _alert_queue.values() if a["status"] == "pending"),
            "processing": sum(1 for a in _alert_queue.values() if a["status"] == "processing"),
            "done": sum(1 for a in _alert_queue.values() if a["status"] == "done"),
        },
    }


@app.get("/ops/dependencies")
async def ops_dependencies() -> dict[str, Any]:
    """Dependency graph with status of each."""
    deps = await _check_dependencies()
    return {"service": "sre-agent", "dependencies": deps}


@app.get("/ops/errors")
async def ops_errors() -> dict[str, Any]:
    """Recent errors with types and counts."""
    errors = list(state.recent_errors)
    counts: dict[str, int] = {}
    for e in errors:
        t = e["type"]
        counts[t] = counts.get(t, 0) + 1
    return {
        "total": len(errors),
        "by_type": counts,
        "recent": errors[-20:],
    }


# --- /ops/* Remediation Endpoints (require auth) ---


@app.post("/ops/loglevel")
async def ops_loglevel(request: Request) -> dict[str, str]:
    """Temporarily adjust log verbosity for debugging without a redeploy."""
    _require_ops_auth(request)
    body = await request.json()
    level = body.get("level", "").upper()
    valid = {"DEBUG", "INFO", "WARNING", "ERROR"}
    if level not in valid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid log level. Valid: {', '.join(sorted(valid))}",
        )
    logging.root.setLevel(getattr(logging, level))
    logger.info("Log level changed to %s", level)
    return {"status": "ok", "level": level}


@app.post("/ops/drain")
async def ops_drain(request: Request) -> dict[str, Any]:
    """Put the service into drain mode.

    Stops accepting new webhooks but finishes in-flight alert processing.
    Does not kill the process.
    """
    _require_ops_auth(request)
    state.draining = True
    logger.info("Service entering drain mode")
    return {
        "status": "draining",
        "active_incidents": len(state.active_incidents),
    }


# --- Internal Helpers ---


def _require_ops_auth(request: Request) -> None:
    """Verify bearer token for remediation endpoints.

    Diagnostic GET endpoints are open. Remediation POST endpoints
    require the OPS_AUTH_TOKEN.
    """
    if not config.ops_auth_token:
        return
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    token = auth.removeprefix("Bearer ")
    if not hmac.compare_digest(token, config.ops_auth_token):
        raise HTTPException(status_code=403, detail="Invalid auth token")


def _compute_metrics() -> dict[str, Any]:
    """Compute Golden Signals and RED metrics from runtime state."""
    uptime = time.time() - state.start_time
    total = state.webhooks_received
    total_errors = state.webhooks_failed + state.agent_runs_failed

    # Latency (from agent run durations)
    durations = sorted(state.run_durations) if state.run_durations else []
    if durations:
        p50 = durations[len(durations) // 2]
        p95 = durations[int(len(durations) * 0.95)]
        p99 = durations[min(int(len(durations) * 0.99), len(durations) - 1)]
    else:
        p50 = p95 = p99 = 0.0

    # Rate
    rate = (total / uptime * 60) if uptime > 0 else 0.0

    # Error rate
    error_rate = (total_errors / total * 100) if total > 0 else 0.0

    return {
        "latency": {
            "p50_seconds": round(p50, 3),
            "p95_seconds": round(p95, 3),
            "p99_seconds": round(p99, 3),
        },
        "traffic": {
            "requests_per_minute": round(rate, 2),
            "total_webhooks": total,
        },
        "errors": {
            "error_rate_percent": round(error_rate, 2),
            "total_errors": total_errors,
            "webhook_failures": state.webhooks_failed,
            "agent_failures": state.agent_runs_failed,
        },
        "saturation": {
            "active_incidents": len(state.active_incidents),
        },
        "red": {
            "rate": round(rate, 2),
            "errors": total_errors,
            "duration_p99_seconds": round(p99, 3),
        },
        "counters": {
            "webhooks_received": state.webhooks_received,
            "webhooks_processed": state.webhooks_processed,
            "webhooks_ignored": state.webhooks_ignored,
            "webhooks_failed": state.webhooks_failed,
            "agent_runs_completed": state.agent_runs_completed,
            "agent_runs_failed": state.agent_runs_failed,
        },
        "token_usage": {
            "total_input_tokens": state.total_input_tokens,
            "total_output_tokens": state.total_output_tokens,
            "total_estimated_cost_usd": round(state.total_estimated_cost_usd, 4),
            "tokens_last_hour": _tokens_last_hour(),
            "hourly_budget": config.max_tokens_per_hour,
            "hourly_budget_exhausted": _is_hourly_budget_exhausted(),
        },
        "intake": {
            "queue_depth": intake.queue_depth if intake else 0,
            "active_runs": intake.active_count if intake else 0,
            "max_concurrent": config.max_concurrent_alerts,
            "alerts_deduplicated": state.alerts_deduplicated,
            "alerts_queued": state.alerts_queued,
            "alerts_expired": state.alerts_expired,
        },
    }


async def _check_llm_reachable() -> bool:
    """Lightweight LLM connectivity check.

    Sends a minimal chat completion request (cheap, fast) to verify the
    LLM endpoint is reachable and the credentials are valid. Works with
    all OpenAI-compatible providers including Vertex AI.
    """
    # Refresh ADC token for Vertex AI (no-op for other providers)
    config.refresh_llm_token()

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{config.llm_api_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {config.llm_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": config.llm_model,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1,
            },
        )
        return resp.status_code == 200


async def _check_dependencies() -> dict[str, Any]:
    """Check connectivity to all dependencies."""
    deps: dict[str, Any] = {}

    # System prompt file
    prompt_path = Path(config.sre_prompt_path)
    deps["system_prompt"] = (
        {"status": "ok", "path": str(prompt_path)}
        if prompt_path.exists()
        else {
            "status": "error",
            "path": str(prompt_path),
            "error": "file not found",
        }
    )

    # LLM API — lightweight connectivity check
    try:
        llm_ok = await _check_llm_reachable()
        deps["llm_api"] = {
            "status": "ok" if llm_ok else "error",
            "model": config.llm_model,
            "base_url": config.llm_api_base_url,
            "provider": "vertex_ai" if config.vertex_ai else "api_key",
        }
    except Exception as e:
        deps["llm_api"] = {"status": "error", "error": str(e)}

    # PagerDuty API — lightweight connectivity check
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(
                "https://api.pagerduty.com/abilities",
                headers={
                    "Authorization": f"Token token={config.pagerduty_api_token}"
                },
            )
            deps["pagerduty_api"] = {
                "status": "ok" if resp.status_code == 200 else "error",
                "status_code": resp.status_code,
            }
        except Exception as e:
            deps["pagerduty_api"] = {"status": "error", "error": str(e)}

    # Monitored services — listed with config, not probed from health check
    for svc in config.services:
        deps[f"service:{svc.name}"] = {
            "status": "configured",
            "base_url": svc.base_url,
            "critical": svc.critical,
        }

    return deps


def _verify_signature(body: bytes, signature: str, secret: str) -> bool:
    """Verify PagerDuty V3 webhook HMAC signature."""
    if not signature:
        return False

    # PagerDuty V3 signatures use v1=<hmac-sha256>
    expected = hmac.new(
        secret.encode(), body, hashlib.sha256
    ).hexdigest()

    provided = signature.removeprefix("v1=")
    return hmac.compare_digest(expected, provided)
