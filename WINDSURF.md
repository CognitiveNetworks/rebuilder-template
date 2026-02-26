# Project: [project-name]

## Architecture

- [Brief description of project structure]
- [Key directories and what lives where]
- [Service boundaries and how components communicate]
- [Data flow — where data enters, how it transforms, where it lands]

### API-First Design
- Every service exposes its functionality through APIs. If it cannot be tested, validated, and operated through an API call, it is not done.
- No business logic hidden behind UIs, CLI tools, or cron jobs that cannot be triggered and verified via API. The UI is a consumer of the API, not a replacement for it.
- All features are built API-first. The API is designed, documented, and testable before any frontend or consumer is built on top of it.
- Every API endpoint must be testable in isolation — given a request, it returns a predictable response. If an endpoint requires manual UI interaction to validate, the design is wrong.
- Use OpenAPI/Swagger specs as the source of truth. The spec is written first, the implementation follows, and contract tests verify they stay in sync.

### Designing for Scale
- Architect every component as if it will need to handle 10x current load without a rewrite. That doesn't mean over-engineer — it means make choices that don't paint you into a corner.
- Stateless services. Application processes should hold nothing in memory between requests. Session data, caches, and job state belong in external stores — not in local variables that die with the process.
- Separate read and write paths early. Even if they hit the same database today, structuring code to distinguish queries from commands makes it trivial to add read replicas, caching layers, or CQRS later.
- Design APIs with pagination, filtering, and rate limiting from day one. Retrofitting these after users depend on unbounded responses is painful and breaking.
- Use queues and async processing for anything that doesn't need a synchronous response. Email, notifications, report generation, webhooks, data enrichment — these are background jobs, not request handlers.
- Database schema decisions are the hardest to reverse. Normalize properly, index deliberately, and think about query patterns before you create tables. A bad schema at scale is a migration project, not a bug fix.
- Connection pooling, circuit breakers, and backpressure are not premature optimization — they are operational hygiene. A service that cannot shed load gracefully will take down everything upstream when it struggles.
- Cache deliberately, not desperately. Know what you're caching, why, and when it expires. Stale cache bugs are harder to diagnose than slow queries.
- Infrastructure should scale horizontally by default. If your architecture requires a bigger box instead of more boxes, you've created a scaling ceiling.
- Plan for failure at every boundary. Services go down, networks partition, disks fill, certificates expire. The question is not if but how your system behaves when a dependency is unavailable.

### Technology Selection
- Choose enterprise-grade technologies. We are building systems that need to run reliably at scale, not prototypes that get replaced in six months. Every technology choice should have a proven track record in production at companies larger than ours.
- Databases: PostgreSQL for relational workloads. It handles JSONB, full-text search, and partitioning well enough that you rarely need a second database engine early on. If you need a document store at scale, use a managed offering with enterprise support — not a hobby-tier project.
- Caching: Redis with persistence and clustering, not Memcached. Redis gives you data structures, pub/sub, and durability options that Memcached does not.
- Container orchestration: Kubernetes. Not Docker Compose in production, not hand-rolled systemd units.
- IaC: Terraform. No exceptions. Infrastructure is code, versioned and reviewed like application code.
- Cloud provider: GCP or AWS. Either is acceptable — choose based on team expertise, existing infrastructure, and managed service availability for the workload. Document the cloud provider decision in an ADR. Do not split a single project across both providers without a documented justification.
- The litmus test for any technology choice: Does it have enterprise support options? Is there a managed offering on your chosen cloud provider? Can you hire engineers who already know it? If the answer to any of these is no, justify the exception in writing or pick something else.

## Development Environment

- [Your stack-specific setup commands here, e.g.:]
- `npm install` to bootstrap dependencies
- `npm run test` to run tests
- `npm run lint` to check style
- [How to run the full stack locally — containers, env vars, seed data]
- [How to verify the environment is working before writing any code]

## Coding Practices

