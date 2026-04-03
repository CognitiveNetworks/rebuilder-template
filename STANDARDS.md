# Project: [project-name]

## Architecture

## Architecture

- **Project structure**: Layers, key directories, service boundaries
- **Data flow**: Entry points → transformations → outputs
- **Service boundaries**: Component communication patterns
- **Infrastructure layout**: Service deployment topology
- **API design**: Endpoint organization, versioning, OpenAPI spec location
- **API-first principle**: All functionality exposed and testable through APIs. UI consumes API — does not replace it.

### API-First Design

- Every service exposes functionality through APIs. If not testable, validated, and operated through API call → not done
- No business logic hidden behind UIs, CLI tools, or cron jobs that cannot be triggered/verified via API
- All features built API-first. API designed, documented, and testable before frontend/consumer
- Every API endpoint testable in isolation — given request, returns predictable response
- Use OpenAPI/Swagger specs as source of truth. Spec written first, implementation follows, contract tests verify sync

### Designing for Scale

- **10x load assumption**: Architect as if handling 10x current load without rewrite — make choices that don't paint into corner
- **Stateless services**: Application processes hold nothing in memory between requests. Session data, caches, job state → external stores
- **Separate read/write paths early**: Even with same database, structure code to distinguish queries from commands → enables read replicas, caching, CQRS
- **API design from day one**: Pagination, filtering, rate limiting. Retrofitting after users depend on unbounded responses is painful/breaking
- **Async processing**: Queues for anything not needing synchronous response (email, notifications, report generation, webhooks, data enrichment)
- **Database schema decisions**: Hardest to reverse. Normalize properly, index deliberately, think about query patterns before tables
- **Operational hygiene**: Connection pooling, circuit breakers, backpressure — not premature optimization
- **Cache deliberately**: Know what/why/when expires. Stale cache bugs harder than slow queries
- **Horizontal scaling by default**: If architecture requires bigger box instead of more boxes → created scaling ceiling
- **Plan for failure at every boundary**: Services go down, networks partition, disks fill, certificates expire

### Technology Selection

- **Enterprise-grade technologies**: Build systems that run reliably at scale, not prototypes replaced in 6 months
- **Proven track record**: Every technology choice should have production experience at companies larger than ours
- **Databases**: PostgreSQL for relational workloads. Handles JSONB, full-text search, partitioning well enough → rarely need second database engine early
- **Document stores at scale**: Use managed offering with enterprise support — not hobby-tier project
- **Caching**: Redis with persistence and clustering, not Memcached. Provides data structures, pub/sub, durability
- **Container orchestration**: Kubernetes. Not Docker Compose in production, not hand-rolled systemd units
- **IaC**: Terraform. No exceptions. Infrastructure as code, versioned and reviewed like application code
- **Cloud provider**: Design for local portability with GCP or AWS. Choose based on team expertise, existing infrastructure, managed service availability. Document decision in ADR. Do not split single project across both providers without justification
- **Litmus test**: Enterprise support options? Managed offering on chosen cloud provider? Can hire engineers who know it? If any answer is no → justify exception in writing or pick something else

## Development Environment

- **Setup commands**:
  - `npm install` to bootstrap dependencies
  - `npm run test` to run tests
  - `npm run lint` to check style
- **Local stack**: How to run full stack locally — containers, env vars, seed data
- **Environment verification**: How to verify environment is working before writing code

## Coding Practices

### General Principles

- Write code next engineer can understand without asking → refactor first, comment second
- Fail fast and fail loud. Silent failures → production incidents waiting to happen
- No dead code. No commented-out blocks. No "just in case" abstractions
- Functions do one thing. `processAndValidateAndSave` → three functions
- Prefer explicit over implicit. Magic values, hidden side effects, implicit ordering → impossible to trace bugs

### Error Handling

- Handle errors at boundary where you can do something about them
- Do not catch exceptions just to re-throw or log them
- Every error message answers: what happened, what was expected, what operator should do
- Distinguish retryable vs fatal errors. Retrying permissions failure → waste. Crashing on transient network blip → fragile

### Security

