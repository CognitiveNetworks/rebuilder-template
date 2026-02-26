# SRE Agent Runtime

The runtime service that receives alerts from monitoring platforms (GCP Cloud Monitoring, New Relic, Datadog, etc.) and runs an agentic diagnostic loop via any OpenAI-compatible LLM API (GitHub Models, OpenAI, Azure OpenAI, etc.).

The agent operates exclusively through HTTP APIs. It has no SSH access, no kubectl access, no shell access, and no direct database connections. Every interaction with monitored services goes through their `/ops/*` endpoints, every infrastructure diagnostic goes through cloud provider APIs (read-only), and all escalation goes through the PagerDuty API.

## Architecture

```
Monitoring Platform Alert (webhook)
    │
    ▼
┌──────────────────────────┐
│  FastAPI Webhook Receiver │  POST /webhook/gcp (or provider-specific)
│  (main.py)               │  Verifies auth token
│                          │  Parses alert payload
│                          │  Returns immediately
└───────────┴──────────────┘
            │
            ▼
┌──────────────────────────┐
│  Alert Intake Pipeline   │  Incident-level deduplication
│  (intake.py)             │  Service-level serialization (1 per service)
│                          │  Global concurrency limit (default: 3)
│                          │  Priority queue (P1 first)
│                          │  Stale alert expiry (TTL)
└───────────┴──────────────┘
            │ dispatched
            ▼
┌──────────────────────────┐
│  Agent Loop              │  Reads WINDSURF_SRE.md from disk (SRE_PROMPT_PATH)
│  (agent.py)              │  Sends it as the LLM "system" message
│                          │  Sends alert as first "user" message
│                          │  LLM responds with function calls
│                          │  Service executes tools, feeds results back
│                          │  Loop until resolved or escalated
│                          │  Max 20 turns / 5 min (safety limits)
│                          │
│                          │  ⚠ WINDSURF_SRE.md IS the agent's brain.
│                          │  Everything it knows comes from this file.
└───────────┴──────────────┘
            │ function calls
            ▼
┌──────────────────────────┐
│  Tool Executor           │  All interactions are HTTP API calls:
│  (tools.py)              │
│                          │  call_ops_endpoint  → GET/POST /ops/*
│                          │  query_cloud_logs   → Cloud Logging / CloudWatch
│                          │  query_cloud_metrics→ Cloud Monitoring / CloudWatch
│                          │  scale_service      → POST /ops/scale or cloud API
│                          │  escalate_pagerduty → PagerDuty API (escalation)
│                          │  acknowledge_alert  → PagerDuty API (escalation)
│                          │  write_incident_report → local filesystem
└──────────────────────────┘
```

## Files

| File | Purpose |
|---|---|
| `main.py` | FastAPI app — `/health`, `/webhook/gcp`, `/alerts/*`, and `/ops/*` endpoints |
| `agent.py` | Agentic loop — OpenAI-compatible LLM orchestration with function calling |
| `tools.py` | Tool definitions and executor |
| `config.py` | Configuration loaded and validated from environment variables |
| `models.py` | Pydantic models for alert payloads and internal types |
| `intake.py` | Alert intake pipeline — dedup, service serialization, priority queue, concurrency control |
| `state.py` | Runtime state tracking for Golden Signals and `/ops/*` metrics |
| `telemetry.py` | OpenTelemetry initialization — tracers, meters, metric instruments |
| `Dockerfile` | Container image — Python 3.12, non-root, health check |
| `requirements.txt` | Python dependencies |
| `requirements-dev.txt` | Dev dependencies — pytest, ruff |
| `pyproject.toml` | Linter and test configuration |
| `.env.example` | Environment variable template for local development |
| `tests/` | Unit and API tests |
| `terraform/` | Cloud Run deployment with secrets from Secret Manager |

## Prerequisites