### General Principles
- Write code that the next engineer can understand without asking you. If it needs a comment, the code isn't clear enough — refactor first, comment second.
- Fail fast and fail loud. Silent failures are production incidents waiting to happen. If something is wrong, raise it immediately — do not swallow errors, return empty defaults, or log and continue.
- No dead code. No commented-out blocks. No "just in case" abstractions. If it's not running in production, it doesn't belong in the repo.
- Functions do one thing. If you're naming it `processAndValidateAndSave`, that's three functions.
- Prefer explicit over implicit. Magic values, hidden side effects, and implicit ordering create bugs that are impossible to trace at 2 AM.

### Error Handling
- Handle errors at the boundary where you can do something about them. Do not catch exceptions just to re-throw or log them.
- Every error message should answer: what happened, what was expected, and what the operator should do about it.
- Distinguish between retryable and fatal errors. Retrying a permissions failure is a waste. Crashing on a transient network blip is fragile.

### Security
- Never commit secrets, tokens, or credentials. No exceptions.
- Secrets management: Use your cloud provider's native secrets manager — GCP Secret Manager or AWS Secrets Manager. All application secrets, API keys, database credentials, and service account keys are stored in the secrets manager and injected at runtime — never baked into images, config files, or environment variable definitions in source control. For workloads that span multiple clouds or run on-prem, HashiCorp Vault is the approved alternative. Nothing else.
- Validate and sanitize all external input — user input, API responses, webhook payloads, environment variables. Trust nothing that crosses a boundary.
- Apply least privilege everywhere — database users, API keys, IAM roles, file permissions. If it doesn't need write access, it doesn't get write access.
- Dependencies are attack surface. Pin versions. Audit regularly. Remove what you don't use.

### Performance
- Measure before you optimize. Profiling data beats intuition every time.
- N+1 queries, unbounded loops, and missing indexes are not performance problems — they are bugs. Fix them when you find them.
- Set timeouts on every external call. A missing timeout is a thread leak waiting for a server that will never respond.

## Testing & QA

### Testing Strategy
- Tests are not optional. Untested code is broken code that hasn't been caught yet.
- Write tests that verify behavior, not implementation. If a refactor breaks your test but not the feature, the test was wrong.
- Every bug fix gets a regression test. If it broke once, it will break again.

### Test Levels
- **Unit tests:** Fast, isolated, no network or database. Test business logic, transformations, edge cases. These run in seconds and gate every commit.
- **API tests:** Every endpoint gets tested directly — request in, response out. Validate status codes, response shapes, error handling, auth, pagination, and edge cases. API tests are the primary integration gate. If the API works, consumers can be built with confidence.
- **Integration tests:** Verify that components work together — API endpoints hit the database, services call external APIs through mocked boundaries, migrations run cleanly.
- **End-to-end tests:** Validate critical user workflows against a running stack. Keep these focused on happy paths and high-value failure modes. Flaky E2E tests get fixed or deleted, not skipped.
- **Contract tests:** Validate that API responses match the OpenAPI spec on every build. If the spec and the implementation diverge, the build fails.

### QA Expectations
- Run the full test suite locally before pushing. CI is a safety net, not your first line of defense.
- If you can't write an automated test for it, document the manual test procedure in the PR.
- Test failure is a build failure. Do not merge with failing tests. Do not skip tests to unblock a deploy.
- Load and stress testing happen before major releases, not after the first production incident.

## Git Workflow

- We use git worktrees for parallel development. Each task gets its own worktree and feature branch.
- Branch naming: `feature/<short-description>` or `fix/<short-description>`
- Never commit directly to `main`.
- Write clear, concise commit messages that explain why, not what. The diff shows what changed.
- Squash related changes into logical commits before PR. One commit per logical change — not one per save.
- Rebase on `main` before opening a PR. Merge conflicts are your responsibility, not the reviewer's.

## PR Expectations

