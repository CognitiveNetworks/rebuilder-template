# Go Developer Agent — Project Configuration

> This file contains project-specific values. It is populated during the
> ideation process (Step 8b) or manually for new projects. The
> `go-developer-agent/skill.md` file defines the universal standards; this
> file maps those standards to a specific project.

---

## Project

| Field | Value |
|-------|-------|
| **Name** | *[TODO: project name]* |
| **Repository** | *[TODO: repo URL]* |
| **Language** | Go ≥ 1.22 |
| **Framework** | *[TODO: net/http, chi, gin, fiber]* |
| **Cloud Provider** | *[TODO: AWS / GCP]* |

---

## Development Commands

| Action | Command |
|--------|---------|
| **Build** | `go build ./...` |
| **Unit test** | `go test -race -cover ./...` |
| **Lint** | `golangci-lint run` |
| **Vet** | `go vet ./...` |
| **Format check** | `gofmt -l .` |
| **Import check** | `goimports -l .` |
| **Security scan** | `gosec ./...` |
| **Vulnerability check** | `govulncheck ./...` |
| **Tidy deps** | `go mod tidy && go mod verify` |
| **Docker build** | `docker build -t <service>:latest .` |
| **Docker run** | `docker run -d -p 8000:8000 -e TEST_CONTAINER=true -e ENV=dev -e LOG_LEVEL=DEBUG --name <service> <service>:latest` |
| **Helm lint** | `helm lint ./charts` |
| **Helm template** | `./tests/test-helm-template.sh` |
| **Helm unittest** | `helm unittest ./charts` |

---

## Required Development Tooling

> Quality gate tools that must pass before every commit. See `skill.md` for enforcement rules.
>
> The required tools, their configurations, CI pipeline definitions, Dockerfile pattern,
> entrypoint/environment-check scripts, Helm chart templates, coding practices, and all
> supporting files are defined in the **template repo**, cloned to `template/` during the
> rebuild process (see `<dest>/template/`). The canonical source is
> [`rebuilder-evergreen-template-repo-go`](https://github.com/CognitiveNetworks/rebuilder-evergreen-template-repo-go).
>
> **Read `template/skill.md` first.** It is the authoritative checklist — every item in it
> is mandatory. The README is supplementary context; `skill.md` is the punch list. Complete
> every checkbox in `template/skill.md` during the Build phase. Do not invent your own
> tooling, configs, or patterns — match what the template repo specifies. If an item does
> not apply, mark it N/A with a justification.

The authoritative checklist is in `go-developer-agent/skill.md` → Required
Development Tooling. This table is the project-specific invocation.

---

## CI/CD

| Field | Value |
|-------|-------|
| **Pipeline tool** | GitHub Actions |
| **Pipeline definition** | `.github/workflows/commit.yml` |
| **Container registry** | *[TODO: ECR / Artifact Registry URL]* |
| **Image tag strategy** | `{app}-{branch}-{commit-sha}` |

---

## Environments

| Environment | URL | Terraform Workspace | Deploy Trigger |
|-------------|-----|-------------------|----------------|
| **Dev** | *[TODO]* | `dev` | Automatic on merge to `prerelease` |
| **Staging** | *[TODO]* | `staging` | Manual promotion |
| **Prod** | *[TODO]* | `prod` | Manual promotion |

---

## Terraform

| Field | Value |
|-------|-------|
| **State backend** | *[TODO: S3 / GCS bucket]* |
| **Directory** | `terraform/` |
| **Variable files** | `terraform/envs/{env}.tfvars` |

---

## Services

| Name | Directory | Port | Description |
|------|-----------|------|-------------|
| *[TODO]* | `cmd/app/` | 8000 | *[TODO: service description]* |

---

## Dependencies

### Internal

| Dependency | Registry | Version |
|------------|----------|---------|
| *[TODO]* | *[TODO]* | *[TODO]* |

### External (Managed Services)

| Service | Provider | Purpose |
|---------|----------|---------|
| *[TODO]* | *[TODO]* | *[TODO]* |

---

## Secrets

> Never store actual secret values here. Reference only.

| Secret | Source | Used By |
|--------|--------|---------|
| *[TODO]* | *[TODO: AWS Secrets Manager / GCP Secret Manager]* | *[TODO]* |

---

## Monitoring

| Field | Value |
|-------|-------|
| **Dashboard** | *[TODO: Grafana / Datadog URL]* |
| **Alerting** | *[TODO: PagerDuty / OpsGenie]* |
| **Log query** | *[TODO: CloudWatch / Cloud Logging query]* |

---

## Telemetry (OTEL)

| Field | Value |
|-------|-------|
| **Collector endpoint** | *[TODO]* |
| **Service name** | *[TODO]* |
| **Resource attributes** | `service.name`, `deployment.environment` |
| **APM platform** | *[TODO: Grafana / Datadog / New Relic]* |
| **Trace sampling** | `1.0` (dev/staging), `0.1` (prod) |

---

## SRE Agent Integration

| Field | Value |
|-------|-------|
| **SRE config path** | `sre-agent/config.md` |
| **Service registry** | *[TODO: populated in Step 7]* |