- **LLM API key** — GitHub PAT (for GitHub Models), OpenAI key, or any OpenAI-compatible provider key, stored in your cloud provider's secrets manager
- **PagerDuty API token** — for creating incidents on escalation
- **PagerDuty routing key** — Events API v2 integration key for creating PagerDuty incidents on escalation
- **Service registry** — the services this agent monitors, with their `/ops/*` base URLs
- **OPS auth token** — bearer token the agent uses to authenticate against `/ops/*` endpoints
- **Monitoring webhook** — configure your monitoring platform to send alert webhooks to this service's `/webhook/gcp` endpoint

## Local Development

```bash
# Install dependencies (includes test and lint tools)
pip install -r requirements-dev.txt

# Copy and fill in environment variables
cp .env.example .env
# Edit .env with your values

# Set required environment variables (or source .env)
export LLM_API_KEY="ghp_your-github-pat"  # or OpenAI key
export PAGERDUTY_API_TOKEN="your-pd-token"
export OPS_AUTH_TOKEN="your-ops-token"
export SRE_PROMPT_PATH="../WINDSURF_SRE.md"
export INCIDENTS_DIR="./incidents"
export SERVICE_REGISTRY="api|http://localhost:8000|true,worker|http://localhost:8001|false"

# Run the service
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

## Testing

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linter
ruff check .

# Run formatter check
ruff format --check .
```

## OpenAPI Spec

FastAPI auto-generates the OpenAPI spec from the endpoint definitions. When the service is running:

- **Swagger UI:** `http://localhost:8080/docs`
- **ReDoc:** `http://localhost:8080/redoc`
- **Raw spec:** `http://localhost:8080/openapi.json`

The spec is generated from Pydantic models and endpoint type annotations — it stays in sync with the code automatically.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `LLM_API_KEY` | Yes | LLM API key — GitHub PAT, OpenAI key, or any OpenAI-compatible provider |
| `LLM_MODEL` | No | Model ID (default: `gpt-4o`). Any model on your provider. |
| `LLM_API_BASE_URL` | No | API base URL (default: `https://models.inference.ai.azure.com` — GitHub Models) |
| `PAGERDUTY_API_TOKEN` | Yes | PagerDuty API token (from secrets manager) |
| `OPS_AUTH_TOKEN` | Yes | Bearer token for `/ops/*` endpoint auth (from secrets manager) |
| `SERVICE_REGISTRY` | Yes | Comma-separated: `name\|url\|critical` |
| `SRE_PROMPT_PATH` | No | Path to WINDSURF_SRE.md (default: `/app/WINDSURF_SRE.md`) |
| `INCIDENTS_DIR` | No | Incident report output dir (default: `/app/incidents`) |
| `PAGERDUTY_ROUTING_KEY` | Yes | PagerDuty Events API v2 integration key — the agent uses this to create PagerDuty incidents on escalation. |
| `PAGERDUTY_ESCALATION_POLICY_ID` | No | PagerDuty escalation policy for human handoff |
| `SCALING_LIMITS` | No | Comma-separated scaling bounds: `name\|min\|max\|mode` (e.g., `api\|2\|10\|application`) |
| `MAX_CONCURRENT_ALERTS` | No | Max concurrent agent runs (default: `3`). Excess alerts queue with priority ordering. |
| `ALERT_QUEUE_TTL_SECONDS` | No | Queued alert expiry in seconds (default: `600`). Stale alerts are discarded. |
| `MAX_TOKENS_PER_INCIDENT` | No | Per-incident token ceiling (default: `100000`). Agent escalates when exceeded. `0` = unlimited. |
| `MAX_TOKENS_PER_HOUR` | No | Rolling hourly token ceiling (default: `0` = unlimited). Agent switches to escalate-only when exceeded. |

## Docker