- PR title should summarize the change in one line.
- PR body should include: what changed, why, and how to test it.
- Keep PRs small and focused. A 2,000-line PR doesn't get reviewed — it gets approved. That's not the same thing.
- Ensure all tests pass before creating the PR.
- If the change touches an API, interface, config schema, or migration, call it out explicitly in the description.
- Include before/after evidence where applicable — screenshots, curl output, log samples, benchmark numbers.

## Observability

- Follow Google SRE best practices for service monitoring and reliability.
- Every service must emit structured logs. Unstructured log lines are noise.
- **Logging:** Structured JSON to stdout. Every log entry includes timestamp, level, logger name, and message. Request-scoped fields (trace ID, span ID, incident ID) are attached when available. OTEL log bridge exports logs to APM platforms with trace/span correlation.
- **Tracing:** OpenTelemetry for distributed tracing, exported via OTLP. Every inbound request gets a trace. Child spans cover downstream calls, background processing, and significant internal operations. Trace context propagates via W3C `traceparent` headers.
- Health checks are mandatory. If the service can't verify its own dependencies are reachable, it should not report healthy.

### Golden Signals
- Every service must instrument the four Golden Signals as defined by Google SRE:
  - **Latency:** Time to service a request. Track both successful and failed request latency separately — a fast error is not a healthy response.
  - **Traffic:** Demand on the service — requests per second, transactions per second, or the appropriate throughput metric for the service type.
  - **Errors:** Rate of failed requests — explicit failures (HTTP 5xx), implicit failures (HTTP 200 with wrong content), and policy-based failures (responses exceeding an SLO latency threshold).
  - **Saturation:** How full the service is. CPU, memory, disk, queue depth, connection pool utilization. Alert before hitting 100% — not after.
- Golden Signals are the baseline for every service. If a service does not expose these four metrics, it is not production-ready.

### RED Method
- For request-driven services (APIs, web services, microservices), also apply the RED method:
  - **Rate:** Requests per second.
  - **Errors:** Failed requests per second.
  - **Duration:** Distribution of request latency (use histograms, not averages — p50, p95, p99).
- RED metrics feed directly into SLIs (Service Level Indicators) and SLOs (Service Level Objectives). Define SLOs for every user-facing service and alert on SLO burn rate, not on raw thresholds.

### SLOs & Error Budgets
- Every production service must have defined SLOs. An SLO without an error budget is a wish, not a target.
- When the error budget is exhausted, feature work stops and reliability work takes priority. This is not a suggestion — it is the mechanism that keeps production stable.
- Review SLO performance monthly. Adjust targets based on actual user impact, not on what feels achievable.

### Telemetry Export (OpenTelemetry)
- All services standardize on **OpenTelemetry (OTEL)** for exporting metrics, traces, and logs to external observability and APM platforms. OTEL is the vendor-neutral telemetry standard — it works with Grafana, Datadog, New Relic, Honeycomb, and any OTLP-compatible backend.
- **OTEL and `/ops/*` endpoints coexist.** They serve different purposes:
  - `/ops/*` endpoints = **pull-based** programmatic access. The SRE agent and humans query these on-demand to diagnose specific issues. They return structured snapshots of service health.
  - OTEL = **push-based** continuous export. Metrics, traces, and logs flow to APM platforms for dashboards, alerting, and historical analysis. This is the data pipeline that powers monitoring, not the diagnostic interface.
- **What services must export via OTEL:**
  - **Metrics:** Golden Signals and RED metrics as OTEL instruments — Counters for request/error counts, Histograms for latency distributions, UpDownCounters for saturation (active connections, queue depth). These are the same signals exposed by `/ops/metrics`, but pushed continuously rather than polled.
  - **Traces:** A trace per inbound request with child spans for downstream calls, database queries, cache operations, and background processing. Trace context propagates via W3C `traceparent` headers across service boundaries.
  - **Logs:** Structured JSON logs bridged to the OTEL log pipeline so they correlate with traces and metrics in the APM platform. Log entries include trace ID and span ID when available.
