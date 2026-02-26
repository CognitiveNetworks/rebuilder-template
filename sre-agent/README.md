# SRE Agent

An incident response agent that receives alerts from your monitoring platform (GCP Cloud Monitoring, New Relic, Datadog, etc.), diagnoses service health issues using your application's `/ops/*` endpoints, takes safe remediation actions, and escalates to humans via PagerDuty when it cannot confidently resolve an issue.

The agent uses any **OpenAI-compatible LLM API** (GitHub Models, OpenAI, Azure OpenAI, etc.) as its reasoning engine. It runs headlessly — fully autonomous, 24/7 incident response with no IDE or human in the loop. Alerts flow from your monitoring platform directly to the agent — humans are only paged via PagerDuty if the agent cannot resolve the issue. The agent diagnoses by calling tools (service `/ops/*` endpoints, cloud APIs), and decides whether to remediate or escalate. It does not guess. If it cannot diagnose the issue from the available data, it escalates with a full summary of what it checked and what it found.

## What It Does

1. **Receives alerts** — accepts webhooks from monitoring platforms (GCP Cloud Monitoring, New Relic, Datadog, etc.) via `POST /webhook/gcp`.
2. **Deduplicates and prioritizes** — rejects duplicate alerts for the same incident, serializes alerts per service, and queues by priority (P1 first). Stale queued alerts expire automatically.
3. **Runs the agentic loop** — on every alert, `agent.py` reads the full text of `WINDSURF_SRE.md` from disk and sends it to the LLM as the **system prompt** — the first message in the conversation. The alert payload is then sent as the first **user message**. This means `WINDSURF_SRE.md` is the single document that defines everything the agent knows, believes, and is allowed to do. The diagnostic workflow, escalation rules, remediation actions, hard safety constraints, and tech-stack context are all encoded in this one file. If it's not in the system prompt, the agent doesn't know about it. The LLM responds with function calls (`tool_use`), the agent executes them via `tools.py`, feeds the results back, and the loop continues — up to 20 turns or 5 minutes — until the issue is resolved or escalated.
4. **Diagnoses the issue** — checks `/ops/status` for a composite health verdict, then drills into `/ops/health`, `/ops/metrics`, `/ops/errors`, and `/ops/dependencies`. Follows the dependency chain to find the root cause.
5. **Classifies the problem** — infrastructure, application, dependency, data, or configuration.
6. **Matches a playbook** — checks if the classification matches a remediation playbook (high error rate, high latency, dependency failure, saturation, certificate expiry).
7. **Remediates safely** — executes playbook actions: cache flush, circuit breaker reset, instance drain, log level adjustment, and bounded scaling (within configured min/max limits). All actions are idempotent and non-destructive.
8. **Verifies the fix** — waits 5 minutes after remediation, re-checks `/ops/status`, and monitors for stability.
9. **Escalates when unsure** — if no playbook matches, remediation fails, or the issue involves data integrity, security, or infrastructure changes, the agent escalates to a human by creating a PagerDuty incident with a full diagnostic summary and recommended next action. Humans are only paged when the agent can't resolve it.
10. **Documents everything** — writes a structured incident report for every alert it responds to, whether resolved or escalated.

## What It Does NOT Do

- Deploy code or trigger rollbacks
- Modify infrastructure beyond bounded scaling (no config changes, no IAM modifications, no instance type changes)
- Scale beyond configured min/max limits per service
- Access or rotate secrets
- Delete data or modify persistent state
- Guess. If the diagnosis is uncertain, it escalates.

## Directory Structure

