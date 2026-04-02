# Project: [project-name]

> Daily development instructions. Loaded via IDE instruction files at the project root.
> `.windsurfrules` (Windsurf), `.github/copilot-instructions.md` (VS Code + Copilot), or `AGENTS.md` (other tools)
> instruct the AI assistant to read this file and `config.md` before any work.
> For migration planning, architecture decisions, data migration, and cutover guidance, see `STANDARDS.md`.
> For SRE agent configuration and incident response, see `sre-agent/skill.md`.

## Agent Role

**You are the staff level developer on this project.** When you load this file, every standard in it becomes your operating procedure — not a reference document, not a style guide, but the rules you follow by default.

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
- *[Lint command — e.g., `pylint --disable=import-error --fail-under=10.0 app tests`]*
- *[Run command — e.g., `uvicorn app.main:app --host :: --port 8000 --reload`]*
- *[Verify command — e.g., `curl http://localhost:8000/health`]*

### Local Dev Parity

- The local development environment must be representative of production. If a service runs in a container in prod, it runs in a container locally.
- Use Docker Compose or equivalent for local multi-service development. Every service, database, cache, and queue that exists in prod has a local equivalent.
- **Application code lives at `app/` in the repo root.** There is no `src/` directory. The package `app/` is directly importable without PYTHONPATH manipulation. The `Dockerfile` copies `./app` to `/app/` in the container. This ensures identical import behavior in local dev, CI, and the container — no PYTHONPATH hacks required.
- **Python imports must use `app.*`.** All source code imports must use `from app.module import ...`. The `entrypoint.sh` must use `uvicorn app.main:app`. Since `app/` is at the repo root, `app.*` imports resolve directly in all environments.
- **Container dependencies must be pinned for reproducible builds.** The `Dockerfile` must install from a `requirements.lock.txt` file (or equivalent) that contains exact package versions, not from `requirements.txt` which may have version ranges. Use `pip install --no-cache-dir -r requirements.lock.txt` to ensure identical dependency resolution across builds and environments. Generate the lock file using `pip-tools compile` or equivalent.
- **Dependency locking script must be executed and its output must be captured.** The `scripts/lock.sh` script must be executable (`chmod +x scripts/lock.sh`) and must be run after any modification to `pyproject.toml` or dependency changes. The QA agent must actually execute `bash scripts/lock.sh`, capture the full terminal output, and include it in `TEST_RESULTS.md`. Do not infer the script was run from the presence of pip-compile headers or file timestamps — the actual execution output is required evidence. Run the script twice and compare `md5`/`md5sum` hashes of `requirements.txt` and `requirements-dev.txt` between runs to prove idempotent behavior. Both runs and both hash comparisons must appear in the report.
- **Shell scripts and hooks must be committed with executable permissions.** IDE file-creation tools (e.g., Windsurf `write_to_file`, Copilot) create files as `100644` (non-executable). All `.sh` files and `hooks/*` files must be made executable before commit: `chmod +x <file>` followed by `git update-index --chmod=+x <file>`. Verify with `git ls-files -s <file>` — the mode must be `100755`, not `100644`. This applies to: `scripts/entrypoint.sh`, `scripts/environment-check.sh`, `scripts/lock.sh`, `hooks/pre-commit`, and any other shell scripts or hook files in the repo.
- **Pylint must be configured for CI environments.** Configure pylint in `pyproject.toml` with `--disable=import-error` for local modules that aren't installable in CI (e.g., kafka, rds modules). Use `--fail-under=10.0` to require a perfect score with no errors, warnings, or conventions issues. Ensure all production dependencies are installed before running pylint in CI — install both production and dev requirements: `pip install -r requirements.txt -r requirements-dev.txt`.
- Seed data scripts are checked into the repo and run as part of local setup. A developer should go from clone to working stack with a single command.
- Environment variables for local development are documented in a `.env.example` file. Never commit `.env` files with real values.
- If a dependency cannot run locally (e.g., a managed cloud service), provide a mock or stub with documented behavioral differences.

## Coding Practices