- **Never commit secrets, tokens, or credentials. No exceptions.**
- **Secrets management**: Use cloud provider's native secrets manager — GCP Secret Manager or AWS Secrets Manager. All application secrets, API keys, database credentials, service account keys stored in secrets manager and injected at runtime — never baked into images, config files, or environment variable definitions. For workloads spanning multiple clouds or on-prem → HashiCorp Vault. Nothing else.
- **Input validation**: Validate and sanitize all external input — user input, API responses, webhook payloads, environment variables. Trust nothing that crosses boundary.
- **Least privilege**: Apply everywhere — database users, API keys, IAM roles, file permissions. If doesn't need write access → doesn't get write access.
- **Dependencies as attack surface**: Pin versions. Audit regularly. Remove what you don't use.

### Performance

- Measure before you optimize. Profiling data beats intuition every time
- N+1 queries, unbounded loops, missing indexes → bugs, not performance problems. Fix when found
- Set timeouts on every external call. Missing timeout → thread leak waiting for server that will never respond

## Testing & QA

### Testing Strategy

- **Tests are not optional**: Untested code is broken code that hasn't been caught yet
- **Behavior-focused tests**: Write tests that verify behavior, not implementation. If refactor breaks test but not feature → test was wrong
- **Regression tests**: Every bug fix gets one. If broke once, will break again

### Test Levels

- **Unit tests**: Fast, isolated, no network or database. Test business logic, transformations, edge cases. Run in seconds, gate every commit
- **API tests**: Every endpoint tested directly — request in, response out. Validate status codes, response shapes, error handling, auth, pagination, edge cases. Primary integration gate
- **Integration tests**: Verify components work together — API endpoints hit database, services call external APIs through mocked boundaries, migrations run cleanly
- **End-to-end tests**: Validate critical user workflows against running stack. Keep focused on happy paths and high-value failure modes. Flaky E2E tests → fix or delete, not skip
- **Contract tests**: Validate API responses match OpenAPI spec on every build. If spec and implementation diverge → build fails

### QA Expectations

- Run full test suite locally before pushing. CI is safety net, not first line of defense
- If cannot write automated test → document manual test procedure in PR
- Test failure = build failure. Do not merge with failing tests. Do not skip tests to unblock deploy
- Load and stress testing before major releases, not after first production incident

## Git Workflow

- **Git worktrees**: Use for parallel development. Each task gets own worktree and feature branch
- **Branch naming**: `feature/<short-description>` or `fix/<short-description>`
- **Never commit directly to `main`.**
- **Commit messages**: Clear, concise, explain why not what. Diff shows what changed
- **Squash related changes**: Into logical commits before PR. One commit per logical change — not per save
- **Rebase on `main`**: Before opening PR. Merge conflicts → your responsibility, not reviewer's

## PR Expectations

- **Title**: Summarize change in one line
- **Body**: What changed, why, how to test it
- **Size**: Keep PRs small and focused. 2,000-line PR doesn't get reviewed — gets approved. Not same thing
- **Tests**: Ensure all tests pass before creating PR
- **API/config/migration changes**: Call out explicitly in description
- **Evidence**: Include before/after where applicable — screenshots, curl output, log samples, benchmark numbers

## Observability

- Follow Google SRE best practices for service monitoring and reliability.
- Every service must emit structured logs. Unstructured log lines are noise.
### Logging

- **Structured JSON to stdout**: Every log entry includes timestamp, level, logger name, message
- **Request-scoped fields**: Trace ID, span ID, incident ID attached when available
- **OTEL log bridge**: Exports logs to APM platforms with trace/span correlation
### Tracing

- **OpenTelemetry**: For distributed tracing, exported via OTLP
- **Inbound requests**: Every request gets trace
- **Child spans**: Cover downstream calls, background processing, significant internal operations
- **Trace context propagation**: Via W3C `traceparent` headers
### Health Checks

- **Mandatory**: If service cannot verify its own dependencies are reachable → should not report healthy

### Golden Signals

Every service must instrument four Golden Signals as defined by Google SRE:

