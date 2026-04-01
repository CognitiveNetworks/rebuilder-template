# SRE Agent Configuration

**Instructions:** Fill out this file when setting up the SRE agent for a specific project. This provides the agent with the service registry, thresholds, and escalation contacts it needs to operate.

## Service Registry

> List every service the agent monitors. The agent uses these base URLs to call `/ops/*` endpoints.
>
> **Populating URLs:** Service names are pre-filled during the rebuild process (Step 7). Base URLs are populated after infrastructure is provisioned — typically after `terraform apply` outputs the Cloud Run or load balancer URL. Before wiring alerting, verify each URL responds:
> ```bash
> curl <base-url>/ops/status | jq   # Should return {"status": "healthy", ...}
> curl <base-url>/ops/health | jq   # Should show all dependencies healthy
> ```

| Service Name | Base URL | Environment | Critical? | Notes |
|---|---|---|---|---|
| tvevents-api | <!-- TODO: fill after infra provisioning --> | dev | yes | TV event ingestion API (FastAPI) |
| tvevents-api | <!-- TODO: fill after infra provisioning --> | staging | yes | TV event ingestion API (FastAPI) |
| tvevents-api | <!-- TODO: fill after infra provisioning --> | prod | yes | TV event ingestion API (FastAPI) |

## Tech Stack

> Populated from the chosen rebuild candidate. The agent uses this to make stack-aware decisions.

- **Cloud Provider:** AWS
- **Orchestration:** Kubernetes (AWS EKS)
- **Backend:** Python 3.12 / FastAPI
- **Database:** PostgreSQL (AWS RDS)
- **Cache:** In-memory + file cache (blacklist channel IDs)
- **Database networking:** Private IP (VPC)
- **Additional Services:** Kafka (via kafka_module), OTEL Collector, AWS Global Accelerator

## Alert Source

> The SRE agent receives alerts from your monitoring/alerting platform (GCP Cloud Monitoring, New Relic, Datadog, etc.) — not from PagerDuty. PagerDuty is used only for escalation when the agent cannot resolve an issue.

- **Alerting Platform:** New Relic (via OTEL)
- **Webhook Endpoint:** `<sre-agent-url>/webhook/alerts?auth_token=<ops-auth-token>`
- **Alert Routing:** New Relic Alert Condition → Notification Channel (webhook) → SRE agent → diagnose → escalate to PagerDuty if unresolved

## PagerDuty Escalation

> PagerDuty is the escalation target. The agent creates PagerDuty incidents only when it cannot resolve an issue and needs a human. Populated after PagerDuty setup.

- **API Token:** <!-- TODO: store in AWS Secrets Manager after PagerDuty setup -->
- **Escalation Policy ID:** <!-- TODO: fill after PagerDuty setup -->
- **Service ID:** <!-- TODO: fill after PagerDuty setup -->
- **Routing Key (Events API v2):** <!-- TODO: fill after PagerDuty setup -->

## SLO Thresholds

> Per-service SLO targets. The agent uses these to evaluate `/ops/status` verdicts and determine severity.

| Service | Availability SLO | Latency SLO (p99) | Error Rate SLO | Error Budget (monthly) |
|---|---|---|---|---|
| tvevents-api | 99.9% | 200ms | < 0.1% | 43.2 min/month |

## Escalation Contacts

| Priority | Contact | Channel |
|---|---|---|
| P1 — Critical | <!-- TODO: on-call engineer --> | PagerDuty + #tvevents-alerts Slack |
| P2 — High | <!-- TODO: on-call engineer --> | PagerDuty + #tvevents-alerts Slack |
| P3 — Medium | <!-- TODO: team lead --> | #tvevents-alerts Slack |
| P4 — Low | <!-- TODO: team queue --> | GitHub issue |

## Scaling

> Scaling is managed by cloud-native mechanisms (KEDA, GKE HPA, Cloud Run auto-scaling, ECS auto-scaling) — not by application-level `/ops/scale` endpoints. The SRE agent does not scale services directly. If saturation alerts fire and auto-scaling cannot resolve them, the agent escalates to a human for capacity planning.

## Agent Auth

> The `ops-auth-token` is the bearer token the SRE agent sends in the `Authorization` header when calling `/ops/*` endpoints on monitored services. If using `deploy.sh`, this token is auto-generated and stored in GCP Secret Manager. For manual setup, generate a random token, store it in your secrets manager, and configure both the SRE agent (`OPS_AUTH_TOKEN` env var) and the monitored service to use it.

- **Service Account:** [SRE agent service account with scoped permissions for `/ops/*` endpoints only]
- **Auth Method:** [Bearer token / mTLS / IAM — reference to secrets manager entry]
- **Permissions:** Read-only diagnostics + safe remediation. No write access to application data, infrastructure, or deployments.

## Cloud Platform Access

> The SRE agent requires read-only access to cloud provider APIs for diagnostic correlation. It uses this to understand managed service health alongside the `/ops/*` application endpoints. The agent never modifies cloud infrastructure.

> **Template instruction:** Keep only the section that matches your cloud provider. Delete the other section entirely — leftover cloud-provider sections create noise that can mislead the SRE agent about which cloud it is operating in.

