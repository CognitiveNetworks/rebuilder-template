# Developer Agent Configuration

**Instructions:** Fill out this file when setting up the developer agent for a specific project. This provides project-specific context that the agent needs for daily development work.

## Project

- **Project Name:** rebuilder-evergreen-tvevents
- **Repository:** https://github.com/CognitiveNetworks/rebuilder-evergreen-tvevents
- **Primary Language:** Python 3.12
- **Framework:** FastAPI (latest) + uvicorn
- **Cloud Provider:** AWS

## Development Commands

> Commands the agent uses to build, test, lint, and run the project locally.
> Use `N/A — [reason]` for commands that don't apply (e.g., `N/A — no application database`).

| Command | Purpose |
|---|---|
| `pip install -r requirements.txt -r requirements-dev.txt` | Install dependencies |
| `pytest tests/ -m "not integration"` | Run unit tests |
| `pytest tests/test_api.py` | Run API tests |
| `pytest tests/ -m integration` | Run integration tests |
| `pytest` | Run all tests |
| `pylint src/app tests --disable=import-error --fail-under=10.0` | Run linter |
| `black --check src tests --skip-string-normalization` | Run formatter check |
| `mypy src/app/ --ignore-missing-imports` | Run type checker |
| `complexipy src -mx 15` | Run complexity check |
| `docker build -t tvevents:latest .` | Build container image |
| `docker compose up --build` | Run locally (full stack) |
| `uvicorn src.app.main:app --reload --port 8000` | Run locally (app only) |
| Automatic via `scripts/init-db.sql` in docker-compose | Seed local database |

## Required Development Tooling

> Quality gate tools that must pass before every commit. See `skill.md` for enforcement rules.
>
> The required tools, their configurations, CI pipeline definitions, Dockerfile pattern,
> entrypoint/environment-check scripts, Helm chart templates, coding practices, and all
> supporting files are defined in the **template repo**, cloned to `template/` during the
> rebuild process (see `rebuild-inputs/<project>/template/`). The canonical source is
> [`rebuilder-evergreen-template-repo-python`](https://github.com/CognitiveNetworks/rebuilder-evergreen-template-repo-python).
>
> **Read `template/skill.md` first.** It is the authoritative checklist — every item in it
> is mandatory. The README is supplementary context; `skill.md` is the punch list. Complete
> every checkbox in `template/skill.md` during the Build phase. Do not invent your own
> tooling, configs, or patterns — match what the template repo specifies. If an item does
> not apply, mark it N/A with a justification.
>
> The template repo is **not** an adjacent repo. Adjacent repos (`adjacent/`) are production
> code dependencies. The template repo (`template/`) is the build standard.

## CI/CD

- **Pipeline Tool:** GitHub Actions
- **Pipeline Definition:** `.github/workflows/ci.yml`
- **Container Registry:** AWS ECR
- **Image Tag Strategy:** Commit SHA (`<registry>/<service>:<sha>`)

## Environments

| Environment | URL | Terraform Workspace/Dir | Deploys |
|---|---|---|---|
| Dev | *[TODO: after infra provisioning]* | `terraform/` with `envs/dev.tfvars` | Automatic on merge to `main` |
| Staging | *[TODO: after infra provisioning]* | `terraform/` with `envs/staging.tfvars` | Manual promotion |
| Prod | *[TODO: after infra provisioning]* | `terraform/` with `envs/prod.tfvars` | Manual promotion |

### Terraform

- **State Backend:** `s3://tvevents-terraform-state`
- **Terraform Directory:** `terraform/`
- **Variable Files:** `envs/dev.tfvars`, `envs/staging.tfvars`, `envs/prod.tfvars`

## Services

> List all services in this project. Each service should have its own section in a multi-service project.

| Service | Directory | Port | Description |
|---|---|---|---|
| tvevents-api | `src/app/` | 8000 | TV event ingestion API — receives, validates, transforms, and forwards SmartCast TV telemetry to Kafka |

## Dependencies

### Internal

| Dependency | Type | Registry | Version |
|---|---|---|---|
| kafka_module | Local path dependency | `../rebuilder-evergreen-kafka-python` | latest |
| rds_module | Local path dependency | `../rebuilder-evergreen-rds-python` | latest |

### External

| Dependency | Purpose | Docs |
|---|---|---|
| AWS RDS PostgreSQL | Blacklisted channel ID lookups (via rds_module) | [RDS Docs](https://docs.aws.amazon.com/rds/) |
| Kafka (MSK or self-hosted) | Event data delivery (via kafka_module, replaces Kinesis Firehose) | [Kafka Docs](https://kafka.apache.org/documentation/) |
| New Relic (via OTEL) | Observability — traces, metrics, logs | [New Relic OTLP](https://docs.newrelic.com/docs/more-integrations/open-source-telemetry-integrations/opentelemetry/) |

## Secrets

> Reference only — never store actual secret values here.

| Secret | Secrets Manager Key | Used By |
|---|---|---|
| T1_SALT | `tvevents/tvcdb/T1_SALT` | tvevents-api (HMAC security hash) |
| DB_PASSWORD | `tvevents/tvcdb/RDS_PASS` | tvevents-api (via rds_module) |
| KAFKA_SASL_USERNAME | `tvevents/kafka/SASL_USERNAME` | tvevents-api (via kafka_module) |
| KAFKA_SASL_PASSWORD | `tvevents/kafka/SASL_PASSWORD` | tvevents-api (via kafka_module) |
| OTEL_EXPORTER_OTLP_HEADERS | `inscape/o11y-config/OTLP_HEADERS` | tvevents-api (New Relic API key) |

## Monitoring

- **Dashboard URL:** <!-- TODO: New Relic dashboard URL after setup -->
- **Alerting:** <!-- TODO: PagerDuty service ID after setup -->
- **Log Query:** <!-- TODO: New Relic saved query URL after setup -->

## Telemetry (OpenTelemetry)

- **OTEL Collector Endpoint:** `https://otlp.nr-data.net:443` (via OTEL Collector sidecar)
- **Service Name Convention:** `tvevents-api`
- **Resource Attributes:** `deployment.environment=${ENV},service.version=${COMMIT_SHA}`
- **APM Platform:** New Relic (via OTLP HTTP)
- **Trace Sampling:** `1.0` for dev/staging, `0.1` for prod

## SRE Agent Integration

- **SRE Agent Config:** `../sre-agent/config.md`
- **Service Registry Entry:** `tvevents-api|<!-- TODO: URL after infra -->|true`