- **Latency**: Time to service request. Track successful and failed request latency separately — fast error ≠ healthy response
- **Traffic**: Demand on service — requests per second, transactions per second, or appropriate throughput metric
- **Errors**: Rate of failed requests — explicit failures (HTTP 5xx), implicit failures (HTTP 200 with wrong content), policy-based failures (responses exceeding SLO latency threshold)
- **Saturation**: How full service is. CPU, memory, disk, queue depth, connection pool utilization. Alert before hitting 100% — not after

**Golden Signals are baseline**. If service doesn't expose these four metrics → not production-ready.

### RED Method

For request-driven services (APIs, web services, microservices):

- **Rate**: Requests per second
- **Errors**: Failed requests per second
- **Duration**: Distribution of request latency (use histograms, not averages — p50, p95, p99)

**RED metrics feed directly into SLIs/SLOs**. Define SLOs for every user-facing service and alert on SLO burn rate, not raw thresholds.

### SLOs & Error Budgets

- **SLOs required**: Every production service must have defined SLOs. SLO without error budget = wish, not target
- **Error budget exhaustion**: When exhausted, feature work stops and reliability work takes priority. This is mechanism that keeps production stable
- **Monthly reviews**: Review SLO performance monthly. Adjust targets based on actual user impact, not what feels achievable

### Telemetry Export (OpenTelemetry)

- **Standardization**: All services use OpenTelemetry (OTEL) for exporting metrics, traces, logs to external observability/APM platforms. OTEL is vendor-neutral telemetry standard — works with Grafana, Datadog, New Relic, Honeycomb, any OTLP-compatible backend
- **OTEL and `/ops/*` endpoints coexist**: Serve different purposes
  - `/ops/*` endpoints = **pull-based** programmatic access. SRE agent and humans query on-demand to diagnose specific issues. Return structured snapshots of service health
  - OTEL = **push-based** continuous export. Metrics, traces, logs flow to APM platforms for dashboards, alerting, historical analysis. This is data pipeline that powers monitoring, not diagnostic interface
- **Required exports via OTEL**:
  - **Metrics**: Golden Signals and RED metrics as OTEL instruments — Counters for request/error counts, Histograms for latency distributions, UpDownCounters for saturation (active connections, queue depth)
  - **Traces**: Trace per inbound request with child spans for downstream calls, database queries, cache operations, background processing. Trace context propagates via W3C `traceparent` headers
  - **Logs**: Structured JSON logs bridged to OTEL log pipeline so they correlate with traces and metrics in APM platform. Log entries include trace ID and span ID when available
- **Configuration**: OTEL configured via standard environment variables — `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_PROTOCOL`, `OTEL_RESOURCE_ATTRIBUTES`. No custom configuration. If OTLP endpoint not set → OTEL runs as no-op — service works identically without it
- **Auto-instrumentation**: Use OTEL auto-instrumentation libraries for HTTP framework (FastAPI, Express, etc.) and HTTP clients (httpx, requests, etc.) to get request-level metrics and traces without manual code. Add manual spans for business-logic operations not covered by auto-instrumentation

### Composite Service Health

- **Individual metrics insufficient**: Every service must answer one question: **"Is this service healthy?"** Answer is rollup — computed verdict combining Golden Signals, RED metrics, SLO burn rate, and dependency status into single, actionable assessment
- **Status values**: One of **healthy**, **degraded**, or **unhealthy**. No "unknown" — if service cannot determine own health → unhealthy
- **Healthy**: All Golden Signals within SLO thresholds, all dependencies reachable, error budget has remaining capacity
- **Degraded**: One or more signals approaching SLO thresholds, non-critical dependency impaired, or error budget burn rate elevated. Service functioning but at risk
- **Unhealthy**: SLO breached, critical dependency down, error rate exceeds threshold, or saturation at capacity. Service needs immediate attention
- **Composite status exposure**: Through `/ops/status` — single endpoint returning overall verdict with breakdown of what contributed to it. SRE agents and dashboards use as top-level entry point before drilling into individual signals
- **Health computation logic**: Lives in service, not external aggregator. Service owns definition of healthy because only service knows which dependencies are critical vs optional, which error rates are normal, which latency thresholds matter