```bash
# Build (run from sre-agent/ directory, not runtime/)
# On Apple Silicon, --platform linux/amd64 is required for Cloud Run
docker build --platform linux/amd64 -f runtime/Dockerfile -t sre-agent .

# Run
docker run -p 8080:8080 \
  -e LLM_API_KEY="..." \
  -e PAGERDUTY_API_TOKEN="..." \
  -e OPS_AUTH_TOKEN="..." \
  -e SERVICE_REGISTRY="api|https://api.example.com|true" \
  sre-agent
```

### File Permissions

The Dockerfile creates `/app/incidents` and sets ownership to `appuser` before switching to the non-root user. If you add additional writable directories, ensure they are owned by `appuser`:

```dockerfile
RUN mkdir -p /app/your-dir && chown appuser:appuser /app/your-dir
USER appuser
```

Directories created as root before the `USER appuser` statement are not writable by the application process.

## Deploying to Cloud Run

### Automated (recommended)

The `deploy.sh` script handles the entire deployment — secrets, container build, Terraform, and alert routing setup — in a single command. You only need three credentials:

```bash
# Prerequisites: gcloud auth application-default login
export LLM_API_KEY="ghp_your-github-pat"
export PAGERDUTY_API_TOKEN="your-pd-token"

./deploy.sh ../../rebuild-inputs/orderflow \
  --gcp-project my-gcp-project \
  --service-url https://orderflow-abc123.run.app
```

The script:
1. Extracts the service name from `scope.md` (Target Repository field)
2. Stores secrets in GCP Secret Manager (auto-generates `ops-auth-token`)
3. Builds and pushes the container image to Artifact Registry
4. Deploys Cloud Run via Terraform
5. Stores the PagerDuty routing key in GCP Secret Manager for escalation
6. Verifies the deployment

Use `./deploy.sh --help` for all options, or `./deploy.sh --dry-run` to preview without executing.

### Manual

The `terraform/` directory contains a ready-to-use Cloud Run deployment for manual setup.

```bash
cd terraform

# Create a terraform.tfvars file
cat > terraform.tfvars <<EOF
project_id                 = "your-gcp-project"
region                     = "us-central1"
image                      = "gcr.io/your-project/sre-agent:latest"
llm_api_key_secret         = "llm-api-key"
pagerduty_api_token_secret = "pagerduty-api-token"
ops_auth_token_secret      = "ops-auth-token"
service_registry           = "api|https://api.example.com|true,worker|https://worker.example.com|false"
EOF

terraform init
terraform plan
terraform apply
```

The output includes the `webhook_url` to configure in your monitoring platform's alert notification channel.

## Alert Flow: GCP → SRE Agent → PagerDuty (on escalation only)

The recommended alert flow sends GCP Cloud Monitoring alerts **directly to the SRE agent**. The agent diagnoses and attempts remediation first. Humans are only paged via PagerDuty if the agent cannot resolve the issue.

```
GCP Uptime Check fails
    → GCP Alert Policy fires
    → GCP webhook notification channel → POST /webhook/gcp on SRE agent
        → SRE agent diagnoses (calls /ops/* on the affected service)
        → If resolved → writes incident report (no page)
        → If can't resolve → creates PagerDuty incident (human gets paged)
        → Incident report is ALWAYS written (to disk + logged to stdout)
```

### Setup

1. Deploy the SRE agent to Cloud Run
2. Create a GCP webhook notification channel pointing to `<sre-agent-url>/webhook/gcp?auth_token=<ops-auth-token>`
3. Create a GCP alert policy that fires on uptime check failure, using the webhook notification channel
4. Set `PAGERDUTY_ROUTING_KEY` on the SRE agent (Events API v2 integration key from PagerDuty) — this is how the agent creates PagerDuty incidents on escalation

### Viewing Incident Reports in Logs

Every incident report is logged to stdout with the marker `INCIDENT_REPORT`. On Cloud Run, these go to GCP Cloud Logging automatically.

