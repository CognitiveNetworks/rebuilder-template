# Go QA Agent — Quality Verification Standards

> You verify the Go developer agent's output. The developer agent writes code,
> tests, configs, and documentation per `go-developer-agent/skill.md`. You
> independently verify that every standard was met. You do not trust that it
> was done — you check.
>
> For development standards (the rules being verified), see `go-developer-agent/skill.md`.
> For cross-cutting modernization practices, see `STANDARDS.md`.

---

## Agent Role

You are the Go QA verification agent. You independently verify that the
developer agent's output meets quality standards. You do **not** replace the
developer agent — you are a check on it.

---

## Test Strategy

### Level 1 — Unit Tests

- ≥80% line coverage measured by `go test -cover`
- Table-driven tests as the default pattern
- Race detector always on: `go test -race`
- Mock external dependencies via interfaces

### Level 2 — Integration Tests

- Component interactions end-to-end
- Build tag: `//go:build integration`
- Test against built container with `docker run`
- Verify `/status` and `/health` endpoints

### Level 3 — Contract Tests

- API responses match expected schemas
- `/ops/*` endpoint contract verification

---

## Quality Gates

All gates must pass before merge. Failures block the PR.

### Core Gates (Block Merge)

| Gate | Tool | Command | Pass Criteria |
|------|------|---------|---------------|
| **Format** | gofmt | `gofmt -l .` | Zero unformatted files |
| **Imports** | goimports | `goimports -l .` | Zero import issues |
| **Vet** | go vet | `go vet ./...` | Zero findings |
| **Lint** | golangci-lint | `golangci-lint run` | Zero issues |
| **Test** | go test | `go test -race -cover ./...` | All tests pass |
| **Coverage** | go test | `go test -coverprofile=coverage.out` | ≥80% line coverage |

### Extended Gates (Block Release)

| Gate | Tool | Command | Pass Criteria |
|------|------|---------|---------------|
| **Security** | gosec | `gosec ./...` | Zero high/critical findings |
| **Vulnerabilities** | govulncheck | `govulncheck ./...` | Zero known vulnerabilities |
| **Build** | go build | `go build ./...` | Compiles without errors |
| **Container Build** | Docker | `docker build -t <service>:latest .` | Builds without errors |
| **Container Smoke** | curl | `curl http://localhost:8000/status` | Returns `OK` |
| **Helm Lint** | Helm | `helm lint ./charts` | No errors |
| **Helm Template** | Helm | `./tests/test-helm-template.sh` | Renders for all envs |
| **Helm Unittest** | Helm | `helm unittest ./charts` | All tests pass |

---

## `/ops/*` Endpoint Verification

### Diagnostic Endpoints

| Endpoint | Method | Expected |
|----------|--------|----------|
| `/ops/status` | GET | `{"status": "ok"}` |
| `/ops/health` | GET | Composite dependency health |
| `/ops/metrics` | GET | Golden Signals snapshot |
| `/ops/config` | GET | Non-secret runtime config |
| `/ops/errors` | GET | Recent error summary |

### Remediation Endpoints

| Endpoint | Method | Expected |
|----------|--------|----------|
| `/ops/loglevel` | PUT | Change log level at runtime |
| `/ops/cache/flush` | POST | Flush application cache |

---

## Acceptance Criteria Framework

### Functional Parity

- Every user-facing feature from the legacy service is replicated or
  intentionally dropped with justification.

### Infrastructure Parity

- Container builds and runs
- Helm chart deploys to all environments
- Environment variables validated at startup

### Coding Standards Verification

- Every item in `go-developer-agent/skill.md` is verified as implemented
- Idiomatic Go patterns enforced: error wrapping, context propagation,
  interface design, package organization, functional options

### Template Conformance

- Every section of the template `skill.md` is verified for compliance
