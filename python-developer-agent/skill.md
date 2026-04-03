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

- **Project structure**: Layers, key directories, service boundaries
- **Data flow**: Entry points → transformations → outputs
- **Service boundaries**: Component communication patterns
- **Infrastructure layout**: Service deployment topology
- **API design**: 
  - Endpoint organization
  - Versioning
  - OpenAPI spec location
- **API-first principle**: All functionality exposed and testable through APIs. UI consumes API — does not replace it.

## Development Environment

- **Install command**: `pip install -r requirements.txt`
- **Local services**: `docker compose up -d` to start database and cache
- **Database setup**: `alembic upgrade head` to apply migrations
- **Seed data**: `python seed.py` to populate reference data
- **Test command**: `pytest`
- **Lint command**: `pylint --disable=import-error --fail-under=10.0 app tests`
- **Run command**: `uvicorn app.main:app --host :: --port 8000 --reload`
- **Verify command**: `curl http://localhost:8000/health`
- **`act` is required for local CI pipeline verification.** 
  - Install via `brew install act` (macOS) or see [nektos/act](https://github.com/nektos/act)
  - The `.actrc` file in the repo root configures the runner image and env-file
  - Run individual CI jobs with `act -j <job-name> --env-file env.list` before pushing
  - All CI jobs must exit 0 — this is a merge-blocking quality gate

### Local Dev Parity

- **Local environment mirrors production**: Services running in containers in prod run in containers locally
- **Docker Compose for multi-service development**: Every service, database, cache, and queue from prod has a local equivalent
- **Application code location**: `app/` at repo root — no `src/` directory. Package `app/` directly importable without PYTHONPATH manipulation. `Dockerfile` copies `./app` to `/app/` for identical import behavior across environments
- **Python import pattern**: Use `from app.module import ...`. `entrypoint.sh` uses `uvicorn app.main:app`
- **Container dependencies must be pinned for reproducible builds.** 
  - The `Dockerfile` must install from a `requirements.lock.txt` file (or equivalent) that contains exact package versions, not from `requirements.txt` which may have version ranges
  - Use `pip install --no-cache-dir -r requirements.lock.txt` to ensure identical dependency resolution across builds and environments
  - Generate the lock file using `pip-tools compile` or equivalent
- **Dependency locking script must be executed and its output must be captured.** 
  - The `scripts/lock.sh` script must be executable (`chmod +x scripts/lock.sh`) and must be run after any modification to `pyproject.toml` or dependency changes
  - The QA agent must actually execute `bash scripts/lock.sh`, capture the full terminal output, and include it in `TEST_RESULTS.md`
  - Do not infer the script was run from the presence of pip-compile headers or file timestamps — the actual execution output is required evidence
  - Run the script twice and compare `md5`/`md5sum` hashes of `requirements.txt` and `requirements-dev.txt` between runs to prove idempotent behavior
  - Both runs and both hash comparisons must appear in the report
- **`pip-compile` must use `--allow-unsafe` on both production and dev lock files.** 
  - Without this flag, pip-compile excludes `setuptools`, `pip`, and `wheel` from the lock file
  - When the lock file is installed with `--require-hashes` (the default when any hash is present), pip fails because these transitive dependencies have no pinned hash
  - Both `pip-compile` invocations in `scripts/lock.sh` must include `--allow-unsafe`
- **Shell scripts and hooks must be committed with executable permissions.** 
  - IDE file-creation tools (e.g., Windsurf `write_to_file`, Copilot) create files as `100644` (non-executable)
  - All `.sh` files and `hooks/*` files must be made executable before commit: `chmod +x <file>` followed by `git update-index --chmod=+x <file>`
  - Verify with `git ls-files -s <file>` — the mode must be `100755`, not `100644`
  - This applies to: `scripts/entrypoint.sh`, `scripts/environment-check.sh`, `scripts/lock.sh`, `hooks/pre-commit`, and any other shell scripts or hook files in the repo
- **Pylint must be configured for CI environments.** 
  - Configure pylint in `pyproject.toml` with `--disable=import-error` for local modules that aren't installable in CI (e.g., kafka, rds modules)
  - Use `--fail-under=10.0` to require a perfect score with no errors, warnings, or conventions issues
  - Ensure all production dependencies are installed before running pylint in CI — install both production and dev requirements: `pip install -r requirements.txt -r requirements-dev.txt`
- Seed data scripts are checked into the repo and run as part of local setup. A developer should go from clone to working stack with a single command.
- Environment variables for local development are documented in a `.env.example` file. Never commit `.env` files with real values.
- If a dependency cannot run locally (e.g., a managed cloud service), provide a mock or stub with documented behavioral differences.

## Coding Practices

- Write code the next engineer can understand without asking you. Refactor first, comment second.
- You do not overengineer for the sake of engineering, simplicity is key.
- You do not over abstract for the sake of abstraction, simplicity is key.
- You do not invent patterns or solutions that don't exist in the codebase or are not aligned with the existing patterns.
- **The CI pipeline is immutable.** 
  - Never add, remove, rename, or modify jobs in `.github/workflows/ci.yml` (or any workflow file)
  - The CI jobs are defined by the repo owner and validated by the QA agent
  - If a quality gate is not in CI, it is not your job to add it
  - If a CI job fails, fix the application code or configuration that the job tests — never fix the job definition
  - The only exception is if the human operator explicitly asks you to modify CI
  - This rule applies to all workflow files, not just the CI pipeline
- **Workspace isolation.** 
  - During a rebuild, read only from the legacy repo (`repo/`), the template repo (`template/`), and adjacent repos (`adjacent/`) listed in scope.md
  - Never read from, reference, or import code from any other `rebuilder-*` repository in the workspace
  - Other rebuilder repos may be partially built, stale, or from a different project
  - The destination directory is wiped clean before every run — do not assume prior state exists
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
- **Never access protected members (`_name`) from outside the owning class.** 
  - If a test or another class needs to read or call a private member, either make it public (remove the underscore) or add a public accessor method
  - Do not use `# pylint: disable=protected-access` — fix the design instead
  - When mocking external modules in tests, only mock the public API the app actually calls; do not create mock attributes for private members the app doesn't use
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

- Remove outdated code (DP2.5, Stackdriver, vendor-specific monitoring clients)
- Do not include SRE Agent configuration for library repos — only for deployable services
- DAPR runs as sidecar only — no DAPR client libraries in application code

## Required Development Tooling

The required development tools, configurations, Dockerfile pattern, entrypoint/environment-check scripts, Helm chart templates, CI pipeline structure, coding practices, and all supporting files for this project are defined by the template repo cloned to `template/` (see `config.md` for details). **Read `template/skill.md` and complete every checkbox.** That file is the authoritative punch list — not the README. The template repo is not an adjacent repo — it is the build standard.

Those tools are the only quality gates for this project. Do not add, skip, replace, or weaken any tool the template repo specifies. If a tool reports errors, fix the code — do not disable the rule, suppress the warning, or remove the tool from the pipeline.

Every tool specified by the template repo must pass cleanly before any commit is pushed. "It works" is not sufficient — it must also pass the full toolchain. If you are building a new service or modifying an existing one, the CI pipeline must enforce all of them. Do not ship a CI pipeline that omits any of them.

## Testing

- **Tests are mandatory**: Every bug fix gets a regression test
- **Health check documentation**: Always describe how health checks work and why decisions were made
- **Behavior-focused tests**: Write tests that verify behavior, not implementation
- **Test levels**:
  - **Unit tests**: Gate every commit
  - **API tests**: Validate every endpoint directly (request in, response out)
  - **Integration tests**: Verify components work together
  - **Contract tests**: Ensure API responses match OpenAPI spec
  - **E2E tests**: Validate critical workflows
- **Test fixtures use domain-realistic values.** 
  - Real-looking MAC addresses, model names, firmware versions, serial numbers, timestamps — not generic placeholders like `test-1`, `foo`, or `user_abc`
  - Tests should read like documentation of how the system actually behaves with production-like data
  - This catches edge cases (case sensitivity, format validation, character encoding) that synthetic data misses
- Run the full test suite locally before pushing. Do not merge with failing tests.
- **All static analysis, linting, and formatting tools must run against both `app/` and `tests/` directories.** 
  - Never limit tooling to only application code
  - Tests must meet the same quality standards as production code
  - Configure tools in `pyproject.toml` to include both directories: `pylint --disable=import-error --fail-under=10.0 app tests`, `black --check app tests --skip-string-normalization`, `mypy app/ --ignore-missing-imports`, etc.
- **`pytest.ini` must exclude non-application test directories.** 
  - Every rebuilt repo contains `sre-agent/runtime/tests/` and `python-qa-agent/examples/` which have their own dependencies and are not part of the application test suite
  - Add them to `norecursedirs` so pytest does not collect them:
  ```ini
  norecursedirs = .git .venv sre-agent python-qa-agent python-developer-agent
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

- **Branch naming**: `feature/<short-description>` or `fix/<short-description>`
- **Never commit directly to `main`.**
- **Rebase on `main` before opening a PR.**

### Pre-Commit Checklist

Run before every commit:

1. **Branch check**: On feature/fix branch (not `main`)
2. **Tests pass**: Full test suite passes
3. **Lint/type check clean**: Zero errors
4. **Commit message**: Detailed message with summary + structured body (use `git commit -F`)
5. **Diff review**: Check for unintended changes, debug code, print statements

### Commit Messages

- **Format**: One-line summary + structured body
- **Summary**: Short imperative sentence (e.g., `fix: resolve Redis connection leak on shutdown`)
- **Body**: Categories with bullet points explaining what changed and why
- **Categories**: `Documentation:`, `Production readiness:`, `Bug fixes:`, `Features:`, `Refactoring:`, `Tests:`
- **Squash**: Logical commits before PR

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

- **Title**: One-line summary
- **Body**: What changed, why, how to test
- **Size**: Small and focused PRs
- **Tests**: All tests pass before creating PR
- **API changes**: Call out explicitly in description

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

- **Stages 1-4**: Run on every push — PRs cannot merge unless all pass
- **Stage 5**: Automatic on merge to `main` — dev can break
- **Stages 7 and 9**: Manual approval required
- **Image tagging**: Every image tagged with commit SHA
- **Registry**: Project's container registry (GCR, ECR, or Artifact Registry)
- **Base images**: Pinned to specific versions (e.g., `FROM python:3.12-slim`)
- **Security**: Container vulnerability scanning before push — critical vulnerabilities block build

## Environment Strategy

### Environments

Every project requires at minimum three environments: **dev**, **staging**, and **prod**. All provisioned through Terraform.

| Environment | Purpose | Deploys | Approval |
|---|---|---|---|
| **Dev** | Active development and integration. Can break. | Automatic on merge to `main` | None |
| **Staging** | Final gate before production. Mirrors prod in configuration and scale. | Manual promotion from dev | Team lead |
| **Prod** | Production. Deployments are deliberate, reviewed, and reversible. | Manual promotion from staging | Team lead + on-call |

### Environment Parity

- **Parity required**: Staging must mirror prod in configuration, scale, and data shape
- **Infrastructure code**: Identical Terraform modules with environment-specific variables
- **Configuration management**: Environment variables or config maps — no conditional logic in code

### Promotion Flow

- **Forward only**: dev → staging → prod — no deploying to staging from branch, no skipping environments
- **Artifact promotion**: Same image SHA moves to next environment — no rebuilding
- **Rollback**: Redeploy previous known-good image SHA — not reverting commits
- **Bake period**: Minimum 30 minutes after prod promotion before considering stable

## Service Bootstrap

When creating a new service or component, it ships with these from day one — not as follow-up work:

### Required from First PR

- [ ] `Dockerfile` — production container image, pinned base image, non-root user
- [ ] CI/CD pipeline definition — lint, test, build, scan stages
- [ ] Terraform module — infrastructure definition for all three environments
- [ ] `/health` endpoint — verifies dependencies, returns 503 if unhealthy
- [ ] `/ops/*` endpoints — full diagnostic and remediation contract
- [ ] `/ops/health/<component>` endpoints — individual health check per external dependency
- [ ] Component data viewer endpoints — diagnostic read endpoints for data-bearing components
- [ ] OpenAPI spec — API contract checked into repo
- [ ] OpenAPI response models — every endpoint declares typed Pydantic `response_model`
- [ ] OpenAPI examples — request/response models include `json_schema_extra` with realistic examples
- [ ] OpenAPI query parameter examples — every `Query()` parameter includes `example=` with realistic value
- [ ] Unit and API test scaffolding — tests run from day one
- [ ] `.env.example` — documented environment variables for local development
- [ ] OTEL instrumentation — metrics (Golden Signals), traces (request spans), log bridge configured
- [ ] `README.md` — how to run locally, test, deploy

### Required Before Production

- [ ] Integration tests running in CI pipeline against dev
- [ ] E2E tests running in CI pipeline against staging
- [ ] SLOs defined and error budgets configured
- [ ] Monitoring dashboards for Golden Signals
- [ ] PagerDuty alerting configured and routed
- [ ] SRE agent config updated with new service in registry
- [ ] ADR documenting technology and architecture decisions

## Dependency Management

- **Shared libraries**: Versioned artifacts — not git submodules or copy-pasted code
- **Internal libraries**: Published to private package registry with semantic versioning
- **API contracts**: Documented as OpenAPI specs — breaking changes require version bump and migration plan
- **Third-party dependencies**: Pinned to exact versions in lock files
- **Dependabot**: Runs weekly — security patches merged within 48 hours, feature upgrades monthly

## Observability

- **Golden Signals**: Every service instruments latency, traffic, errors, saturation
- **RED Method**: Request-driven services also track rate, errors, duration (p50/p95/p99)
- **SLOs**: Defined with error budgets — when exhausted, reliability work takes priority
- **Structured logs**: Health checks mandatory
- **Composite health**: `/ops/status` provides single verdict (healthy/degraded/unhealthy) based on Golden Signals, RED metrics, SLO burn rate, and dependency health
- **SRE agent endpoints**: Part of definition of done — build alongside feature endpoints
### SRE Agent Endpoints

**Diagnostics** (build with every service):
- `/ops/status`, `/ops/health` (includes dependency health with latency), `/ops/metrics`, `/ops/config`, `/ops/cache`, `/ops/errors`

**Remediation** (build with every service):
- `/ops/cache/flush`, `/ops/cache/refresh`, `/ops/circuits`, `/ops/loglevel`, `/ops/log-level`

**Requirements**:
- All remediation endpoints are idempotent and non-destructive
- These endpoints are the contract with the SRE agent — treat availability with same priority as main API
- Do not place behind feature flags, separate deployments, or optional middleware
### Individual Component Health Endpoints

- Build one per external dependency (database, message queue, cache, object store, external API)
- Location: `/ops/health/<component>` (e.g., `/ops/health/rds`, `/ops/health/kafka`, `/ops/health/redis`, `/ops/health/s3`)
- Response: Typed `ComponentHealthResponse` with `component`, `status`, `latency_ms`, `error`, `details`
- Tag with `tags=["components"]` for Swagger grouping
### Component Data Viewer Endpoints

Build one per data-bearing component — diagnostic read endpoints for end-to-end data flow verification:

**Message queues**:
- `/ops/kafka/messages?topic=<alias>&count=10` — read recent messages using short-lived consumer
- Use unique ephemeral `group.id` per request to avoid interfering with production consumers

**Caches**:
- `/ops/blacklist`, `/ops/cache/entries` — view actual cached data (IDs, keys, values)

**Databases**:
- `/ops/rds/query` or similar read-only diagnostic queries if appropriate

**Requirements**:
- Endpoints must not modify state
- Import consumer libraries lazily (inside endpoint function) if not otherwise needed at module scope
### Typed Response Models

- Every ops endpoint must declare a Pydantic `response_model` so Swagger renders full response schema
- Do not return bare `JSONResponse` without a model — Swagger will show empty `200: Successful Response` with no schema
- **Logging:** *[Logging framework and format — e.g., "Structured JSON to stdout via Python `logging`"]*
- **Metrics and tracing:** *[Metrics and tracing setup — e.g., "OpenTelemetry SDK with OTLP exporter to Cloud Trace"]*

## Terraform Workflow

- **Infrastructure as code**: Every resource exists in Terraform — no hand-created resources
- **Code location**: In repo — top-level `terraform/` or per-service `infra/` directories
- **PR process**: `terraform plan` runs and output posted as PR comment
- **Merge process**: `terraform apply` runs against dev environment automatically
- **Promotion**: `terraform apply` runs against staging/prod with same modules and environment-specific variables
- **State storage**: Remote (GCS bucket or S3 bucket) with locking — local state never committed
- **Secrets**: Never in `.tfvars` files — come from secrets manager or CI environment
- **Modules**: Versioned — environments updated through normal promotion flow

## Task Scope Rules

- Do not modify files outside assigned task scope
- Bugs/improvements found during work → file as GitHub issues — do not fix inline
- All code work driven through GitHub issues — no ad-hoc work without issue
- All prompting commands/outcomes logged in `prompting.md`
- Do not install new dependencies without explicit approval
- When in doubt about scope, ask before building