- Write code the next engineer can understand without asking you. Refactor first, comment second.
- You do not overengineer for the sake of engineering, simplicity is key.
- You do not over abstract for the sake of abstraction, simplicity is key.
- You do not invent patterns or solutions that don't exist in the codebase or are not aligned with the existing patterns.
- Fail fast and fail loud. Do not swallow errors, return empty defaults, or log and continue.
- You do not create or allow dead code. No commented-out blocks. If it's not running in production, delete it.
- All imports go at the top of the file — never inline inside functions. There are no exceptions and no justifications. If an import inside a function is the only way to avoid an error, the design is wrong; fix the dependency structure. The standard resolution for circular imports caused by shared state (e.g., `LOGGER`, `meter`, OTEL providers) is to extract that state into a dedicated `core.py` module that no other app module imports back from. External modules (`kafka_module`, `rds_module`) must also be imported at the top level — `conftest.py` `sys.modules` mocks ensure they resolve during tests. Do not disable pylint C0415 (`import-outside-toplevel`).
- Follow PEP 8 import ordering. Group imports in this order, separated by a blank line: (1) standard library, (2) third-party packages, (3) local application/library imports.
- You do not introduce circular imports. If adding an import creates a cycle, refactor — extract the shared code into a separate module (e.g., `core.py`) or restructure the call chain. Do not solve circular imports by moving imports inline.
- Functions do one thing. Prefer explicit over implicit.
- Avoid module-level mutable global variables. Pass state through function arguments, class instances, or dependency injection. Read-only module constants (e.g., `LOGGER`, `DEFAULT_TIMEOUT`) are fine.
- Do not shadow global variables or constants inside function calls — use distinct local names.
- All constants must be UPPER_CASE (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`).
- All functions, classes, and modules must have docstrings.
- Use f-strings instead of `%` formatting or `.format()` where appropriate.
- Resolve linter errors instead of ignoring them — avoid `# pylint: disable`, `# type: ignore`, and similar suppression comments wherever possible.
- No `# type: ignore[arg-type]` or `# type: ignore` comments anywhere — fix the type mismatch instead of suppressing it. Remove any that become unused.
- Match expected types exactly — if a function expects `bytes`, pass `bytes` (e.g., `.encode()`), not `str`. Do not rely on implicit conversions.
- Verify argument types against function signatures before calling — check the type hints of every function you call (standard library, third-party, and internal). If a parameter is typed as `bytes`, `int`, `Optional[str]`, etc., the caller must pass exactly that type.
- When integrating with external modules (kafka_module, rds_module, etc.), read the module's type hints or docstrings to confirm expected parameter types. A producer that expects `bytes` must receive `.encode("utf-8")`, not a raw `str`.
- Do not write equality checks that can never be true — if mypy reports `comparison-overlap`, the types on both sides of `==` are incompatible. Narrow the type first with `isinstance()` or restructure the logic.
- Match framework function signatures exactly — e.g., FastAPI's `lifespan` parameter expects `Callable[[FastAPI], AsyncContextManager]`, not `Callable[[], AsyncContextManager]`. Check the framework type stubs when wiring callbacks.
- Always parameterize generic types — use `dict[str, int]`, `list[EventRecord]`, `Optional[dict[str, bytes]]`, etc. with specific, meaningful types. Never use bare `dict` or `list` in type annotations. Avoid `Any` — use the actual expected type instead.
- Run `mypy` as a type-mismatch safety net before every commit. Treat every mypy error as a real bug — not a false positive to suppress.
- **Never access protected members (`_name`) from outside the owning class.** If a test or another class needs to read or call a private member, either make it public (remove the underscore) or add a public accessor method. Do not use `# pylint: disable=protected-access` — fix the design instead. When mocking external modules in tests, only mock the public API the app actually calls; do not create mock attributes for private members the app doesn't use.
- Always specify encoding when calling `open()`: `open(path, encoding="utf-8")`. Never rely on the platform default.
- Handle errors at the boundary where you can act on them. Every error message answers: what happened, what was expected, what to do about it.
- Distinguish retryable from fatal errors.
- Never commit secrets, tokens, or credentials. Use your cloud provider's native secrets manager (GCP Secret Manager or AWS Secrets Manager). No exceptions.
- Validate all external input. Trust nothing that crosses a boundary.
- Least privilege everywhere — database users, API keys, IAM roles, file permissions.
- Pin dependency versions. Audit regularly. Remove what you don't use.
- Measure before you optimize. N+1 queries and missing indexes are bugs, not performance tuning.
- Set timeouts on every external call.

### Standing Orders

These rules apply to every task, every commit, every session. They are not situational.

- Remove outdated code (DP2.5, Stackdriver, vendor-specific monitoring clients). If it is not used in the target architecture, delete it.
- Do not include SRE Agent configuration for library repos — only for deployable services.
- DAPR runs as a sidecar only. Do not add DAPR client libraries to application code. Document which DAPR components are in use and their binding types.

## Required Development Tooling

The required development tools, configurations, Dockerfile pattern, entrypoint/environment-check scripts, Helm chart templates, CI pipeline structure, coding practices, and all supporting files for this project are defined by the template repo cloned to `template/` (see `config.md` for details). **Read `template/skill.md` and complete every checkbox.** That file is the authoritative punch list — not the README. The template repo is not an adjacent repo — it is the build standard.

Those tools are the only quality gates for this project. Do not add, skip, replace, or weaken any tool the template repo specifies. If a tool reports errors, fix the code — do not disable the rule, suppress the warning, or remove the tool from the pipeline.

Every tool specified by the template repo must pass cleanly before any commit is pushed. "It works" is not sufficient — it must also pass the full toolchain. If you are building a new service or modifying an existing one, the CI pipeline must enforce all of them. Do not ship a CI pipeline that omits any of them.

## Testing

- Tests are not optional. Every bug fix gets a regression test.
- You always describe how health checks are working and why you made certain decisions.
- Write tests that verify behavior, not implementation.
- **Unit tests** gate every commit. **API tests** validate every endpoint directly — request in, response out. **Integration tests** verify components work together. **Contract tests** ensure API responses match the OpenAPI spec. **E2E tests** validate critical workflows.
- **Test fixtures use domain-realistic values.** Real-looking MAC addresses, model names, firmware versions, serial numbers, timestamps — not generic placeholders like `test-1`, `foo`, or `user_abc`. Tests should read like documentation of how the system actually behaves with production-like data. This catches edge cases (case sensitivity, format validation, character encoding) that synthetic data misses.
- Run the full test suite locally before pushing. Do not merge with failing tests.
- **All static analysis, linting, and formatting tools must run against both `app/` and `tests/` directories.** Never limit tooling to only application code. Tests must meet the same quality standards as production code. Configure tools in `pyproject.toml` to include both directories: `pylint --disable=import-error --fail-under=10.0 app tests`, `black --check app tests --skip-string-normalization`, `mypy app/ --ignore-missing-imports`, etc.
- **`pytest.ini` must exclude non-application test directories.** Every rebuilt repo contains `sre-agent/runtime/tests/` and `python-qa-agent/examples/` which have their own dependencies and are not part of the application test suite. Add them to `norecursedirs` so pytest does not collect them:
  ```ini
  norecursedirs = .git .venv sre-agent python-qa-agent
  ```

## Code Audit Checklist

Before considering a service implementation complete, verify every item below. Run through each item and confirm it passes. If any item fails, stop and fix it before proceeding — do not defer these to a follow-up PR. These are the issues that pass quality gates but cause production incidents.

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
- [ ] `/ops/health/<component>` endpoints — individual health check per external dependency (see Observability → Individual component health endpoints)
- [ ] Component data viewer endpoints — diagnostic read endpoints for every data-bearing component (see Observability → Component data viewer endpoints)
- [ ] OpenAPI spec — API contract checked into the repo
- [ ] OpenAPI response models — every endpoint (GET, POST, PUT, DELETE) must declare a typed Pydantic `response_model`. No bare `dict` returns. This includes all `/ops/*` endpoints.
- [ ] OpenAPI examples — every request body model and response model must include `json_schema_extra` with realistic `examples` so Swagger UI shows typed schemas and pre-filled "Try it out" payloads. Request body examples must use valid test data (e.g., correct HMAC hashes for the local dev salt) so "Try it out" works without manual editing.
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
  - **Diagnostics** (build with every service): `/ops/status`, `/ops/health` (includes dependency health with latency), `/ops/metrics`, `/ops/config`, `/ops/cache`, `/ops/errors`
  - **Remediation** (build with every service): `/ops/cache/flush`, `/ops/cache/refresh`, `/ops/circuits`, `/ops/loglevel`, `/ops/log-level`
  - All remediation endpoints must be idempotent and non-destructive. See `STANDARDS.md` for full spec.
  - **These endpoints are the contract with the SRE agent.** The SRE agent calls them to diagnose and remediate incidents. If `/ops/*` endpoints are down, the agent cannot operate. Treat `/ops/*` availability with the same priority as the main API — they should not be behind feature flags, separate deployments, or optional middleware that could fail independently.
  - **Individual component health endpoints** (build one per external dependency): every external component the service depends on (database, message queue, cache, object store, external API) must have its own health check endpoint at `/ops/health/<component>`. Each endpoint returns a typed `ComponentHealthResponse` with `component`, `status`, `latency_ms`, `error`, and `details` (connection info, config). Tag these endpoints with `tags=["components"]` so Swagger groups them visibly. Examples: `/ops/health/rds`, `/ops/health/kafka`, `/ops/health/redis`, `/ops/health/s3`.
  - **Component data viewer endpoints** (build one per data-bearing component): every component that stores, caches, or transports data the service writes must have a diagnostic read endpoint so developers and SRE can verify data flow end-to-end from Swagger. Examples:
    - Message queues: `/ops/kafka/messages?topic=<alias>&count=10` — read recent messages from a topic using a short-lived consumer. Use a unique ephemeral `group.id` per request to avoid interfering with production consumers.
    - Caches: `/ops/blacklist`, `/ops/cache/entries` — view the actual cached data (IDs, keys, values), not just cache metadata.
    - Databases: `/ops/rds/query` or similar read-only diagnostic queries if appropriate for the service.
    - These are diagnostic-only endpoints. They must not modify state. Imports for consumer libraries (e.g., `confluent_kafka.Consumer`) should be lazy (inside the endpoint function) if the library is not otherwise needed at module scope — this avoids import failures in test environments that mock the producer but don't install the full client library.
  - **Typed response models on all `/ops/*` endpoints.** Every ops endpoint must declare a Pydantic `response_model` so Swagger renders the full response schema with field descriptions. Do not return bare `JSONResponse` without a model — Swagger will show an empty `200: Successful Response` with no schema, making the endpoint invisible for validation.
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
