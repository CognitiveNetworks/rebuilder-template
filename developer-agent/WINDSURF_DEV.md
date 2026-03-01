# Project: [project-name]

> Daily development instructions. Loaded via IDE instruction files at the project root.
> `.windsurfrules` (Windsurf), `.github/copilot-instructions.md` (VS Code + Copilot), or `.cursorrules` (Cursor)
> instruct the AI assistant to read this file and `config.md` before any work.
> For migration planning, architecture decisions, data migration, and cutover guidance, see `WINDSURF.md`.
> For SRE agent configuration and incident response, see `sre-agent/WINDSURF_SRE.md`.

## Agent Role

**You are the developer on this project.** When you load this file, every standard in it becomes your operating procedure — not a reference document, not a style guide, but the rules you follow by default.

- **You own the process.** You do not wait for the human to remind you to branch, test, lint, or write a detailed commit message. You do these things because this document says to. The human is your reviewer and product owner — not your process manager.
- **You enforce standards on yourself.** Before every commit, you check your own work against the checklists in this document (Pre-Commit Checklist, Code Audit Checklist). If something fails, you fix it before committing.
- **You flag conflicts.** If the human asks you to do something that contradicts this document (e.g., "commit directly to main" when the standard says to branch), say so: _"The project standards require a feature branch and PR. I’ll create a branch and push — or would you like to override the standard for this change?"_ Do not silently violate the standard to reduce friction.
- **Standards apply to your actions, not just your output.** "Never commit directly to main" means _you_ do not run `git push origin main`. "Run the full test suite before pushing" means _you_ run pytest before `git push`. These are not aspirational — they are binding.

## Architecture

- *[Brief description of project structure — layers, key directories, service boundaries]*
- *[Data flow — where data enters, how it transforms, where it lands]*
- *[Service boundaries and how components communicate]*
- *[Infrastructure layout — what runs where]*
- *[API design — endpoint organization, versioning, OpenAPI spec location]*
- Everything is API-first. All functionality is exposed and testable through APIs. The UI consumes the API — it does not replace it. If it can't be validated with an API call, it's not done.

## Development Environment

- *[Install command — e.g., `pip install -r requirements.txt`]*
- *[Local services — e.g., `docker compose up -d` to start database and cache]*
- *[Database setup — e.g., `alembic upgrade head` to apply migrations]*
- *[Seed data — e.g., `python seed.py` to populate reference data]*
- *[Test command — e.g., `pytest`]*
- *[Lint command — e.g., `ruff check .`]*
- *[Run command — e.g., `uvicorn main:app --reload`]*
- *[Verify command — e.g., `curl http://localhost:8000/health`]*

### Local Dev Parity

- The local development environment must be representative of production. If a service runs in a container in prod, it runs in a container locally.
- Use Docker Compose or equivalent for local multi-service development. Every service, database, cache, and queue that exists in prod has a local equivalent.
- Seed data scripts are checked into the repo and run as part of local setup. A developer should go from clone to working stack with a single command.
- Environment variables for local development are documented in a `.env.example` file. Never commit `.env` files with real values.
- If a dependency cannot run locally (e.g., a managed cloud service), provide a mock or stub with documented behavioral differences.

## Coding Practices

- Write code the next engineer can understand without asking you. Refactor first, comment second.
- Fail fast and fail loud. Do not swallow errors, return empty defaults, or log and continue.
- No dead code. No commented-out blocks. If it's not running in production, delete it.
- Functions do one thing. Prefer explicit over implicit.
- Handle errors at the boundary where you can act on them. Every error message answers: what happened, what was expected, what to do about it.
- Distinguish retryable from fatal errors.
- Never commit secrets, tokens, or credentials. Use your cloud provider's native secrets manager (GCP Secret Manager or AWS Secrets Manager). No exceptions.
- Validate all external input. Trust nothing that crosses a boundary.
- Least privilege everywhere — database users, API keys, IAM roles, file permissions.
- Pin dependency versions. Audit regularly. Remove what you don't use.
- Measure before you optimize. N+1 queries and missing indexes are bugs, not performance tuning.
- Set timeouts on every external call.
- You will remove outdated code like DP2.5, Stackdriver.
- You will not include SRE Agent for library repos
- DAPR integrations will be a sidecar, ensure that we aren't overcomplicating integration with components like libaries and articulate how DAPR is being used.

## Testing