### AWS
- **Required Policies (diagnostics — read-only):**
  - `CloudWatchReadOnlyAccess` — read metrics and alarms
  - `CloudWatchLogsReadOnlyAccess` — query logs
  - `AmazonRDSReadOnlyAccess` — database instance status and metrics
  - `AmazonElastiCacheReadOnlyAccess` — cache cluster status
  - `AmazonEKSReadOnlyAccess` — EKS cluster and node group status (if applicable)
  - `AmazonECS_ReadOnlyAccess` — ECS service and task status (if applicable)
  - `AmazonEC2ReadOnlyAccess` — instance and network status
  - `AmazonSQSReadOnlyAccess` — queue depth and metrics (if applicable)
- **Required Policies (scaling — only if using cloud_native scaling mode):**
  - Custom policy with `ecs:UpdateService` and `ecs:DescribeServices` — update ECS desired count (if using ECS)
  - Custom policy with `eks` pod scaling permissions — update EKS deployment replicas (if using EKS)
  - Note: Scope these policies with resource-level conditions to only the specific services the agent is allowed to scale

## Runtime Configuration

> The SRE agent runs as a containerized service. See `runtime/README.md` for full setup and deployment instructions.

### Required Environment Variables

| Variable | Source | Description |
|---|---|---|
| `LLM_API_KEY` | Secrets manager | LLM API key (GitHub PAT for GitHub Models, OpenAI key, etc.). **Not needed for Vertex AI** — uses ADC. |
| `PAGERDUTY_API_TOKEN` | Secrets manager | PagerDuty API token for creating incidents on escalation |
| `OPS_AUTH_TOKEN` | Secrets manager | Bearer token the agent uses to authenticate against `/ops/*` endpoints |
| `SERVICE_REGISTRY` | Config / env | Comma-separated service list: `name\|url\|critical` (e.g., `api\|https://api.example.com\|true`) |

### Optional Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LLM_MODEL` | `gpt-4o` | LLM model ID. For Vertex AI: `google/gemini-2.0-flash` or `google/gemini-2.5-pro` |
| `LLM_MODEL_ESCALATION` | (empty) | Stronger model for complex incidents. If set, the agent starts with `LLM_MODEL` and switches to this after `LLM_ESCALATION_TURN` turns without resolution. |
| `LLM_ESCALATION_TURN` | `5` | Turn number at which to switch to the escalation model. Only applies when `LLM_MODEL_ESCALATION` is set. |
| `LLM_API_BASE_URL` | `https://models.inference.ai.azure.com` | LLM API base URL. For Vertex AI: `https://REGION-aiplatform.googleapis.com/v1beta1/projects/PROJECT/locations/REGION/endpoints/openapi` |
| `SRE_PROMPT_PATH` | `/app/skill.md` | Path to skill.md inside the container |
| `INCIDENTS_DIR` | `/app/incidents` | Directory where incident reports are written |
| `PAGERDUTY_ROUTING_KEY` | (empty) | PagerDuty Events API v2 integration key (from Secret Manager). Required — agent creates incidents on escalation. |
| `PAGERDUTY_ESCALATION_POLICY_ID` | (empty) | PagerDuty escalation policy ID for human handoff |
| `SCALING_LIMITS` | (empty) | Comma-separated scaling bounds: `name\|min\|max\|mode` (e.g., `api\|2\|10\|application,worker\|1\|5\|cloud_native`). Without this, the agent cannot scale any service and will escalate saturation alerts. |
| `MAX_CONCURRENT_ALERTS` | `3` | Maximum concurrent agent runs. Excess alerts queue with priority ordering (P1 first). |
| `ALERT_QUEUE_TTL_SECONDS` | `600` | Queued alert expiry in seconds. Stale alerts are discarded when their slot opens. |
| `MAX_TOKENS_PER_INCIDENT` | `100000` | Per-incident token ceiling. Agent escalates to human when exceeded. `0` = unlimited. |
| `MAX_TOKENS_PER_HOUR` | `0` (unlimited) | Rolling hourly token ceiling. Agent switches to escalate-only mode when exceeded. |

### Deployment

The runtime includes Terraform templates for GCP Cloud Run in `runtime/terraform/`. For AWS, replace the Terraform with equivalent ECS/Fargate resources — the container image, environment variables, and secrets pattern are the same.

**LLM Provider for GCP projects:** Use `--vertex-ai` when deploying. This configures the agent to use Vertex AI (Gemini) via the OpenAI-compatible endpoint with Application Default Credentials — no API key needed. The Cloud Run service account authenticates automatically. Deploy with:
```bash
./deploy.sh <project-dir> --gcp-project <id> --service-url <url> --gcp-direct --vertex-ai
```

### Alert Routing Setup

1. Deploy the runtime service
2. Create a PagerDuty Events API v2 integration on the target PD service
3. Set `PAGERDUTY_ROUTING_KEY` to the integration key
4. Configure your alerting platform to send webhooks to `<service_url>/webhook/alerts?auth_token=<ops-auth-token>`
5. Alerts flow to the SRE agent; PagerDuty incidents are only created when the agent escalates