- **Configuration:** OTEL is configured via standard environment variables — `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_PROTOCOL`, `OTEL_RESOURCE_ATTRIBUTES`. No custom configuration. If the OTLP endpoint is not set, OTEL runs as a no-op — the service works identically without it.
- **Auto-instrumentation:** Use OTEL auto-instrumentation libraries for your HTTP framework (FastAPI, Express, etc.) and HTTP clients (httpx, requests, etc.) to get request-level metrics and traces without manual code. Add manual spans for business-logic operations that are not covered by auto-instrumentation.

### Composite Service Health
- Individual metrics are not enough. Every service must be able to answer one question: **"Is this service healthy?"** The answer is a rollup — a computed verdict that combines Golden Signals, RED metrics, SLO burn rate, and dependency status into a single, actionable assessment.
- The composite health status is one of: **healthy**, **degraded**, or **unhealthy**. There is no "unknown" — if the service cannot determine its own health, it is unhealthy.
- **Healthy:** All Golden Signals within SLO thresholds, all dependencies reachable, error budget has remaining capacity.
- **Degraded:** One or more signals approaching SLO thresholds, a non-critical dependency is impaired, or error budget burn rate is elevated. The service is functioning but at risk.
- **Unhealthy:** SLO is breached, a critical dependency is down, error rate exceeds threshold, or saturation is at capacity. The service needs immediate attention.
- This composite status is exposed through `/ops/status` — a single endpoint that returns the overall verdict with a breakdown of what contributed to it. SRE agents and dashboards use this as the top-level entry point before drilling into individual signals.
- The health computation logic lives in the service, not in an external aggregator. The service owns its own definition of healthy because only the service knows which dependencies are critical vs. optional, which error rates are normal, and which latency thresholds matter.

### SRE Agent Endpoints
- Every service must expose a set of operational API endpoints designed for consumption by SRE agents. These endpoints allow agents to understand system state, diagnose issues, and take safe remediation actions without human intervention.
- **Read-only diagnostic endpoints** (no auth escalation required):
  - `/ops/status` — composite health verdict (healthy / degraded / unhealthy) with breakdown of Golden Signals, RED metrics, SLO burn rate, and dependency status. This is the first endpoint an agent or human checks. One call answers "is this service healthy?"
  - `/ops/health` — deep health check including all downstream dependencies, connection pools, and queue depths. Returns structured JSON with per-dependency status, not just a 200 OK.
  - `/ops/metrics` — current Golden Signals and RED metrics snapshot. Agents use this to assess individual signal details after `/ops/status` flags a concern.
  - `/ops/config` — running configuration (sanitized — no secrets). Allows agents to verify expected vs. actual config without SSH access.
  - `/ops/dependencies` — dependency graph with status of each. Shows what this service talks to and whether those connections are healthy.
  - `/ops/errors` — recent error summary with counts, types, and sample stack traces. Gives agents enough context to classify the failure without tailing logs.
- **Safe remediation endpoints** (require SRE agent auth role, all actions are idempotent and non-destructive):
  - `/ops/drain` — put the service instance into drain mode. It stops accepting new traffic but finishes in-flight requests. Does not kill the process.
  - `/ops/cache/flush` — flush application-level caches. Safe to call at any time. The service rebuilds cache from source on next request.
  - `/ops/circuits` — view and reset circuit breakers. Agents can identify tripped circuits and reset them after the downstream dependency recovers.
  - `/ops/loglevel` — temporarily adjust log verbosity for debugging without a redeploy. Reverts to default after a configurable TTL.
  - `/ops/scale` — set the target instance count for services with application-managed scaling. Body: `{"target_instances": N, "reason": "..."}`. Returns current and target counts. Bounded by the service's configured min/max limits. Services that scale through cloud-native mechanisms (GKE HPA, Cloud Run, ECS) do not implement this endpoint — the SRE agent scales them directly via cloud provider APIs.