```bash
# Tail SRE agent logs in real time
gcloud run services logs tail sre-agent-dev \
  --region=us-central1 --project=<your-project>

# Search for incident reports in Cloud Logging
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="sre-agent-dev" AND textPayload:"INCIDENT_REPORT"' \
  --project=<your-project> --limit=10 --format="value(textPayload)"

# Or in the GCP Console:
# Logging → Logs Explorer → filter: resource.type="cloud_run_revision" AND "INCIDENT_REPORT"
```

## PagerDuty Configuration (Escalation Only)

PagerDuty is the **escalation target** — the agent creates PagerDuty incidents when it cannot resolve an issue autonomously. PagerDuty is **not** an alert source.

### Setup

1. Create a PagerDuty service and escalation policy for the monitored application.
2. Create an Events API v2 integration on the PagerDuty service and note the **integration key** (routing key).
3. Set `PAGERDUTY_ROUTING_KEY` on the SRE agent with this integration key.
4. Set `PAGERDUTY_API_TOKEN` with a PagerDuty API token that has permissions to manage incidents.
5. Optionally set `PAGERDUTY_ESCALATION_POLICY_ID` to control which escalation policy receives incidents.

## Operational Endpoints

The runtime exposes `/ops/*` endpoints for its own observability, following the same contract that all services in the platform implement.

### Diagnostic (GET, no elevated auth)

| Endpoint | Description |
|---|---|
| `/ops/status` | Composite health verdict (healthy/degraded/unhealthy) with Golden Signals breakdown |
| `/ops/health` | Deep dependency check — probes PagerDuty API, verifies system prompt |
| `/ops/metrics` | Golden Signals and RED metrics snapshot — latency percentiles, request rate, error rate, saturation |
| `/ops/config` | Sanitized running configuration — no secrets exposed |
| `/ops/dependencies` | Dependency graph with per-dependency status |
| `/ops/errors` | Recent errors with types, counts, and details |

### Remediation (POST, requires `OPS_AUTH_TOKEN`)

| Endpoint | Description |
|---|---|
| `/ops/loglevel` | Adjust log verbosity without a redeploy. Body: `{"level": "DEBUG"}` |
| `/ops/drain` | Enter drain mode — stop accepting new webhooks, finish in-flight work |

### Design Decisions

- **API-only access** — the agent has no SSH, kubectl, shell, or direct database access. All diagnostics go through service `/ops/*` endpoints and cloud provider APIs. All remediation goes through service `/ops/*` POST endpoints. All escalation goes through the PagerDuty API. If an action cannot be performed through an API, the agent escalates.
- **Structured JSON logging** — all log output is JSON for log aggregation systems.
- **Trace IDs** — every webhook gets a UUID trace ID propagated through the agent loop and tool calls via `X-Trace-Id` header. Correlate logs across the agent and monitored services.
- **Config validation** — all required environment variables are validated at startup with clear error messages. Invalid `SERVICE_REGISTRY` entries and malformed URLs are rejected.
- **Graceful shutdown** — on SIGTERM, the service waits up to 30 seconds for active incidents to finish before shutting down.
- **Path traversal prevention** — incident report filenames are validated to prevent writing outside the incidents directory.
- **Agent timeout** — 5-minute absolute timeout per alert (in addition to the 20-turn safety limit).

## Telemetry (OpenTelemetry)

The runtime optionally exports metrics, traces, and logs via OpenTelemetry (OTEL) to any OTLP-compatible APM platform (Grafana, Datadog, New Relic, etc.). OTEL runs as a **no-op** when `OTEL_EXPORTER_OTLP_ENDPOINT` is not set — the service works identically without it.

### Configuration

OTEL uses standard environment variables — no custom configuration:

| Variable | Description |
|---|---|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint (e.g., `http://localhost:4318`). Set this to enable OTEL. |
| `OTEL_SERVICE_NAME` | Service name in traces/metrics (default: `sre-agent`) |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | Export protocol (default: `http/protobuf`) |
| `OTEL_RESOURCE_ATTRIBUTES` | Additional resource attributes (e.g., `deployment.environment=prod`) |