### SRE Agent Endpoints

Every service must expose operational API endpoints designed for consumption by SRE agents. These endpoints allow agents to understand system state, diagnose issues, and take safe remediation actions without human intervention.

**Read-only diagnostic endpoints** (no auth escalation required):
- `/ops/status` — composite health verdict (healthy/degraded/unhealthy) with breakdown of Golden Signals, RED metrics, SLO burn rate, dependency status. First endpoint agent/human checks. One call answers "is this service healthy?"
- `/ops/health` — deep health check including all downstream dependencies (with latency), connection pools, queue depths. Returns structured JSON with per-dependency status, not just 200 OK. Single source of dependency health
- `/ops/metrics` — current Golden Signals and RED metrics snapshot. Agents use to assess individual signal details after `/ops/status` flags concern
- `/ops/config` — running configuration (sanitized — no secrets). Allows agents to verify expected vs actual config without SSH access
- `/ops/errors` — recent error summary with counts, types, sample stack traces. Gives agents enough context to classify failure without tailing logs

**Safe remediation endpoints** (require SRE agent auth role, all actions idempotent and non-destructive):
- `/ops/cache/flush` — flush application-level caches. Safe to call anytime. Service rebuilds cache from source on next request
- `/ops/cache/refresh` — refresh application-level caches from source of truth. Safe to call anytime
- `/ops/loglevel` — temporarily adjust log verbosity for debugging without redeploy. Reverts to default after configurable TTL

**Hard rules for SRE agent endpoints**:
- No endpoint may delete data, drop connections to databases, restart processes, or modify persistent state. Agents diagnose and stabilize — do not perform destructive operations
- All remediation endpoints are idempotent. Calling twice produces same result as calling once
- Every action through ops endpoint logged to audit trail with agent identity, timestamp, action taken
- Agents make decisions based on aggregate health across services — not single metric in isolation. Spike in latency on one service may be caused by saturation on dependency. Diagnostic endpoints give full picture to make determination
- If agent cannot confidently diagnose or remediate issue → escalates to human. Guessing in production not permitted
- SRE agent's full operating instructions, diagnostic workflow, playbooks, incident documentation format defined in `sre-agent/skill.md`. Agent configured per-project via `sre-agent/config.md` and trained on tech stack chosen from rebuild candidate

## CI/CD

- **CI pipeline**: What runs on each push, PR, merge to main
- **CD pipeline**: How deployments happen, what environments exist
- **Pipeline is source of truth**: If green → deployable. If not → nothing else matters
- **Infrastructure changes**: Go through same PR process as application code. No manual resource creation

## Environment Strategy

- **Minimum environments**: Every project requires dev, staging, prod
- **Dev**: Active development and integration. Can break. Deployed on every merge to `main`
- **Staging**: Mirrors prod in configuration, scale (or near-scale), and data shape. Final gate before production. If doesn't work in staging → doesn't go to prod
- **Prod**: Sacred. Deployments deliberate, reviewed, and reversible
- **Environment parity**: Not optional. If staging uses different database engine, smaller instance class, or skips sidecar that exists in prod → not staging — it's a lie that will betray during cutover
- **Provisioning**: All environments through Terraform. No hand-created resources
- **Configuration**: Environment-specific (endpoints, credentials, feature flags) managed through environment variables or config maps — never through conditional logic in application code

## API Versioning & Contracts