- **Hard rules for SRE agent endpoints:**
  - No endpoint may delete data, drop connections to databases, restart processes, or modify persistent state. Agents diagnose and stabilize — they do not perform destructive operations.
  - All remediation endpoints are idempotent. Calling them twice produces the same result as calling them once.
  - Every action taken through an ops endpoint is logged to the audit trail with the agent identity, timestamp, and action taken.
  - Agents make decisions based on the aggregate health across services — not a single metric in isolation. A spike in latency on one service may be caused by saturation on a dependency. The diagnostic endpoints give agents the full picture to make that determination.
  - If an agent cannot confidently diagnose or remediate an issue, it escalates to a human. Guessing in production is not permitted.
  - The SRE agent's full operating instructions, diagnostic workflow, playbooks, and incident documentation format are defined in `sre-agent/WINDSURF_SRE.md`. The agent is configured per-project via `sre-agent/config.md` and trained on the tech stack chosen from the rebuild candidate.

## CI/CD

- [CI pipeline description — what runs on each push, PR, merge to main]
- [CD pipeline description — how deployments happen, what environments exist]
- The pipeline is the source of truth. If it's green, it's deployable. If it's not, nothing else matters.
- Infrastructure changes go through the same PR process as application code. No manual resource creation.

## Environment Strategy

- Every project requires at minimum three environments: **dev**, **staging**, and **prod**.
- Dev is for active development and integration. It can break. It gets deployed on every merge to `main`.
- Staging mirrors prod in configuration, scale (or near-scale), and data shape. It is the final gate before production. If it doesn't work in staging, it doesn't go to prod.
- Prod is sacred. Deployments to prod are deliberate, reviewed, and reversible.
- Environment parity is not optional. If staging uses a different database engine, a smaller instance class, or skips a sidecar that exists in prod, it is not staging — it is a lie that will betray you during cutover.
- All environments are provisioned through Terraform. No hand-created resources. If it exists in prod, it exists in code.
- Environment-specific configuration (endpoints, credentials, feature flags) is managed through environment variables or config maps — never through conditional logic in application code.

## API Versioning & Contracts

- Every API that has external consumers or is consumed by other services must be versioned from day one. Prefer URL path versioning (`/v1/`, `/v2/`) for clarity.
- API contracts are documented and treated as promises. Breaking changes require a version bump, a migration path for consumers, and a deprecation timeline. Do not break existing consumers silently.
- During a legacy rebuild, the new system must support the legacy API surface as a compatibility layer until all consumers have migrated. Document which legacy endpoints are supported, which are deprecated, and the timeline for removal.
- Use OpenAPI/Swagger specs checked into the repo. The spec is the contract. If the code and the spec disagree, the code is wrong.
- Integration tests validate the API contract on every build. If a response shape changes, the test fails before a consumer discovers it in production.

## Data Migration & Validation

- Data migration is the highest-risk phase of any legacy rebuild. Treat it with the same rigor as a production deployment — planned, scripted, tested, and reversible.
- Every migration must be scripted end-to-end. No manual SQL, no one-off shell commands, no "just run this notebook." If it cannot be re-executed from scratch and produce the same result, it is not a migration — it is an accident.
- Schema mapping between legacy and target must be documented explicitly — every table, every column, every transformation. The rebuild analysis process generates an initial `docs/data-migration-mapping.md` from the legacy assessment (Step 11). Review and refine it during migration planning.
- Run migrations against a copy of production data in staging before touching prod. Validate row counts, referential integrity, null handling, encoding, and edge cases (empty strings vs nulls, timezone conversions, truncated fields).
- Build reconciliation checks that compare legacy and target data after migration. Counts, checksums, and spot-check samples at minimum. Automated reconciliation scripts are required — not optional.
- Define a rollback plan before the migration runs. If the migration fails midway or validation shows data loss, how do you revert? If the answer is "we can't," the migration plan is not ready.
- For large datasets, plan for incremental or CDC (change data capture) migration rather than big-bang. Dual-write or sync patterns allow the legacy system to keep running while data flows to the new system.
- Data migration is never "done" until reconciliation passes and the legacy data source is formally decommissioned. Until then, track drift.