### What Gets Exported

**Metrics** — Golden Signals and RED metrics as OTEL instruments, updated alongside the existing `state.py` counters:

| Instrument | Type | Description |
|---|---|---|
| `sre_agent.webhooks.received` | Counter | Total webhooks received |
| `sre_agent.webhooks.processed` | Counter | Webhooks that triggered the agent loop |
| `sre_agent.webhooks.ignored` | Counter | Webhooks filtered out (non-trigger events) |
| `sre_agent.webhooks.failed` | Counter | Webhooks that failed processing |
| `sre_agent.agent.runs.completed` | Counter | Successful agent runs |
| `sre_agent.agent.runs.failed` | Counter | Failed agent runs |
| `sre_agent.agent.run.duration` | Histogram | Agent run duration in seconds |
| `sre_agent.incidents.active` | UpDownCounter | Currently active incidents |
| `sre_agent.intake.deduplicated` | Counter | Alerts skipped (same incident already processing) |
| `sre_agent.intake.queued` | Counter | Alerts queued (service busy or concurrency limit) |
| `sre_agent.intake.expired` | Counter | Queued alerts expired past TTL |
| `sre_agent.intake.queue_depth` | UpDownCounter | Current intake queue depth |

**Traces** — distributed traces for every webhook:

- Root span per inbound webhook request (via FastAPI auto-instrumentation)
- `sre_agent.process_alert` — alert processing span with incident ID and service attributes
- `sre_agent.agent.turn` — per-turn span in the agent loop
- `sre_agent.tool.execute` — tool execution span with tool name
- `sre_agent.tool.call_ops_endpoint` — outbound `/ops/*` call span
- `sre_agent.tool.scale_service` — scaling operation span
- Outbound HTTP spans via httpx auto-instrumentation

**Logs** — structured JSON logs bridged to OTEL with trace/span ID correlation.

### Relationship to `/ops/*` Endpoints

Both OTEL and `/ops/*` endpoints report the same signals. They serve different purposes:

- `/ops/*` = **pull-based**. The SRE agent and humans query these on-demand.
- OTEL = **push-based**. Metrics, traces, and logs flow continuously to APM platforms.

`state.py` remains the local source of truth for `/ops/*` responses. OTEL instruments are updated at the same instrumentation points.

### Testing Locally with an OTEL Collector

```bash
# Run an OTEL collector (receives and logs telemetry)
docker run -p 4318:4318 otel/opentelemetry-collector

# Start the service with OTEL enabled
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
uvicorn main:app --host 0.0.0.0 --port 8080
```

## Token Budget Controls

The agent tracks LLM token usage per incident and globally. Two configurable budgets prevent runaway costs:

| Variable | Default | Description |
|---|---|---|
| `MAX_TOKENS_PER_INCIDENT` | `100000` | Per-incident token ceiling. When exceeded mid-diagnosis, the agent stops, escalates to a human via PagerDuty with a summary of what it found so far, and writes an incident report noting the budget was exceeded. Set to `0` for unlimited. |
| `MAX_TOKENS_PER_HOUR` | `0` (unlimited) | Rolling hourly token ceiling. When exceeded, the agent switches to **escalate-only mode** — incoming alerts are immediately escalated to humans without running the diagnostic loop. The budget resets as older token usage ages out of the 1-hour rolling window. |

**What gets tracked:**
- Per-turn input and output tokens from `response.usage` on every LLM API call
- Per-incident totals (included in incident reports under `## Token Usage`)
- Global totals and rolling hourly usage (exposed via `/ops/metrics` under `token_usage`)
- OTEL metrics: `sre_agent.tokens.input`, `sre_agent.tokens.output`, `sre_agent.tokens.per_run`

**What happens when a budget is hit:**