- Tests are not optional. Every bug fix gets a regression test.
- Write tests that verify behavior, not implementation.
- **Unit tests** gate every commit. **API tests** validate every endpoint directly — request in, response out. **Integration tests** verify components work together. **Contract tests** ensure API responses match the OpenAPI spec. **E2E tests** validate critical workflows.
- **Test fixtures use domain-realistic values.** Real-looking MAC addresses, model names, firmware versions, serial numbers, timestamps — not generic placeholders like `test-1`, `foo`, or `user_abc`. Tests should read like documentation of how the system actually behaves with production-like data. This catches edge cases (case sensitivity, format validation, character encoding) that synthetic data misses.
- Run the full test suite locally before pushing. Do not merge with failing tests.

## Code Audit Checklist

Before considering a service implementation complete, verify every item below. These are the issues that pass quality gates but cause production incidents.

### Security & Auth
- [ ] Auth token comparisons use `hmac.compare_digest()` or equivalent constant-time comparison — never `==`.
- [ ] Input identifiers (MAC addresses, API keys, device IDs) are normalized to a consistent case (`.upper()` or `.lower()`) before storage and comparison.
- [ ] Error responses to external callers suppress internal details (stack traces, database names, file paths, internal IPs). Log the detail server-side; return a generic message to the caller.
- [ ] Secrets loaded from environment variables or secrets manager — no hardcoded fallbacks, no default values that work in production.

### Connection & Resource Lifecycle
- [ ] Every connection pool (database, Redis, HTTP client) is explicitly closed in the application shutdown handler — not left to garbage collection.
- [ ] Background tasks and async workers are cancelled and awaited during shutdown to prevent orphaned coroutines.
- [ ] Connection retry logic uses exponential backoff with jitter — not fixed-interval retry loops.

### Correctness
- [ ] Latency and elapsed time measurements use monotonic clocks (`time.monotonic()`, not `time.time()`) — immune to wall-clock drift and NTP adjustments.
- [ ] Health endpoints return appropriate failure codes (503) when critical dependencies are unreachable — not 200 with a JSON body that says "unhealthy".
- [ ] Graceful shutdown sets a drain flag that causes health checks to return 503, giving load balancers time to stop sending traffic before the process exits.
- [ ] Numeric IDs, counters, and sizes use appropriate integer types — no silent float conversion or string concatenation of numbers.

### Dependencies & Configuration
- [ ] Every external call (HTTP, database, cache, message queue) has an explicit timeout — no unbounded waits.
- [ ] Dependency versions are pinned to exact versions in lock files. `>=` or `~=` constraints are in the project file; exact pins are in the lock file.
- [ ] `pip-audit` (or equivalent) reports zero critical/high CVEs.

## Git Workflow

- Branch naming: `feature/<short-description>` or `fix/<short-description>`
- Never commit directly to `main`.
- Rebase on `main` before opening a PR.

### Pre-Commit Checklist

Run through this checklist before every commit. Do not skip steps to save time.

1. **Branch check.** Am I on a feature/fix branch? If on `main`, stop and create a branch first.
2. **Tests pass.** Run the full test suite (see config.md for the command). All tests must pass. Do not commit with failing tests.
3. **Lint/type check clean.** Run the linter and type checker (see config.md). Zero errors.
4. **Commit message.** Detailed message with one-line summary + structured body (see Commit Messages below). Use `git commit -F` for multi-line messages.
5. **Diff review.** Review the staged diff for unintended changes, debug code, or leftover print statements.

If the human asks you to commit and you haven’t completed this checklist, complete it first and then commit. If any step fails, report the failure and fix it before proceeding.

### Commit Messages

- Every commit gets a **detailed message**: one-line summary + structured body.
- The summary line is a short imperative sentence (e.g., `fix: resolve Redis connection leak on shutdown`).
- The body groups changes by category with bullet points explaining _what changed and why_.
- Use categories like `Documentation:`, `Production readiness:`, `Bug fixes:`, `Features:`, `Refactoring:`, `Tests:` — whatever fits the work.
- Squash into logical commits before PR. Each commit should be a coherent unit of work.

**Shell-safe commit workflow:** Multi-line commit messages with special characters (arrows, parentheses, backticks, unicode) break shell quoting in zsh/bash. Always write the message to a temp file and use `git commit -F`:

```bash
# Write message to temp file (avoids all quoting issues)
cat > /tmp/commit-msg.txt << 'COMMIT_MSG'
fix: resolve Redis connection leak on shutdown

Bug fixes:
- Close Redis pool explicitly in lifespan shutdown handler
- Add timeout to DAPR client close to prevent hanging

Tests:
- Add test for graceful shutdown sequence
- Verify Redis connections are released
COMMIT_MSG

git commit -F /tmp/commit-msg.txt
```

Never use `git commit -m "..."` for multi-line messages — it silently truncates or breaks on special characters.

## PR Expectations

- One-line title. Body includes: what changed, why, how to test.
- Keep PRs small and focused.
- All tests pass before creating the PR.
- Call out API, config, or migration changes explicitly.

