"""Tests for PagerDuty webhook models and parsing."""

from models import AlertSeverity, PagerDutyAlert, Priority, ServiceEndpoint


class TestPagerDutyAlert:
    """Tests for PagerDutyAlert.from_webhook parsing."""

    def _make_payload(self, **overrides) -> dict:
        """Build a minimal valid PagerDuty V3 webhook payload."""
        data = {
            "id": "P123ABC",
            "title": "High error rate on api service",
            "urgency": "high",
            "created_at": "2025-01-15T10:30:00Z",
            "service": {"summary": "api"},
            "priority": {"summary": "P2"},
            "incident_key": "api/high-error-rate",
            "body": {"details": {}},
        }
        data.update(overrides)
        return {"event": {"event_type": "incident.triggered", "data": data}}

    def test_parses_valid_webhook(self):
        payload = self._make_payload()
        alert = PagerDutyAlert.from_webhook(payload)

        assert alert.incident_id == "P123ABC"
        assert alert.service_name == "api"
        assert alert.severity == AlertSeverity.HIGH
        assert alert.priority == Priority.P2
        assert alert.description == "High error rate on api service"
        assert alert.dedup_key == "api/high-error-rate"

    def test_parses_critical_urgency(self):
        payload = self._make_payload(urgency="critical")
        alert = PagerDutyAlert.from_webhook(payload)
        assert alert.severity == AlertSeverity.CRITICAL

    def test_parses_warning_urgency(self):
        payload = self._make_payload(urgency="warning")
        alert = PagerDutyAlert.from_webhook(payload)
        assert alert.severity == AlertSeverity.WARNING

    def test_defaults_severity_to_high_for_unknown(self):
        payload = self._make_payload(urgency="unknown-value")
        alert = PagerDutyAlert.from_webhook(payload)
        assert alert.severity == AlertSeverity.HIGH

    def test_handles_missing_priority(self):
        payload = self._make_payload()
        payload["event"]["data"]["priority"] = {}
        alert = PagerDutyAlert.from_webhook(payload)
        assert alert.priority is None

    def test_handles_missing_service_name(self):
        payload = self._make_payload()
        payload["event"]["data"]["service"] = {}
        alert = PagerDutyAlert.from_webhook(payload)
        assert alert.service_name == "unknown"

    def test_handles_missing_incident_key(self):
        payload = self._make_payload()
        del payload["event"]["data"]["incident_key"]
        alert = PagerDutyAlert.from_webhook(payload)
        assert alert.dedup_key is None

    def test_extracts_runbook_url_from_details(self):
        payload = self._make_payload()
        payload["event"]["data"]["body"] = {
            "details": {"runbook_url": "https://wiki.example.com/runbook"}
        }
        alert = PagerDutyAlert.from_webhook(payload)
        assert alert.runbook_url == "https://wiki.example.com/runbook"

    def test_parses_all_priorities(self):
        for p in ["P1", "P2", "P3", "P4"]:
            payload = self._make_payload()
            payload["event"]["data"]["priority"] = {"summary": p}
            alert = PagerDutyAlert.from_webhook(payload)
            assert alert.priority == Priority(p)

    def test_falls_back_to_summary_when_title_missing(self):
        payload = self._make_payload()
        del payload["event"]["data"]["title"]
        payload["event"]["data"]["summary"] = "Fallback summary"
        alert = PagerDutyAlert.from_webhook(payload)
        assert alert.description == "Fallback summary"


class TestServiceEndpoint:
    """Tests for ServiceEndpoint model."""

    def test_creates_with_defaults(self):
        svc = ServiceEndpoint(name="api", base_url="https://api.example.com")
        assert svc.name == "api"
        assert svc.base_url == "https://api.example.com"
        assert svc.critical is True

    def test_creates_non_critical(self):
        svc = ServiceEndpoint(
            name="worker", base_url="https://worker.example.com", critical=False
        )
        assert svc.critical is False
