"""OpenTelemetry initialization for the SRE agent runtime.

Configures metrics, traces, and log export via OTLP. If
OTEL_EXPORTER_OTLP_ENDPOINT is not set, everything runs as a no-op —
the service works identically without an OTLP collector.

Configuration uses standard OTEL environment variables:
  OTEL_SERVICE_NAME           — defaults to "sre-agent"
  OTEL_EXPORTER_OTLP_ENDPOINT — OTLP collector URL (e.g., http://localhost:4318)
  OTEL_EXPORTER_OTLP_PROTOCOL — defaults to "http/protobuf"
  OTEL_RESOURCE_ATTRIBUTES    — additional resource attributes
"""

import logging
import os

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)

# Module-level state
_initialized = False
_tracer_provider: TracerProvider | None = None
_meter_provider: MeterProvider | None = None

# --- Metric Instruments ---
# These are initialized as no-op by default. After init_telemetry() they
# become real instruments if an OTLP endpoint is configured.

_meter = metrics.get_meter("sre_agent")

webhooks_received_counter = _meter.create_counter(
    name="sre_agent.webhooks.received",
    description="Total webhooks received",
    unit="1",
)
webhooks_processed_counter = _meter.create_counter(
    name="sre_agent.webhooks.processed",
    description="Total webhooks processed (accepted for agent triage)",
    unit="1",
)
webhooks_ignored_counter = _meter.create_counter(
    name="sre_agent.webhooks.ignored",
    description="Total webhooks ignored (non-incident events)",
    unit="1",
)
webhooks_failed_counter = _meter.create_counter(
    name="sre_agent.webhooks.failed",
    description="Total webhooks that failed (auth, parse, or processing errors)",
    unit="1",
)
agent_runs_completed_counter = _meter.create_counter(
    name="sre_agent.agent.runs.completed",
    description="Total agent runs completed successfully",
    unit="1",
)
agent_runs_failed_counter = _meter.create_counter(
    name="sre_agent.agent.runs.failed",
    description="Total agent runs that failed",
    unit="1",
)
agent_run_duration_histogram = _meter.create_histogram(
    name="sre_agent.agent.run.duration",
    description="Agent run duration",
    unit="s",
)
incidents_active_updown = _meter.create_up_down_counter(
    name="sre_agent.incidents.active",
    description="Currently active incidents being processed",
    unit="1",
)

# --- Token Usage Metrics ---

tokens_input_counter = _meter.create_counter(
    name="sre_agent.tokens.input",
    description="Total input tokens sent to LLM API",
    unit="1",
)
tokens_output_counter = _meter.create_counter(
    name="sre_agent.tokens.output",
    description="Total output tokens received from LLM API",
    unit="1",
)
tokens_per_run_histogram = _meter.create_histogram(
    name="sre_agent.tokens.per_run",
    description="Total tokens consumed per agent run",
    unit="1",
)

# --- Intake Pipeline Metrics ---

alerts_deduplicated_counter = _meter.create_counter(
    name="sre_agent.intake.deduplicated",
    description="Alerts skipped due to incident-level deduplication",
    unit="1",
)
alerts_queued_counter = _meter.create_counter(
    name="sre_agent.intake.queued",
    description="Alerts queued (service busy or concurrency limit reached)",
    unit="1",
)
alerts_expired_counter = _meter.create_counter(
    name="sre_agent.intake.expired",
    description="Queued alerts expired past TTL without processing",
    unit="1",
)
intake_queue_depth_updown = _meter.create_up_down_counter(
    name="sre_agent.intake.queue_depth",
    description="Current number of alerts waiting in the intake queue",
    unit="1",
)


def is_enabled() -> bool:
    """Check if OTEL export is configured."""
    return bool(os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", ""))


def init_telemetry(app=None) -> None:
    """Initialize OpenTelemetry providers and auto-instrumentation.

    Call this once during application startup. If OTEL_EXPORTER_OTLP_ENDPOINT
    is not set, this function is a no-op — all OTEL API calls (metrics, traces)
    will use the default no-op implementations.

    Args:
        app: Optional FastAPI app instance for auto-instrumentation.
    """
    global _initialized, _tracer_provider, _meter_provider  # noqa: PLW0603

    if _initialized:
        return

    _initialized = True

    if not is_enabled():
        logger.info("OTEL_EXPORTER_OTLP_ENDPOINT not set — telemetry export disabled")
        return

    endpoint = os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"]
    service_name = os.environ.get("OTEL_SERVICE_NAME", "sre-agent")

    logger.info("Initializing OpenTelemetry: endpoint=%s service=%s", endpoint, service_name)

    resource = Resource.create({"service.name": service_name})

    # --- Traces ---
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    span_exporter = OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces")
    _tracer_provider = TracerProvider(resource=resource)
    _tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(_tracer_provider)

    # --- Metrics ---
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

    metric_exporter = OTLPMetricExporter(endpoint=f"{endpoint}/v1/metrics")
    metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=60000)
    _meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(_meter_provider)

    # --- Auto-instrumentation ---
    if app is not None:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)

    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

    HTTPXClientInstrumentor().instrument()

    logger.info("OpenTelemetry initialized — metrics, traces, and auto-instrumentation active")


def shutdown_telemetry() -> None:
    """Flush and shut down OTEL providers. Call during application shutdown."""
    global _initialized  # noqa: PLW0603

    if not _initialized:
        return

    if _tracer_provider is not None:
        _tracer_provider.shutdown()
    if _meter_provider is not None:
        _meter_provider.shutdown()

    _initialized = False
    logger.info("OpenTelemetry shut down")


def get_tracer(name: str = "sre_agent") -> trace.Tracer:
    """Get an OTEL tracer. Returns no-op tracer if OTEL is not configured."""
    return trace.get_tracer(name)
