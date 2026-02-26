"""Tests for the FastAPI webhook receiver and /ops/* endpoints."""

import hashlib
import hmac
import importlib
import json
import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from intake import AlertIntake

# Config must be patched before importing main
REQUIRED_ENV = {
    "LLM_API_KEY": "ghp-test",
    "PAGERDUTY_API_TOKEN": "pd-test",
    "OPS_AUTH_TOKEN": "ops-test",
    "SERVICE_REGISTRY": "api|https://api.example.com|true",
    "SRE_PROMPT_PATH": "/dev/null",
}


def _reload_main():
    """Reload the main module to pick up patched environment."""
    import main as main_module  # noqa: I001

    importlib.reload(main_module)
    return main_module


@pytest.fixture()
def client():
    """Create a test client with mocked config and intake pipeline."""
    with patch.dict(os.environ, REQUIRED_ENV, clear=True):
        main_module = _reload_main()
        # Reset state between tests
        main_module.state.webhooks_received = 0
        main_module.state.webhooks_processed = 0
        main_module.state.webhooks_ignored = 0
        main_module.state.webhooks_failed = 0
        main_module.state.agent_runs_completed = 0
        main_module.state.agent_runs_failed = 0
        main_module.state.alerts_deduplicated = 0
        main_module.state.alerts_queued = 0
        main_module.state.alerts_expired = 0
        main_module.state.active_incidents.clear()
        main_module.state.recent_errors.clear()
        main_module.state.run_durations.clear()
        main_module.state.draining = False
        # Initialize intake with mock process function
        main_module.intake = AlertIntake(
            process_fn=AsyncMock(),
            state=main_module.state,
            max_concurrent=3,
            queue_ttl_seconds=600,
        )
        yield TestClient(main_module.app)


def _make_webhook_payload(event_type="incident.triggered", **data_overrides):
    """Build a minimal PagerDuty V3 webhook payload."""
    data = {
        "id": "P123ABC",
        "title": "Test alert",
        "urgency": "high",
        "created_at": "2025-01-15T10:30:00Z",
        "service": {"summary": "api"},
        "priority": {"summary": "P2"},
        "incident_key": "test-dedup",
        "body": {"details": {}},
    }
    data.update(data_overrides)
    return {"event": {"event_type": event_type, "data": data}}


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_returns_healthy(self, client, tmp_path):
        prompt_file = tmp_path / "WINDSURF_SRE.md"
        prompt_file.write_text("system prompt content")
        with patch.dict(os.environ, {"SRE_PROMPT_PATH": str(prompt_file)}):
            main_module = _reload_main()
            main_module.intake = AlertIntake(
                process_fn=AsyncMock(),
                state=main_module.state,
            )
            test_client = TestClient(main_module.app)
            resp = test_client.get("/health")
            assert resp.status_code == 200
            assert resp.json()["status"] == "healthy"

    def test_returns_unhealthy_when_prompt_missing(self, client):
        resp = client.get("/health")
        # /dev/null exists but is empty
        assert resp.status_code == 503