## Feature Parity Tracking

- Before the rebuild starts, produce a feature parity matrix: a complete list of every user-facing feature, integration, and workflow in the legacy application. The rebuild analysis process generates an initial `docs/feature-parity.md` from the legacy assessment (Step 10). Review and refine it before development begins.
- Each feature gets a status: **Must Rebuild**, **Rebuild Improved**, **Intentionally Dropped**, or **Deferred**. Every feature must have a status — no unknowns.
- Features marked **Intentionally Dropped** require a documented justification. If users depend on it and you remove it without explanation, you have created a regression, not a rebuild.
- Acceptance criteria for the rebuild are tied to this matrix. The rebuild is not complete until every **Must Rebuild** and **Rebuild Improved** feature passes acceptance testing.
- Update the matrix as the rebuild progresses. It is a living document, not a snapshot from day one.

## Cutover Strategy

- Cutover is not a single event — it is a planned, phased transition with defined checkpoints, success criteria, and rollback triggers.
- Define the cutover approach in the PRD: blue/green deployment, canary rollout, traffic shifting, or parallel run with shadow traffic. The choice depends on risk tolerance and data sensitivity.
- Every cutover plan must include a rollback trigger — a specific, measurable condition under which you abort and revert to the legacy system. "It doesn't feel right" is not a trigger. Error rate thresholds, latency SLOs, and data reconciliation failures are.
- Run a cutover rehearsal in staging before executing against prod. Time it. Document every step. Identify what took longer than expected. Fix it before the real cutover.
- During cutover, maintain a war room or dedicated communication channel. Every participant knows their role, the runbook, and who makes the call to proceed or rollback.
- After cutover, the legacy system stays running in read-only or standby mode for a defined bake period. Do not decommission legacy until the bake period passes and all success criteria are met.
- Document the cutover outcome — what happened, what deviated from the plan, and what you would do differently. This goes in `docs/cutover-report.md`.

## Access Control & RBAC

- Every application must implement role-based access control. Users get the minimum permissions required for their role — no shared admin accounts, no blanket access.
- Define roles and permissions early in the rebuild, not as an afterthought. Document them in the PRD. Common baseline: admin, operator, viewer. Extend as needed but resist role explosion.
- Authentication and authorization are separate concerns. Authentication verifies identity (who you are). Authorization verifies permissions (what you can do). Do not conflate them.
- Use a centralized identity provider — GCP Identity Platform, AWS Cognito, Firebase Auth, or an external IdP (Okta, Auth0). Do not build custom auth. Rolling your own authentication is how breaches happen.
- Service-to-service authentication uses service accounts with scoped IAM roles, not shared API keys. Rotate credentials automatically.
- Audit all access to sensitive operations and data. Who accessed what, when, and from where. This is not optional — it is how you answer questions during an incident.

## Architecture Decision Records

- Every significant technical decision gets an ADR (Architecture Decision Record). Stored in `docs/adr/` in the rebuild repo, numbered sequentially: `001-use-postgresql.md`, `002-gke-over-cloud-run.md`, etc.
- An ADR answers four questions: What is the decision? What is the context? What alternatives were considered? Why was this option chosen?
- ADRs are immutable once accepted. If a decision is reversed, write a new ADR that supersedes the original — do not edit the old one. The history of why you changed your mind is as valuable as the decision itself.
- ADRs are required for: technology choices, architectural patterns, data model decisions, third-party service selections, and any deviation from the standards in this document.
- Write the ADR before implementing the decision, not after. If you cannot articulate why you are making a choice, you are not ready to make it.

