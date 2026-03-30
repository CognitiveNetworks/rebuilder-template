# Go QA Agent — Project Configuration

> This file contains project-specific QA values. Populated during ideation
> Step 8d or manually for new projects.

---

## Project

| Field | Value |
|-------|-------|
| **Name** | *[TODO: project name]* |
| **Repository** | *[TODO: repo URL]* |
| **Language** | Go ≥ 1.22 |
| **Framework** | *[TODO: net/http, chi, gin, fiber]* |
| **Original Legacy Repo** | *[TODO: legacy repo URL]* |

---

## Test Commands

| Tool | Command | Gate |
|------|---------|------|
| **gofmt** | `gofmt -l .` | Format |
| **goimports** | `goimports -l .` | Imports |
| **go vet** | `go vet ./...` | Vet |
| **golangci-lint** | `golangci-lint run` | Lint |
| **go test** | `go test -race -cover ./...` | Unit test |
| **go cover** | `go test -coverprofile=coverage.out ./...` | Coverage |
| **gosec** | `gosec ./...` | Security |
| **govulncheck** | `govulncheck ./...` | Vulnerabilities |
| **go build** | `go build ./...` | Build |
| **helm lint** | `helm lint ./charts` | Helm |
| **helm template** | `./tests/test-helm-template.sh` | Helm |
| **helm unittest** | `helm unittest ./charts` | Helm |

---

## Quality Gate Thresholds

| Gate | Threshold | Blocking Stage |
|------|-----------|----------------|
| gofmt | Zero unformatted files | Merge |
| goimports | Zero import issues | Merge |
| go vet | Zero findings | Merge |
| golangci-lint | Zero issues | Merge |
| go test | All pass, -race clean | Merge |
| Coverage | ≥80% | Merge |
| gosec | Zero high/critical | Release |
| govulncheck | Zero known vulns | Release |
| Container build | Succeeds | Release |
| Container smoke | `/status` → `OK` | Release |
| Helm lint | No errors | Release |

---

## Test Environments

| Environment | Dependencies | Purpose |
|-------------|-------------|---------|
| **Local** | Mocked via interfaces | Developer iteration |
| **CI** | Mocked via interfaces | PR validation |
| **Dev** | Real (deployed) | Integration verification |
| **Staging** | Real (deployed) | Pre-production validation |

---

## Required Test Environment Variables

| Variable | Test Default | Purpose |
|----------|-------------|---------|
| `ENV` | `dev` | Environment name |
| `LOG_LEVEL` | `DEBUG` | Logging verbosity |
| `TEST_CONTAINER` | `true` | Skip external deps in smoke test |
| `SERVICE_NAME` | `local-testing` | OTEL service identifier |

---

## Acceptance Criteria — App-Specific

### API Endpoints to Verify

| Method | Path | Expected Status |
|--------|------|----------------|
| GET | `/status` | 200 — `OK` |
| GET | `/health` | 200 — composite health |
| *[TODO]* | *[TODO]* | *[TODO]* |

### Environment Variable Mapping

| Original (Legacy) | Rebuilt | Notes |
|-------------------|---------|-------|
| *[TODO]* | *[TODO]* | *[TODO]* |
