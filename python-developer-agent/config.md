# Developer Agent Configuration

**Instructions:** Fill out this file when setting up the developer agent for a specific project. This provides project-specific context that the agent needs for daily development work.

## Project

- **Project Name:** *[project name]*
- **Repository:** *[new repo URL]*
- **Primary Language:** Python 3.12
- **Framework:** *[framework and version]*
- **Cloud Provider:** *[GCP or AWS]*

## Development Commands

> Commands the agent uses to build, test, lint, and run the project locally.
> Use `N/A — [reason]` for commands that don't apply (e.g., `N/A — no application database`).

| Command | Purpose |
|---|---|
| *[install command — e.g., `pip install -r requirements.txt -r requirements-dev.txt`]* | Install dependencies |
| *[unit test command — e.g., `pytest tests/ -m "not integration"`]* | Run unit tests |
| *[api test command — e.g., `pytest tests/test_api.py`]* | Run API tests |
| *[integration test command — e.g., `pytest tests/ -m integration`]* | Run integration tests |
| *[full test command — e.g., `pytest tests/ --cov=app --cov-fail-under=80`]* | Run all tests with coverage |
| `pylint --disable=import-error --fail-under=10.0 app tests` | Lint check (matches CI) |
| `black --check app tests --skip-string-normalization` | Format check (matches CI) |
| `mypy app/ --ignore-missing-imports --disable-error-code=unused-ignore` | Type check (matches CI) |
| `complexipy app -mx 15 && complexipy tests -mx 15` | Cognitive complexity (matches CI) |
| `pylint --disable=all --enable=duplicate-code app tests` | Duplicate code check |
| `pip-audit` | Dependency vulnerability scan |
| `interrogate app/ tests/ -v` | Docstring coverage |
| `helm lint charts/` | Helm chart lint |
| `act -j black --env-file env.list` | CI pipeline: black job (requires Docker + act) |
| `act -j pytest --env-file env.list` | CI pipeline: pytest job (requires Docker + act) |
| `act -j pylint --env-file env.list` | CI pipeline: pylint job (requires Docker + act) |
| `act -j complexipy --env-file env.list` | CI pipeline: complexipy job (requires Docker + act) |
| `act -j mypy --env-file env.list` | CI pipeline: mypy job (requires Docker + act) |
| `act -j helm_lint` | CI pipeline: helm lint job (requires Docker + act) |
| *[build command — e.g., `docker build -t app:latest .`]* | Build container image |
| *[run command — e.g., `uvicorn app.main:app --host :: --port 8000 --reload`]* | Run locally |
| *[seed command — e.g., `python seed.py` or `N/A — no application database`]* | Seed local database |

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

- **Pipeline Tool:** *[GitHub Actions, Cloud Build, etc.]*
- **Pipeline Definition:** *[path to pipeline file]*
- **Container Registry:** *[registry URL]*
- **Image Tag Strategy:** Commit SHA (`<registry>/<service>:<sha>`)

## Environments

| Environment | URL | Terraform Workspace/Dir | Deploys |
|---|---|---|---|
| Dev | *[TODO: after infra provisioning]* | `terraform/` with `envs/dev.tfvars` | Automatic on merge to `main` |
| Staging | *[TODO: after infra provisioning]* | `terraform/` with `envs/staging.tfvars` | Manual promotion |
| Prod | *[TODO: after infra provisioning]* | `terraform/` with `envs/prod.tfvars` | Manual promotion |

### Terraform

- **State Backend:** *[`gs://` for GCP or `s3://` for AWS with project name]*
- **Terraform Directory:** `terraform/`
- **Variable Files:** `envs/dev.tfvars`, `envs/staging.tfvars`, `envs/prod.tfvars`

## Services

> List all services in this project. Each service should have its own section in a multi-service project.

| Service | Directory | Port | Description |
|---|---|---|---|
| *[service-name]* | *[directory]* | *[port]* | *[description]* |

## Dependencies

### Internal

| Dependency | Type | Registry | Version |
|---|---|---|---|
| *[or "None"]*  | | | |

### External

| Dependency | Purpose | Docs |
|---|---|---|
| *[managed service or third-party API]* | *[purpose]* | *[docs link]* |

## Secrets

> Reference only — never store actual secret values here.

| Secret | Secrets Manager Key | Used By |
|---|---|---|
| *[secret name]* | *[secrets manager path]* | *[service]* |

## Monitoring

- **Dashboard URL:** *[TODO: after setup]*
- **Alerting:** *[TODO: PagerDuty service ID after setup]*
- **Log Query:** *[TODO: saved query URL after setup]*

## Telemetry (OpenTelemetry)

- **OTEL Collector Endpoint:** *[TODO: OTLP endpoint]*
- **Service Name Convention:** *[service name]*
- **Resource Attributes:** `deployment.environment=${ENVIRONMENT},service.version=${COMMIT_SHA}`
- **APM Platform:** *[Cloud Trace, Datadog, etc.]*
- **Trace Sampling:** `1.0` for dev/staging, `0.1` for prod

## SRE Agent Integration

- **SRE Agent Config:** `../sre-agent/config.md`
- **Service Registry Entry:** *[service-name|URL|critical]*