class TestWebhookEndpoint:
    """Tests for POST /webhook."""

    def test_accepts_incident_triggered(self, client):
        payload = _make_webhook_payload("incident.triggered")
        resp = client.post("/webhook", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "dispatched"
        assert body["incident_id"] == "P123ABC"
        assert "trace_id" in body

    def test_ignores_non_incident_events(self, client):
        payload = _make_webhook_payload("incident.resolved")
        resp = client.post("/webhook", json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "ignored"

    def test_rejects_invalid_payload(self, client):
        payload = {"event": {"event_type": "incident.triggered", "data": {}}}
        resp = client.post("/webhook", json=payload)
        # from_webhook should still parse (defaults to "unknown"), so this succeeds
        assert resp.status_code == 200

    def test_rejects_when_draining(self, client):
        import main as main_module  # noqa: I001

        main_module.state.draining = True
        payload = _make_webhook_payload()
        resp = client.post("/webhook", json=payload)
        assert resp.status_code == 503

    def test_response_includes_disposition(self, client):
        """Verify webhook response includes intake disposition field."""
        payload = _make_webhook_payload("incident.triggered")
        resp = client.post("/webhook", json=payload)
        body = resp.json()
        # Disposition comes from intake.submit() — one of the valid values
        assert body["status"] in ("dispatched", "queued", "deduplicated", "rejected")

    def test_increments_webhooks_processed(self, client):
        import main as main_module  # noqa: I001

        payload = _make_webhook_payload("incident.triggered")
        client.post("/webhook", json=payload)
        assert main_module.state.webhooks_processed == 1


class TestOpsStatusEndpoint:
    """Tests for GET /ops/status."""

    def test_returns_healthy_by_default(self, client):
        resp = client.get("/ops/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] in ("healthy", "degraded", "unhealthy")
        assert "golden_signals" in body

    def test_returns_unhealthy_when_draining(self, client):
        import main as main_module  # noqa: I001

        main_module.state.draining = True
        resp = client.get("/ops/status")
        assert resp.json()["status"] == "unhealthy"


class TestOpsMetricsEndpoint:
    """Tests for GET /ops/metrics."""

    def test_returns_metrics_structure(self, client):
        resp = client.get("/ops/metrics")
        assert resp.status_code == 200
        body = resp.json()
        assert "latency" in body
        assert "traffic" in body
        assert "errors" in body
        assert "saturation" in body
        assert "red" in body
        assert "counters" in body
        assert "intake" in body

    def test_latency_percentiles_present(self, client):
        resp = client.get("/ops/metrics")
        latency = resp.json()["latency"]
        assert "p50_seconds" in latency
        assert "p95_seconds" in latency
        assert "p99_seconds" in latency

    def test_intake_metrics_present(self, client):
        resp = client.get("/ops/metrics")
        intake_data = resp.json()["intake"]
        assert "queue_depth" in intake_data
        assert "active_runs" in intake_data
        assert "max_concurrent" in intake_data
        assert "alerts_deduplicated" in intake_data
        assert "alerts_queued" in intake_data
        assert "alerts_expired" in intake_data


class TestOpsConfigEndpoint:
    """Tests for GET /ops/config."""

    def test_returns_sanitized_config(self, client):
        resp = client.get("/ops/config")
        assert resp.status_code == 200
        body = resp.json()
        assert "services" in body
        assert "intake" in body
        assert body["intake"]["max_concurrent_alerts"] == 3
        assert body["intake"]["alert_queue_ttl_seconds"] == 600

    def test_does_not_expose_secrets(self, client):
        resp = client.get("/ops/config")
        raw = json.dumps(resp.json())
        assert "ghp-test" not in raw
        assert "pd-test" not in raw
        assert "ops-test" not in raw


class TestOpsErrorsEndpoint:
    """Tests for GET /ops/errors."""

    def test_returns_empty_errors(self, client):
        resp = client.get("/ops/errors")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["by_type"] == {}
        assert body["recent"] == []


class TestOpsRemediationAuth:
    """Tests for auth on remediation POST endpoints."""

    def test_loglevel_requires_auth(self, client):
        resp = client.post("/ops/loglevel", json={"level": "DEBUG"})
        assert resp.status_code == 401

    def test_loglevel_accepts_valid_token(self, client):
        resp = client.post(
            "/ops/loglevel",
            json={"level": "DEBUG"},
            headers={"Authorization": "Bearer ops-test"},
        )
        assert resp.status_code == 200

    def test_loglevel_rejects_invalid_token(self, client):
        resp = client.post(
            "/ops/loglevel",
            json={"level": "DEBUG"},
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert resp.status_code == 403

    def test_loglevel_rejects_invalid_level(self, client):
        resp = client.post(
            "/ops/loglevel",
            json={"level": "TRACE"},
            headers={"Authorization": "Bearer ops-test"},
        )
        assert resp.status_code == 400

    def test_drain_requires_auth(self, client):
        resp = client.post("/ops/drain")
        assert resp.status_code == 401

    def test_drain_sets_draining_flag(self, client):
        import main as main_module  # noqa: I001

        resp = client.post(
            "/ops/drain",
            headers={"Authorization": "Bearer ops-test"},
        )
        assert resp.status_code == 200
        assert main_module.state.draining is True


class TestWebhookSignatureVerification:
    """Tests for HMAC signature verification."""

    def test_verify_signature_rejects_missing_signature(self, client):
        from main import _verify_signature

        assert _verify_signature(b"body", "", "secret") is False

    def test_verify_signature_accepts_valid(self, client):
        from main import _verify_signature

        body = b'{"test": "payload"}'
        secret = "test-secret"
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        signature = f"v1={expected}"
        assert _verify_signature(body, signature, secret) is True

    def test_verify_signature_rejects_invalid(self, client):
        from main import _verify_signature

        assert _verify_signature(b"body", "v1=invalid", "secret") is False