- **Versioning from day one**: Every API with external consumers or consumed by other services must be versioned. Prefer URL path versioning (`/v1/`, `/v2/`) for clarity
- **Contracts as promises**: API contracts documented and treated as promises. Breaking changes require version bump, migration path for consumers, deprecation timeline. Do not break existing consumers silently
- **Legacy rebuild compatibility**: During legacy rebuild, new system must support legacy API surface as compatibility layer until all consumers migrated. Document which legacy endpoints supported, deprecated, removal timeline
- **OpenAPI specs**: Use specs checked into repo. Spec is contract. If code and spec disagree → code is wrong
- **Swagger UI optimization**: Design APIs for optimal Swagger UI interaction. Use JSON request bodies with Pydantic models instead of query parameters for enum fields to enable proper dropdown menus. For editable fields, use Pydantic models with proper enum definitions, examples, descriptions so Swagger UI renders interactive controls users can edit directly. Avoid query parameters for complex operations — reserve for simple filtering, pagination, optional flags. POST/PUT endpoints should use request bodies; GET endpoints should use query parameters only for idempotent operations
- **Integration tests**: Validate API contract on every build. If response shape changes → test fails before consumer discovers in production
- **IPv6 support**: All FastAPI services must support dual-stack IPv4/IPv6 networking. Configure uvicorn to listen on both address families (`host="::"` binds to all interfaces on both IPv4 and IPv6). Validate connectivity in CI/CD with tests that exercise both IPv4 and IPv6 endpoints when environment supports dual-stack networking
- **CI dependencies**: CI/CD pipelines must install both production and development dependencies before running static analysis tools. Use `pip install -r requirements.txt -r requirements-dev.txt` to ensure pylint, mypy, other tools can resolve all imports. Configure PYTHONPATH to include source directories (`export PYTHONPATH=$PWD/src:$PYTHONPATH`) so tools can find local modules

## Data Migration & Validation

- **Highest-risk phase**: Data migration is highest-risk phase of any legacy rebuild. Treat with same rigor as production deployment — planned, scripted, tested, and reversible
- **End-to-end scripting**: Every migration must be scripted end-to-end. No manual SQL, no one-off shell commands, no "just run this notebook." If cannot be re-executed from scratch and produce same result → not migration, it's accident
- **Schema mapping**: Schema mapping between legacy and target must be documented explicitly — every table, every column, every transformation. Rebuild analysis process generates initial `docs/data-migration-mapping.md` from legacy assessment (Step 11). Review and refine during migration planning
- **Staging validation**: Run migrations against copy of production data in staging before touching prod. Validate row counts, referential integrity, null handling, encoding, edge cases (empty strings vs nulls, timezone conversions, truncated fields)
- **Reconciliation checks**: Build reconciliation checks that compare legacy and target data after migration. Counts, checksums, spot-check samples at minimum. Automated reconciliation scripts required — not optional
- **Rollback plan**: Define rollback plan before migration runs. If migration fails midway or validation shows data loss → how revert? If answer is "we can't" → migration plan not ready
- **Large datasets**: For large datasets, plan for incremental or CDC (change data capture) migration rather than big-bang. Dual-write or sync patterns allow legacy system to keep running while data flows to new system
- **Completion criteria**: Data migration never "done" until reconciliation passes and legacy data source formally decommissioned. Until then, track drift

## Feature Parity Tracking

- **Feature parity matrix**: Before rebuild starts, produce complete list of every user-facing feature, integration, workflow in legacy application. Rebuild analysis process generates initial `docs/feature-parity.md` from legacy assessment (Step 10). Review and refine before development begins
- **Feature status**: Each feature gets status — **Must Rebuild**, **Rebuild Improved**, **Intentionally Dropped**, or **Deferred**. Every feature must have status — no unknowns
- **Dropped features**: Features marked **Intentionally Dropped** require documented justification. If users depend on it and you remove without explanation → created regression, not rebuild
- **Acceptance criteria**: Acceptance criteria for rebuild tied to matrix. Rebuild not complete until every **Must Rebuild** and **Rebuild Improved** feature passes acceptance testing
- **Living document**: Update matrix as rebuild progresses. It is living document, not snapshot from day one

## Cutover Strategy

