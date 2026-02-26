# Developer Agent Configuration

**Instructions:** Fill out this file when setting up the developer agent for a specific project. This provides project-specific context that the agent needs for daily development work.

## Project

- **Project Name:** *[project name]*
- **Repository:** *[new repo URL]*
- **Primary Language:** *[language and version]*
- **Framework:** *[framework and version]*
- **Cloud Provider:** *[GCP or AWS]*

## Development Commands

> Commands the agent uses to build, test, lint, and run the project locally.

| Command | Purpose |
|---|---|
| *[install command]* | Install dependencies |
| *[unit test command]* | Run unit tests |
| *[api test command]* | Run API tests |
| *[integration test command]* | Run integration tests |
| *[full test command]* | Run all tests |
| *[lint command]* | Run linter / formatter |
| *[build command]* | Build container image |
| *[run command]* | Run locally |
| *[seed command]* | Seed local database |

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
