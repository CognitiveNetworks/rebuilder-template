"""Tests for OpenTelemetry initialization and instrumentation."""

import os
from unittest.mock import patch

from opentelemetry import trace


class TestTelemetryInit:
    """Tests for telemetry module initialization."""

    def test_is_enabled_false_without_endpoint(self):
        with patch.dict(os.environ, {}, clear=True):
            from telemetry import is_enabled

            assert is_enabled() is False

    def test_is_enabled_true_with_endpoint(self):
        with patch.dict(os.environ, {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4318"}):
            from telemetry import is_enabled

            assert is_enabled() is True

    def test_get_tracer_returns_tracer(self):
        from telemetry import get_tracer

        tracer = get_tracer()
        # Should return a valid tracer (no-op when not configured)
        assert tracer is not None
        assert isinstance(tracer, trace.Tracer)

    def test_no_op_span_works_without_endpoint(self):
        """Verify that spans work as no-ops when OTEL is not configured."""
        from telemetry import get_tracer

        tracer = get_tracer()
        with tracer.start_as_current_span("test.span") as span:
            # No-op span should not raise
            assert span is not None


class TestMetricInstruments:
    """Tests for OTEL metric instrument creation."""

    def test_counter_instruments_exist(self):
        from telemetry import (
            agent_runs_completed_counter,
            agent_runs_failed_counter,
            webhooks_failed_counter,
            webhooks_ignored_counter,
            webhooks_processed_counter,
            webhooks_received_counter,
        )

        # All counters should be created (no-op when not configured)
        assert webhooks_received_counter is not None
        assert webhooks_processed_counter is not None
        assert webhooks_ignored_counter is not None
        assert webhooks_failed_counter is not None
        assert agent_runs_completed_counter is not None
        assert agent_runs_failed_counter is not None

    def test_histogram_instrument_exists(self):
        from telemetry import agent_run_duration_histogram

        assert agent_run_duration_histogram is not None

    def test_updown_counter_instrument_exists(self):
        from telemetry import incidents_active_updown

        assert incidents_active_updown is not None

    def test_counter_add_does_not_raise(self):
        """Verify counter operations work in no-op mode."""
        from telemetry import webhooks_received_counter

        # Should not raise even without OTEL configured
        webhooks_received_counter.add(1)

    def test_histogram_record_does_not_raise(self):
        """Verify histogram operations work in no-op mode."""
        from telemetry import agent_run_duration_histogram

        agent_run_duration_histogram.record(1.5)

    def test_updown_counter_operations_do_not_raise(self):
        """Verify up-down counter operations work in no-op mode."""
        from telemetry import incidents_active_updown

        incidents_active_updown.add(1)
        incidents_active_updown.add(-1)


class TestTelemetryShutdown:
    """Tests for clean shutdown."""

    def test_shutdown_without_init_does_not_raise(self):
        from telemetry import shutdown_telemetry

        # Should not raise even if never initialized
        shutdown_telemetry()