- **Planned phased transition**: Cutover is not single event — planned, phased transition with defined checkpoints, success criteria, and rollback triggers
- **Approach definition**: Define cutover approach in PRD: blue/green deployment, canary rollout, traffic shifting, or parallel run with shadow traffic. Choice depends on risk tolerance and data sensitivity
- **Rollback trigger**: Every cutover plan must include rollback trigger — specific, measurable condition under which you abort and revert to legacy system. "It doesn't feel right" is not trigger. Error rate thresholds, latency SLOs, data reconciliation failures are
- **Cutover rehearsal**: Run cutover rehearsal in staging before executing against prod. Time it. Document every step. Identify what took longer than expected. Fix before real cutover
- **War room**: During cutover, maintain war room or dedicated communication channel. Every participant knows role, runbook, and who makes call to proceed or rollback
- **Legacy standby**: After cutover, legacy system stays running in read-only or standby mode for defined bake period. Do not decommission legacy until bake period passes and all success criteria met
- **Cutover report**: Document cutover outcome — what happened, what deviated from plan, and what you would do differently. Goes in `docs/cutover-report.md`

## Access Control & RBAC

- **Role-based access control**: Every application must implement RBAC. Users get minimum permissions required for role — no shared admin accounts, no blanket access
- **Early definition**: Define roles and permissions early in rebuild, not as afterthought. Document in PRD. Common baseline: admin, operator, viewer. Extend as needed but resist role explosion
- **Auth vs Authorization**: Authentication and authorization are separate concerns. Authentication verifies identity (who you are). Authorization verifies permissions (what you can do). Do not conflate them
- **Centralized identity**: Use centralized identity provider — GCP Identity Platform, AWS Cognito, Firebase Auth, or external IdP (Okta, Auth0). Do not build custom auth. Rolling your own authentication is how breaches happen
- **Service-to-service auth**: Uses service accounts with scoped IAM roles, not shared API keys. Rotate credentials automatically
- **Audit access**: Audit all access to sensitive operations and data. Who accessed what, when, from where. This is not optional — it's how you answer questions during incident

## Architecture Decision Records

- Every significant technical decision gets an ADR (Architecture Decision Record). Stored in `docs/adr/` in the rebuild repo, numbered sequentially: `001-use-postgresql.md`, `002-gke-over-cloud-run.md`, etc.
- An ADR answers four questions: What is the decision? What is the context? What alternatives were considered? Why was this option chosen?
- ADRs are immutable once accepted. If a decision is reversed, write a new ADR that supersedes the original — do not edit the old one. The history of why you changed your mind is as valuable as the decision itself.
- ADRs are required for: technology choices, architectural patterns, data model decisions, third-party service selections, and any deviation from the standards in this document.
- Write the ADR before implementing the decision, not after. If you cannot articulate why you are making a choice, you are not ready to make it.

## Disaster Recovery & Business Continuity

- **DR plan required**: Every production service must have documented disaster recovery plan. Store in `docs/disaster-recovery.md`
- **RTO/RPO**: Define RTO (Recovery Time Objective) and RPO (Recovery Point Objective) for each service. These are business decisions, not engineering guesses — get from stakeholders and design to meet them
- **Backup strategy**: Database backups automated, tested, and stored in separate region. Backup never restored → not backup, it's hope. Test restores quarterly at minimum
- **Infrastructure rebuildability**: Infrastructure must be rebuildable from code. If cloud project or account deleted → Terraform should recreate every resource. If cannot → Terraform incomplete
- **Recovery runbook**: Document recovery runbook: step-by-step instructions that on-call engineer who did not build system can follow at 3 AM. If recovery requires tribal knowledge → will fail when person with knowledge unavailable
- **Multi-region deployment**: Multi-region or multi-zone deployment required for any service with RTO under 1 hour. Single-zone deployments = single points of failure
- **Postmortems**: After any incident triggering DR procedures → conduct blameless postmortem. Document what happened, impact, how resolved, what changes prevent recurrence. Store postmortems in `docs/postmortems/`

## Rebuild Philosophy

- **New repo for rebuild**: A rebuild means new repo. Legacy application's codebase never modified, patched, or forked. All new work happens in clean repository. No exceptions
- **Legacy as reference**: Legacy repo is reference — read it, study it, understand it, but do not touch it. Changing legacy code defeats purpose of rebuild and introduces risk to system still running in production
- **Rewrite from scratch**: If need to understand how legacy app works → read its code and data. If need to reproduce behavior → rewrite from scratch in new repo. Copy-pasting legacy code into new repo = not rebuilding, it's relocating tech debt
- **Coexistence**: Legacy application continues to run until rebuild proven, migrated, and cut over. Two systems coexist during transition. Plan for that