```
sre-agent/
├── README.md              # This file
├── WINDSURF_SRE.md        # Agent instructions — loaded as system prompt
├── config.md              # Per-project config — service registry, SLOs, PagerDuty, escalation
├── playbooks/             # Remediation playbooks by incident type
│   ├── high-error-rate.md
│   ├── high-latency.md
│   ├── dependency-failure.md
│   ├── saturation.md
│   ├── certificate-expiry.md
│   └── service-down.md
├── incidents/             # Agent-written incident reports
│   └── .gitkeep
└── runtime/               # Agent runtime — webhook listener + agentic loop
    ├── README.md          # Runtime architecture, setup, and deployment guide
    ├── main.py            # FastAPI app — webhook receiver, /ops/* endpoints
    ├── agent.py           # Agentic loop — OpenAI-compatible LLM orchestration
    ├── tools.py           # Tool definitions and executor
    ├── config.py          # Configuration from environment variables
    ├── models.py          # Pydantic models for alert payloads
    ├── state.py           # Runtime state tracking for Golden Signals
    ├── intake.py          # Alert intake pipeline — dedup, serialization
    ├── telemetry.py       # OpenTelemetry initialization and metric instruments
    ├── requirements.txt   # Python dependencies
    ├── requirements-dev.txt # Dev dependencies — pytest, ruff
    ├── pyproject.toml     # Linter and test configuration
    ├── .env.example       # Environment variable template for local development
    ├── Dockerfile         # Container image
    ├── tests/             # Unit and API tests
    └── terraform/         # Cloud Run deployment
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

## Key Files

### `WINDSURF_SRE.md`

The agent's operating instructions — and the **single most important file** in the SRE agent. On every alert, `agent.py` reads this file from disk and sends it to the LLM as the `system` message (the first message in the conversation). The alert becomes the first `user` message. Everything the agent knows, every decision it makes, and every constraint it follows comes from this file. If a behavior isn't defined here, the agent won't exhibit it.

This is a **template** with placeholder sections — it is populated with the project's tech stack during the rebuild process (Step 7) and baked into the container image at build time. The condensed prompt fits within GitHub Models' 8k token limit.

**Why this matters:** The system prompt is not a configuration file or a set of rules the agent "checks" — it is the agent's entire identity and knowledge base for each incident. Changing this file changes the agent's diagnostic approach, escalation thresholds, remediation behavior, and safety constraints. The runtime code (`agent.py`, `tools.py`) is generic infrastructure — `WINDSURF_SRE.md` is what makes it an SRE agent.

It defines:

- **Role** — diagnose and stabilize only, no features, no deployments
- **Tech stack** — placeholder, populated per-project during rebuild
- **Diagnostic workflow** — 7-step process: check status, drill into health/deps/errors, classify, remediate or escalate
- **Escalation rules** — when to stop trying and hand off to a human (uses `create_pagerduty_incident` to page humans)
- **Remediation actions** — cache flush, circuit reset, drain, log level, bounded scaling (all idempotent)
- **Hard rules** — API-only access, no destructive actions, no deployments, no secret access, no guessing
- **Incident report requirement** — must call `write_incident_report` and `email_incident_report` for every alert

> [!NOTE]
> **Loading path:** `SRE_PROMPT_PATH` env var → defaults to `/app/WINDSURF_SRE.md` in the container. `config.load_system_prompt()` reads the file on every agent run. The `/ops/health` endpoint verifies the file exists and is readable.

### `config.md`

Per-project configuration template. Fill this out when setting up the agent for a specific project:

- **Service registry** — every service the agent monitors, with base URLs for `/ops/*` endpoints
- **Tech stack** — auto-populated from the rebuild process
- **PagerDuty integration** — API token reference, escalation policy, service IDs, routing key for creating incidents on escalation
- **SLO thresholds** — per-service availability, latency, and error rate targets
- **Escalation contacts** — who gets paged at each priority level
- **Agent auth** — service account and permissions for `/ops/*` endpoints
- **Cloud platform access** — required IAM roles (GCP) or policies (AWS) for read-only diagnostic access
- **Runtime configuration** — environment variables for the deployed service

### `playbooks/`

Remediation playbooks for common incident types. Each playbook defines:

- **Trigger condition** — what alert pattern activates this playbook
- **Diagnostic steps** — ordered sequence of `/ops/*` endpoint calls to gather data
- **Remediation actions** — condition-to-action table (what to do for each scenario)
- **After remediation** — verification steps (wait, re-check, monitor)
- **Escalation criteria** — when the playbook's actions are insufficient

Included playbooks:

| Playbook | Trigger |
|---|---|
| `high-error-rate.md` | Elevated 5xx responses, unhandled exceptions |
| `high-latency.md` | p95/p99 latency above SLO threshold |
| `dependency-failure.md` | Downstream service or external API unreachable |
| `saturation.md` | CPU, memory, disk, connection pool, or queue exhaustion |
| `certificate-expiry.md` | TLS certificate expired or expiring (always escalates) |
| `service-down.md` | Cloud Run service unreachable or scaled to zero |

### `runtime/`

The agent runtime. A Python/FastAPI application that:

- Listens for monitoring platform webhooks on `POST /webhook/gcp`
- Verifies auth tokens
- Deduplicates, validates, and dispatches alerts to the agentic diagnostic loop
- Runs `agent.py` to diagnose and remediate using any OpenAI-compatible LLM
- Exposes its own `/ops/*` endpoints for self-observability (Golden Signals, composite health, dependencies)
- Exports metrics, traces, and logs via OpenTelemetry (OTLP) to APM platforms — runs as a no-op when not configured
- Emits structured JSON logs with trace ID correlation
- Supports drain mode and graceful shutdown
- Includes unit and API tests, linter config (ruff), and `.env.example` for local development

See `runtime/README.md` for setup, testing, deployment, and customization instructions.

## How It Connects to the Rebuild Process

1. **`rebuild/run.sh`** generates a PRD from the legacy assessment.
2. **Step 7** of the rebuild process auto-populates `WINDSURF_SRE.md` and `config.md` with the tech stack from the chosen rebuild candidate.
3. Your rebuilt services expose `/ops/*` endpoints as defined in `WINDSURF.md`.
4. You fill in the remaining fields in `config.md` — service URLs, PagerDuty escalation config, escalation contacts.
5. You deploy the runtime from `runtime/`.
6. You configure your monitoring platform to send webhooks to `/webhook/gcp` on the agent.
7. You set `PAGERDUTY_ROUTING_KEY` (Events API v2 integration key) so the agent can create PagerDuty incidents when it escalates.
8. The agent is operational — alerts are received, diagnosed, and remediated or escalated automatically.

## Prerequisites

- **LLM provider** — Vertex AI (recommended for GCP — uses ADC, no API key), GitHub Models (GitHub PAT), OpenAI, or any OpenAI-compatible provider
- **Services with `/ops/*` endpoints** — the agent has no value if the services it monitors don't expose diagnostic and remediation endpoints
- **PagerDuty** — Events API v2 integration key (`PAGERDUTY_ROUTING_KEY`, stored in Secret Manager) for creating incidents on escalation. API token for managing incident lifecycle.
- **Cloud provider IAM** — read-only access to cloud monitoring, logging, and managed service status (see `config.md` for required roles/policies)

## How the Agent Interacts with Services

The agent operates exclusively through HTTP APIs. It has no direct access to infrastructure.

- **No SSH.** The agent does not connect to servers, containers, or VMs.
- **No kubectl.** The agent does not run commands against Kubernetes clusters.
- **No database connections.** The agent does not query databases directly.
- **No shell access.** The agent does not execute commands on any system.

Every interaction goes through one of three API surfaces:

| Interface | Purpose | Examples |
|---|---|---|
| **Service `/ops/*` endpoints** | Diagnose and remediate application-level issues | `GET /ops/status`, `POST /ops/cache/flush`, `POST /ops/drain`, `POST /ops/scale` |
| **Cloud provider APIs** | Infrastructure diagnostics + bounded scaling | Cloud Monitoring metrics, Cloud Logging queries, managed service status, replica count adjustments (within configured limits) |
| **PagerDuty API** | Escalation to humans | Create incidents (Events API v2), add notes, manage incident lifecycle |

This means the agent can only act on services that expose `/ops/*` endpoints. If a service doesn't implement the `/ops/*` contract defined in `WINDSURF.md`, the agent cannot diagnose or remediate it — it can only escalate based on the alert context alone.

## Observability Model

The SRE agent **diagnoses** services through their `/ops/*` endpoints — pull-based, on-demand queries that return structured health snapshots. This is the agent's primary interface for understanding service state. OTEL does not change this.

The SRE agent runtime **also instruments itself** with OpenTelemetry because it is a service, and all services in the platform follow the same observability standard defined in `WINDSURF.md`. The agent's own OTEL telemetry (metrics, traces, logs) flows to your APM platform for dashboards and alerting on the agent itself — webhook throughput, agent run duration, error rates, intake queue depth.

These are separate concerns:

| Interface | Direction | Purpose |
|---|---|---|
| `/ops/*` endpoints on monitored services | Agent pulls from services | Diagnose and remediate service health issues |
| `/ops/*` endpoints on the SRE agent runtime | Humans/agents pull from agent | Monitor the agent's own health |
| OTEL from monitored services | Services push to APM | Continuous telemetry for dashboards and alerting |
| OTEL from the SRE agent runtime | Agent pushes to APM | Continuous telemetry for the agent's own operational visibility |

The developer-agent defines OTEL as a standard that developers implement in every service they build. The SRE agent follows that same standard for itself — it does not consume OTEL data from other services. See `runtime/README.md` for the agent's OTEL configuration and exported instruments.

## Design Principles

- **API-only access.** The agent interacts with services and cloud providers exclusively through HTTP APIs. No SSH, no shell, no direct infrastructure access. If it can't be done through an API, the agent escalates.
- **Diagnose and stabilize, never modify beyond safe bounds.** The agent reads system state and takes safe, reversible actions. It can scale services within pre-configured min/max limits but does not deploy, rotate secrets, or change configuration.
- **No guessing.** If the agent cannot confidently diagnose the issue from the available data, it escalates immediately with everything it knows.
- **Every action is logged.** Diagnostic calls, remediation actions, escalations — all recorded in the incident report with timestamps.
- **Playbooks over improvisation.** The agent follows defined playbooks. If no playbook matches, it escalates rather than inventing a fix.
- **The agent monitors itself.** The runtime exposes the same `/ops/*` contract it expects from the services it monitors.

## LLM Provider

The agent uses the OpenAI Python SDK to call any OpenAI-compatible LLM API. The default provider is **GitHub Models** (gpt-4o via `https://models.inference.ai.azure.com`), authenticated with a GitHub PAT.

Swap providers by changing two environment variables:

| Provider | `LLM_API_KEY` | `LLM_API_BASE_URL` |
|---|---|---|
| GitHub Models (default) | GitHub PAT | `https://models.inference.ai.azure.com` |
| OpenAI | OpenAI API key | `https://api.openai.com/v1` |
| Azure OpenAI | Azure key | `https://your-resource.openai.azure.com/openai/deployments/your-deployment` |
| Any OpenAI-compatible | Provider key | Provider's base URL |

See `runtime/README.md` for the full environment variable reference.