## Disaster Recovery & Business Continuity

- Every production service must have a documented disaster recovery plan. Store it in `docs/disaster-recovery.md`.
- Define RTO (Recovery Time Objective) and RPO (Recovery Point Objective) for each service. These are business decisions, not engineering guesses — get them from stakeholders and design to meet them.
- Database backups are automated, tested, and stored in a separate region. A backup that has never been restored is not a backup — it is a hope. Test restores quarterly at minimum.
- Infrastructure must be rebuildable from code. If a cloud project or account were deleted, Terraform should be able to recreate every resource. If it cannot, the Terraform is incomplete.
- Document the recovery runbook: step-by-step instructions that an on-call engineer who did not build the system can follow at 3 AM. If recovery requires tribal knowledge, it will fail when the person with that knowledge is unavailable.
- Multi-region or multi-zone deployment is required for any service with an RTO under 1 hour. Single-zone deployments are single points of failure.
- After any incident that triggers DR procedures, conduct a blameless postmortem. Document what happened, what the impact was, how it was resolved, and what changes prevent recurrence. Store postmortems in `docs/postmortems/`.

## Rebuild Philosophy

- A rebuild means a new repo. The legacy application's codebase is never modified, patched, or forked. All new work happens in a clean repository. No exceptions.
- The legacy repo is a reference — read it, study it, understand it, but do not touch it. Changing the legacy code defeats the purpose of the rebuild and introduces risk to a system that is still running in production.
- If you need to understand how the legacy app works, read its code and its data. If you need to reproduce its behavior, rewrite it from scratch in the new repo. Copy-pasting legacy code into the new repo is not rebuilding — it's relocating tech debt.
- The legacy application continues to run until the rebuild is proven, migrated, and cut over. Two systems coexist during the transition. Plan for that.

### Dependency Boundaries
- Legacy applications rarely live in isolation. The target repo will reference other repos — shared caches, auth services, message brokers, internal libraries, data pipelines. You cannot pull all of them into the rebuild scope or you will never finish.
- Draw a hard boundary: the rebuild covers the primary application repo and nothing else. Adjacent repos are treated as external services with defined interfaces, not as code you own.
- If the legacy app depends on another repo for runtime behavior (e.g., a shared Redis cache, a sidecar service, an internal API), interact with it through its existing interface. Do not fork it, do not inline it, do not rewrite it as part of this rebuild.
- If a dependency's interface is undocumented or unstable, document it as a contract in the new repo. Write integration tests against that contract. When the dependency eventually gets rebuilt, the contract tells you what to verify.
- If a dependency is so tightly coupled that the primary app cannot function without modifying the dependency's code, that is a finding — document it in the legacy assessment and scope.md. It may mean the rebuild boundary needs to shift, or that the dependency itself needs a separate, focused rebuild first.
- The rule of thumb: if you can stub it behind an interface and the rebuild still works end-to-end, it stays outside the boundary. If you cannot, escalate the scope decision — do not silently absorb another repo into the rebuild.
- Each repo gets rebuilt on its own timeline, with its own scope.md, its own PRD, and its own cutover plan. Compartmentalized rebuilds ship. Monolithic rewrites stall.

## Task Scope Rules

- Do not modify files outside the scope of your assigned task.
- If you discover a bug or improvement opportunity unrelated to the current task, do not fix it — create a GitHub issue. Every bug, enhancement, and task gets tracked as an issue. No exceptions.
- All code work is driven through GitHub issues. Do not start work based on ad-hoc prompting alone. If a prompt results in work that should be done, create an issue first, then work the issue.
- All individual prompting commands and their outcomes are logged in `prompting.md` at the repo root. This provides an audit trail of what was asked, what was generated, and what decisions were made. If it was prompted, it gets logged.
- Do not install new dependencies without explicit approval.
- When in doubt about scope, ask before building.