### Dependency Boundaries

- **Hard boundary**: Legacy applications rarely live in isolation. Target repo will reference other repos — shared caches, auth services, message brokers, internal libraries, data pipelines. Cannot pull all into rebuild scope or will never finish
- **Boundary definition**: Draw hard boundary: rebuild covers primary application repo and nothing else. Adjacent repos treated as external services with defined interfaces, not as code you own
- **Interface interaction**: If legacy app depends on another repo for runtime behavior (e.g., shared Redis cache, sidecar service, internal API) → interact through existing interface. Do not fork, inline, or rewrite as part of this rebuild
- **Undocumented interfaces**: If dependency's interface undocumented or unstable → document as contract in new repo. Write integration tests against that contract. When dependency eventually gets rebuilt → contract tells you what to verify
- **Tight coupling**: If dependency so tightly coupled that primary app cannot function without modifying dependency's code → that is finding. Document in legacy assessment and scope.md. May mean rebuild boundary needs shift, or dependency itself needs separate, focused rebuild first
- **Rule of thumb**: If can stub behind interface and rebuild still works end-to-end → stays outside boundary. If cannot → escalate scope decision — do not silently absorb another repo into rebuild
- **Compartmentalized rebuilds**: Each repo gets rebuilt on own timeline, with own scope.md, own PRD, own cutover plan. Compartmentalized rebuilds ship. Monolithic rewrites stall

## Modernization Best Practices

> Every modernized and containerized service — regardless of language — must implement these practices. Each language-specific developer agent (`python-developer-agent`, `c-developer-agent`, `go-developer-agent`) references this section as authoritative cross-cutting standard.

### 1. Static Analysis

Examine code structure and logic for security vulnerabilities, logical errors, runtime failures — without executing program.

| Language | Tool |
|----------|------|
| Python | mypy |
| C | cppcheck, clang-tidy |
| Go | go vet, staticcheck, gosec, govulncheck |

### 2. Code Linting

Enforce consistency in coding style, formatting, and adherence to established standards.

| Language | Tool |
|----------|------|
| Python | pylint |
| C | clang-tidy |
| Go | golangci-lint |

### 3. Code Style Enforcement

Ensure source code adheres to predefined set of formatting and stylistic rules.

| Language | Tool |
|----------|------|
| Python | black |
| C | clang-format |
| Go | gofmt, goimports |

### 4. Cyclomatic Complexity Checks

Measure number of linearly independent paths through code. Keep complexity low for maintainability.

| Language | Tool |
|----------|------|
| Python | complexipy |
| C | lizard, pmccabe |
| Go | gocyclo (via golangci-lint) |

### 5. Unit Testing to Defined Coverage Percentage

Code coverage valuable as concept — reveals untested paths and potential bugs. Do not chase percentage for own sake; write meaningful tests that address functionality and edge cases.

| Language | Tool | Minimum Coverage |
|----------|------|-----------------|
| Python | pytest + pytest-cov | ≥80% (≥90% for template repos) |
| C | Unity or CMocka + gcov/lcov | ≥80% |
| Go | go test -cover | ≥80% |

### 6. GitHub Workflows for Release Process Enforcement

`main` branch updated only via PRs from `prerelease`. Direct commits to `prerelease` prohibited. Workflow: feature branch → PR to prerelease → merge → PR from prerelease to main → merge.

### 7. CI Checks for Docker Image Build and Start

Every CI workflow for container artifacts must verify container builds and application functions, typically via `/status` or `/monitoring` endpoint:

```bash
docker build -t <service>:latest . --pull --no-cache
docker run -d -p 8000:8000 \
  -e TEST_CONTAINER=true \
  -e ENV=dev \
  -e LOG_LEVEL=DEBUG \
  --name <service>-container \
  <service>:latest
sleep 3
response=$(curl --silent --fail http://localhost:8000/status)
if [[ "$response" != "OK" ]]; then
  echo "Container /status endpoint did not return OK"
  exit 1
fi
docker stop <service>-container && docker rm <service>-container
```

