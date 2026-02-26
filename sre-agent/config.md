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
| *[service-name]* | *[TODO: URL after infra provisioning]* | *[env]* | *[yes/no]* | *[description]* |

## Tech Stack

> Populated from the chosen rebuild candidate. The agent uses this to make stack-aware decisions.

- **Cloud Provider:** *[GCP or AWS]*
- **Orchestration:** *[Cloud Run, GKE, ECS, etc.]*
- **Backend:** *[language / framework]*
- **Database:** *[engine, managed service]*
- **Cache:** *[engine, managed service]*
- **Database networking:** *[private IP only / public IP / cross-cloud]*
- **Additional Services:** *[queues, CDNs, service discovery, etc.]*

## Alert Source

> The SRE agent receives alerts from your monitoring/alerting platform (GCP Cloud Monitoring, New Relic, Datadog, etc.) — not from PagerDuty. PagerDuty is used only for escalation when the agent cannot resolve an issue.

- **Alerting Platform:** *[GCP Cloud Monitoring, New Relic, Datadog, etc.]*
- **Webhook Endpoint:** `<sre-agent-url>/webhook/gcp?auth_token=<ops-auth-token>`
- **Alert Routing:** *[describe how alerts flow: e.g., GCP Uptime Check → Alert Policy → webhook notification channel → SRE agent → diagnose → escalate to PagerDuty if unresolved]*

## PagerDuty Escalation

> PagerDuty is the escalation target. The agent creates PagerDuty incidents only when it cannot resolve an issue and needs a human. Populated after PagerDuty setup.

- **API Token:** *[stored in secrets manager — reference only, not the actual token]*
- **Escalation Policy ID:** *[PagerDuty escalation policy for human handoff]*
- **Service ID:** *[PagerDuty service ID — find in URL: `https://<domain>.pagerduty.com/services/PXXXXXX`]*
- **Routing Key (Events API v2):** *[integration key from PagerDuty service → Integrations → Events API v2 — used by SRE agent to CREATE incidents on escalation]*

## SLO Thresholds

> Per-service SLO targets. The agent uses these to evaluate `/ops/status` verdicts and determine severity.

| Service | Availability SLO | Latency SLO (p99) | Error Rate SLO | Error Budget (monthly) |
|---|---|---|---|---|
| *[service-name]* | *[target]* | *[target]* | *[target]* | *[budget]* |

## Escalation Contacts

| Priority | Contact | Channel |
|---|---|---|
| P1 — Critical | [On-call engineer] | [PagerDuty + Slack channel] |
| P2 — High | [On-call engineer] | [PagerDuty + Slack channel] |
| P3 — Medium | [Team lead] | [Slack channel] |
| P4 — Low | [Team queue] | [GitHub issue] |

## Scaling Limits

> Per-service scaling bounds. The SRE agent can only scale services that appear in this table, and only within the configured min/max range. Services without an entry here cannot be scaled by the agent — saturation alerts for those services will be escalated.

| Service Name | Min Instances | Max Instances | Scaling Mode | Notes |
|---|---|---|---|---|
| *[service-name]* | *[min]* | *[max]* | *[application or cloud_native]* | *[notes]* |

### Scaling Modes

- **application** — the service manages its own scaling. The agent calls `POST /ops/scale` on the service with `{"target_instances": N, "reason": "..."}`. The service is responsible for adjusting its own instance count.
- **cloud_native** — the agent adjusts the replica/instance count directly via cloud provider APIs (GKE HPA, Cloud Run instance count, ECS desired count). Requires write IAM permissions (see Cloud Platform Access below).

### Scaling Safety

- The agent always uses absolute targets, never relative increments.
- The agent never scales below min or above max.
- If the service is already at max and still saturated, the agent escalates for capacity planning.
- Scaling is a remediation action, not a substitute for root cause analysis. If saturation is caused by a leak or runaway process, scaling will not fix it.

## Agent Auth

> The `ops-auth-token` is the bearer token the SRE agent sends in the `Authorization` header when calling `/ops/*` endpoints on monitored services. If using `deploy.sh`, this token is auto-generated and stored in GCP Secret Manager. For manual setup, generate a random token, store it in your secrets manager, and configure both the SRE agent (`OPS_AUTH_TOKEN` env var) and the monitored service to use it.

- **Service Account:** [SRE agent service account with scoped permissions for `/ops/*` endpoints only]
- **Auth Method:** [Bearer token / mTLS / IAM — reference to secrets manager entry]
- **Permissions:** Read-only diagnostics + safe remediation. No write access to application data, infrastructure, or deployments.

## Cloud Platform Access

> The SRE agent requires read-only access to cloud provider APIs for diagnostic correlation. It uses this to understand managed service health alongside the `/ops/*` application endpoints. The agent never modifies cloud infrastructure.

### GCP (if applicable)
- **Required Roles (secrets — all Cloud Run services):**
  - `roles/secretmanager.secretAccessor` — required on the Cloud Run service account (or default compute SA) to read secrets injected via `value_source.secret_key_ref` in Terraform. Without this, the service fails to start.
- **Required Roles (diagnostics — read-only):**
  - `roles/monitoring.viewer` — read metrics and alerting policies
  - `roles/logging.viewer` — query logs
  - `roles/cloudsql.viewer` — database instance status and metrics
  - `roles/redis.viewer` — Memorystore instance status
  - `roles/container.viewer` — GKE cluster, node, and workload status
  - `roles/compute.viewer` — instance and network status
  - `roles/run.viewer` — Cloud Run service and revision status (if applicable)
- **Required Roles (scaling — only if using cloud_native scaling mode):**
  - `roles/run.developer` — update Cloud Run service revision instance counts (if using Cloud Run)
  - `roles/container.developer` — update GKE deployment replica counts (if using GKE)
  - Note: Scope these roles to only the specific services the agent is allowed to scale, not the entire project

### AWS (if applicable)
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
| `SRE_PROMPT_PATH` | `/app/WINDSURF_SRE.md` | Path to WINDSURF_SRE.md inside the container |
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
4. Configure your alerting platform to send webhooks to `<service_url>/webhook/gcp?auth_token=<ops-auth-token>`
5. Alerts flow to the SRE agent; PagerDuty incidents are only created when the agent escalates