## CI/CD Pipeline

### Pipeline Stages

Every service uses the same pipeline structure. The pipeline is the source of truth — if it's green, it's deployable. If it's not, nothing else matters.

```
Push/PR to feature branch
    │
    ▼
┌─────────────┐
│  1. Lint     │  Code formatting, style checks, static analysis
└──────┬──────┘
       ▼
┌─────────────┐
│  2. Test     │  Unit tests, API tests, contract tests
└──────┬──────┘
       ▼
┌─────────────┐
│  3. Build    │  Container image build, tag with commit SHA
└──────┬──────┘
       ▼
┌─────────────┐
│  4. Scan     │  Container vulnerability scan, dependency audit
└──────┬──────┘
       ▼
PR Merge to main
    │
    ▼
┌───────────────────┐
│  5. Deploy to Dev │  Automatic on merge to main
└──────┬────────────┘
       ▼
┌───────────────────┐
│  6. Integration   │  Integration tests run against dev environment
│     Tests         │
└──────┬────────────┘
       ▼
┌───────────────────┐
│  7. Promote to    │  Manual approval gate
│     Staging       │
└──────┬────────────┘
       ▼
┌───────────────────┐
│  8. E2E Tests     │  End-to-end tests run against staging
└──────┬────────────┘
       ▼
┌───────────────────┐
│  9. Promote to    │  Manual approval gate + release tag
│     Prod          │
└───────────────────┘
```

### Pipeline Rules

- **Stages 1-4 run on every push** — PRs cannot merge unless all four pass.
- **Stage 5 is automatic** — every merge to `main` deploys to dev. Dev can break. That's what it's for.
- **Stages 7 and 9 require manual approval** — a human decides when to promote. The pipeline provides confidence; the human provides judgment.
- **Every image is tagged with its commit SHA** — you always know exactly what code is running in each environment.
- **Infrastructure changes go through the same pipeline** — Terraform plans run on PR, apply runs on merge. No manual resource creation.
- **The pipeline definition lives in the repo** — `.github/workflows/`, `cloudbuild.yaml`, or equivalent. Pipeline-as-code, versioned and reviewed like application code.

### Container Build

- Every service has a Dockerfile in the repo root or service directory.
- Images are tagged with the git commit SHA: `<registry>/<service>:<sha>`. No `latest` tags in any environment.
- Images are pushed to the project's container registry (GCR, ECR, or Artifact Registry).
- Base images are pinned to specific versions. Do not use `FROM python:3` — use `FROM python:3.12-slim`.
- Container vulnerability scanning runs before the image is pushed. Critical vulnerabilities block the build.

## Environment Strategy

### Environments

Every project requires at minimum three environments: **dev**, **staging**, and **prod**. All provisioned through Terraform.

| Environment | Purpose | Deploys | Approval |
|---|---|---|---|
| **Dev** | Active development and integration. Can break. | Automatic on merge to `main` | None |
| **Staging** | Final gate before production. Mirrors prod in configuration and scale. | Manual promotion from dev | Team lead |
| **Prod** | Production. Deployments are deliberate, reviewed, and reversible. | Manual promotion from staging | Team lead + on-call |

### Environment Parity

- Environment parity is not optional. If staging uses a different database engine, or skips a sidecar that exists in prod, it is not staging — it is a lie that will betray you during cutover.
- All environments share the same Terraform modules with environment-specific variable files. The infrastructure code is identical; the configuration differs.
- Environment-specific configuration (endpoints, credentials, feature flags) is managed through environment variables or config maps — never through conditional logic in application code.

### Promotion Flow

- Code flows forward only: dev → staging → prod. You do not deploy to staging from a branch. You do not skip environments.
- Each promotion is a specific image SHA moving to the next environment. The image does not get rebuilt — the same artifact that passed integration tests in dev is the artifact that runs in staging and prod.
- Rollback is redeploying the previous known-good image SHA. It is not reverting commits.
- After a promotion to prod, there is a bake period (minimum 30 minutes, longer for critical services) before the release is considered stable. During the bake period, the previous image stays ready for immediate rollback.

## Service Bootstrap

When creating a new service or component, it ships with these from day one — not as follow-up work:

### Required from First PR