### 8. GitHub CODEOWNERS

Specify individuals or teams as owners of specific files, directories, or the entire repository. Subject matter experts are automatically requested for reviews on pull requests.

### 9. GitHub Pull Request Templates

Provide a predefined structure for contributors — purpose of changes, related issues, testing steps, and potential impacts. Reduces back-and-forth communication and streamlines the review process.

### 10. GitHub Actions Local Runner with ACT

When feasible, all GitHub Actions should be set up to run locally with [ACT](https://github.com/nektos/act) for faster feedback.

### 11. README Documentation for Local Development

README dictating important details about repo and how to set it up for local testing/development must be included.

### 12. Reproducible Build Architecture with Lock Files

All applications must implement dependency locking for fully reproducible builds.

| Language | Lock Mechanism |
|----------|---------------|
| Python | `pip-tools` with `pip-compile --generate-hashes` → `requirements.txt` |
| C | `CMakeLists.txt` with pinned versions or vendored dependencies |
| Go | `go.mod` + `go.sum` (built-in) |

### 13. Git Hooks for Local CI Enforcement

All CI tests must be integrated into git hook, enabling developers to verify changes do not break build before pushing.

### 14. Coverage Reports for Code Coverage

All coverage reports must be posted to pull requests as comments for immediate visibility into test coverage changes.

### 15. IaC Misconfiguration Reporting via WIZ and CodeQL

WIZ must scan Infrastructure-as-Code (IaC) files — Terraform, CloudFormation, Kubernetes manifests — to detect misconfigurations and insecure permissions before deployment.

### 16. Log All Logs to stdout/stderr

In Docker container, all logs must be directed to `stdout` and `stderr`. This eliminates in-container log file management and ensures logs are captured by Docker logging driver.

### 17. Entrypoint Environment Variable Validation

If entrypoint script or application requires environment variables, check for existence in entrypoint script:

```bash
if [ -z "$AWS_REGION" ]; then
  printf "Error: AWS_REGION environment variable is not set.\n"
  exit 1
fi
```

### 18. Scripts Exit on Missing Variables or Errors

Using `set -eu` ensures scripts fail fast and clearly when errors or misconfigurations occur.

### 19. Entrypoint Scripts for Build/Runtime Separation

`entrypoint.sh` file establishes clear separation between build and runtime. Entrypoint scripts configure environment variables, execute pre-start initialization, and conduct system checks before launching main application.

### 20. Use `exec` for Main Container Command

Using `exec` replaces shell process with application process, ensuring application becomes PID 1. This enables proper signal handling (`SIGTERM`, `SIGKILL`) for graceful shutdowns.

### 21. Docker Build Best Practices

1. **Multi-stage builds** — separate build and runtime stages to reduce image size
2. **Pin base image versions** — use specific tags or digests for consistency
3. **Leverage `.dockerignore`** — exclude unnecessary files from build context
4. **Minimize installed packages** — reduce image size, dependencies, and vulnerabilities
5. **Create ephemeral containers** — stateless, stoppable, destroyable, recreatable
6. **Decouple applications** — one primary concern per container
7. **Use build cache efficiently** — understand cache mechanics, order layers by change frequency
8. **Sort multi-line arguments alphanumerically** — simplify updates and reviews
9. **Run builds in CI pipelines** — every change automatically built and tested
10. **Adopt trusted base images** — official or verified base images

## Task Scope Rules

- Do not modify files outside assigned task scope
- If discover bug or improvement opportunity unrelated to current task → do not fix — create GitHub issue. Every bug, enhancement, and task gets tracked as issue. No exceptions
- All code work driven through GitHub issues. Do not start work based on ad-hoc prompting alone. If prompt results in work that should be done → create issue first, then work issue
- All individual prompting commands and outcomes logged in `prompting.md` at repo root. Provides audit trail of what was asked, what was generated, what decisions made. If prompted → gets logged
- Do not install new dependencies without explicit approval
- When in doubt about scope, ask before building