| Budget | Behavior |
|---|---|
| Per-incident exceeded | Agent escalates the current incident to PagerDuty with a note explaining the token budget was exceeded. Incident report is written with `Budget Exceeded: yes`. |
| Hourly exceeded | All new alerts are immediately escalated without diagnosis. PagerDuty note explains the hourly budget is exhausted. Existing in-flight agent runs are not interrupted. |

Check token usage at any time via `/ops/metrics`:

```bash
curl http://localhost:8080/ops/metrics | jq '.token_usage'
```

## Customization

### Cloud Log/Metric Queries

The `query_cloud_logs` and `query_cloud_metrics` tools in `tools.py` are stubs. Implement them for your cloud provider:

- **GCP:** Add `google-cloud-logging` and `google-cloud-monitoring` to `requirements.txt`
- **AWS:** Add `boto3` to `requirements.txt` and use CloudWatch Logs and CloudWatch Metrics APIs

### Deployment by Cloud Provider

The included `terraform/` directory contains a Cloud Run deployment. Adapt it for your target cloud provider:

- **GCP (Cloud Run):** Use the included Terraform as-is. Secrets come from GCP Secret Manager.
- **AWS (ECS/Fargate):** Replace `terraform/main.tf` with ECS task definition, service, and ALB resources. Use AWS Secrets Manager for secrets. The container image, environment variables, and secrets pattern are the same.

### Additional Tools

During incident response, the agent enters an agentic loop where it decides which tools to call based on what it finds. Each tool is a tool-use definition in `tools.py` paired with a handler that does the actual work. The built-in tools are:

- `call_ops_endpoint` — call `/ops/*` diagnostic and remediation endpoints on monitored services
- `query_cloud_logs` — search cloud provider logs (stub — implement for your provider)
- `query_cloud_metrics` — query infrastructure metrics (stub — implement for your provider)
- `escalate_pagerduty` — escalate an incident to a human responder
- `acknowledge_alert` — acknowledge or resolve a PagerDuty incident
- `write_incident_report` — write a markdown incident report
- `scale_service` — scale a service within configured min/max bounds

To add new tools:

1. Add the tool definition to `TOOL_DEFINITIONS` in `tools.py`
2. Add a handler method to `ToolExecutor`
3. Register the handler in the `handlers` dict in `ToolExecutor.execute()`

> [!NOTE]
> **Example — adding a `restart_pod` tool:**
>
> Tools are not called via `/ops/*` endpoints. During incident response, the agent enters an agentic loop and decides which tools to invoke based on the diagnostic workflow. When the agent wants to restart a pod, it returns a `tool_use` block like this:
>
> ```json
> {
>     "type": "tool_use",
>     "name": "restart_pod",
>     "input": {
>         "namespace": "production",
>         "pod_name": "orderflow-api-7b4d6f8c9-x2k5m"
>     }
> }
> ```
>
> To add a new tool, you add it in two places:
>
> ```python
> # 1. Add to TOOL_DEFINITIONS — tells the LLM the tool exists and how to call it
> {
>     "name": "restart_pod",
>     "description": "Restart a specific pod in a Kubernetes deployment.",
>     "input_schema": {
>         "type": "object",
>         "properties": {
>             "namespace": {"type": "string", "description": "Kubernetes namespace."},
>             "pod_name": {"type": "string", "description": "Name of the pod to restart."},
>         },
>         "required": ["namespace", "pod_name"],
>     },
> }
>
> # 2. Add a handler method to ToolExecutor — does the actual work
> async def _restart_pod(self, input: dict[str, Any]) -> str:
>     namespace = input.get("namespace", "")
>     pod_name = input.get("pod_name", "")
>     # ... call Kubernetes API ...
>     return json.dumps({"status": "restarted", "pod": pod_name})
>
> # 3. Register in the handlers dict in ToolExecutor.execute()
> handlers = {
>     ...
>     "restart_pod": self._restart_pod,
> }
> ```