- [ ] `Dockerfile` — production container image, pinned base image, non-root user
- [ ] CI/CD pipeline definition — lint, test, build, scan stages
- [ ] Terraform module — infrastructure definition for all three environments
- [ ] `/health` endpoint — verifies dependencies, returns 503 if unhealthy
- [ ] `/ops/*` endpoints — full diagnostic and remediation contract (see Observability below)
- [ ] OpenAPI spec — API contract checked into the repo
- [ ] OpenAPI response models — every endpoint (GET, POST, PUT, DELETE) must declare a typed Pydantic `response_model`. No bare `dict` returns.
- [ ] OpenAPI examples — every request body model and response model must include `json_schema_extra` with realistic `examples` so Swagger UI shows typed schemas and pre-filled "Try it out" payloads
- [ ] Unit and API test scaffolding — tests run from day one, not added later
- [ ] `.env.example` — documented environment variables for local development
- [ ] OTEL instrumentation — metrics (Golden Signals), traces (request spans), and log bridge configured with OTLP exporter
- [ ] `README.md` — how to run locally, how to test, how to deploy

### Required Before Production

- [ ] Integration tests running in the CI pipeline against dev
- [ ] E2E tests running in the CI pipeline against staging
- [ ] SLOs defined and error budgets configured
- [ ] Monitoring dashboards for Golden Signals
- [ ] PagerDuty alerting configured and routed
- [ ] SRE agent config updated with the new service in the registry
- [ ] ADR documenting technology and architecture decisions

## Dependency Management

- Shared libraries, API clients, and proto definitions are versioned artifacts — not git submodules, not copy-pasted code.
- Internal libraries are published to a private package registry (npm, PyPI, Maven, or equivalent) with semantic versioning. Consumers pin to a version range.
- When a shared library changes, consumers are not force-upgraded. The library maintains backward compatibility or publishes a major version bump. Consumers upgrade on their own timeline.
- API contracts between services are documented as OpenAPI specs. Breaking changes require a version bump and a migration plan, not a Slack message.
- Third-party dependencies are pinned to exact versions in lock files. Dependabot or equivalent runs weekly. Security patches are merged within 48 hours; feature upgrades are batched monthly.

## Observability

- Follow Google SRE best practices. Every service instruments the four **Golden Signals**: latency, traffic, errors, saturation.
- Request-driven services also apply the **RED method**: rate, errors, duration (p50/p95/p99 — not averages).
- Every production service has defined SLOs with error budgets. When the error budget is exhausted, reliability work takes priority over features.
- Structured logs only. Health checks are mandatory.
- Every service must answer **"is this service healthy?"** via `/ops/status` — a composite rollup of Golden Signals, RED metrics, SLO burn rate, and dependency health into a single verdict: **healthy**, **degraded**, or **unhealthy**. The service owns this computation, not an external aggregator.
- SRE agent `/ops/*` endpoints are part of the definition of done for every service. A service without them is not shippable. Build them alongside your feature endpoints, not after.
  - **Diagnostics** (build with every service): `/ops/status`, `/ops/health`, `/ops/metrics`, `/ops/config`, `/ops/dependencies`, `/ops/errors`
  - **Remediation** (build with every service): `/ops/drain`, `/ops/cache/flush`, `/ops/circuits`, `/ops/loglevel`, `/ops/scale` (for services with application-managed scaling)
  - All remediation endpoints must be idempotent and non-destructive. See `WINDSURF.md` for full spec.
  - **These endpoints are the contract with the SRE agent.** The SRE agent calls them to diagnose and remediate incidents. If `/ops/*` endpoints are down, the agent cannot operate. Treat `/ops/*` availability with the same priority as the main API — they should not be behind feature flags, separate deployments, or optional middleware that could fail independently.
- **Logging:** *[Logging framework and format — e.g., "Structured JSON to stdout via Python `logging`"]*
- **Metrics and tracing:** *[Metrics and tracing setup — e.g., "OpenTelemetry SDK with OTLP exporter to Cloud Trace"]*

## Terraform Workflow

- Infrastructure is code. Every resource exists in Terraform. No hand-created resources in any environment.
- Terraform code lives in the repo, either in a top-level `terraform/` directory or in per-service `infra/` directories.
- **On PR:** `terraform plan` runs and the output is posted as a PR comment. Reviewers see exactly what will change before approving.
- **On merge to main:** `terraform apply` runs against the dev environment automatically.
- **On promotion:** `terraform apply` runs against staging or prod with the same modules and environment-specific variables.
- State is stored remotely (GCS bucket or S3 bucket) with locking. Local state files are never committed.
- Sensitive values are never in `.tfvars` files in the repo. They come from the secrets manager or are set in the CI environment.
- Terraform modules are versioned. When a module changes, environments are updated through the normal promotion flow — not by running `terraform apply` from a laptop.

## Task Scope Rules

- Do not modify files outside the scope of your assigned task.
- Bugs and improvements found during work get filed as GitHub issues — do not fix them inline.
- All code work is driven through GitHub issues. No ad-hoc work without an issue.
- All prompting commands and outcomes are logged in `prompting.md`.
- Do not install new dependencies without explicit approval.
- When in doubt, ask before building.
