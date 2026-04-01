# PRD: [Product/Feature Name]

> **Reference document.** This is the product requirements document from the ideation process. It informs implementation but does not override {lang}-developer-agent/skill.md for coding standards or process rules.

## Background

[Why this rebuild is happening. Link to legacy assessment findings.]

## Goals

[Numbered list of measurable goals]

## Non-Goals

[What this rebuild explicitly does not do]

## Current Behavior

[How the application works today]

## Target Behavior

[How the application should work after the rebuild]

## Target Repository

[The new repo from scope.md where the rebuilt application will live. All new code goes here — the legacy repo is never modified.]

## Technical Approach

[Architecture, stack choices, key implementation decisions]

## API Design

[API-first: target API surface, versioning strategy (/v1/), OpenAPI spec. All functionality testable through APIs. Every endpoint must have a typed Pydantic response model (no bare dict returns) and every request/response model must include `json_schema_extra` examples so Swagger UI is fully functional out of the box.]

## Observability & SRE

[Golden Signals, RED metrics, SLOs with error budgets. /ops/* SRE agent endpoints for diagnostics (health, metrics, config, dependencies, errors) and safe remediation (drain, cache flush, circuit reset, log level).]

**Embedded Monitoring Removal:**

Do **not** carry forward embedded, vendor-specific monitoring or alerting clients from the legacy codebase (e.g., PagerDuty SDK, Stackdriver client libraries, Datadog agent integrations, New Relic APM, custom StatsD emitters). The rebuilt application emits standardized telemetry via OpenTelemetry (OTEL) — metrics, traces, and structured logs — and exposes `/ops/*` diagnostic endpoints. Alerting, paging, and dashboard integrations are handled **externally** by the SRE agent and the platform's monitoring stack. If the legacy application contains an embedded alerting client, document it in the feature-parity matrix as "Intentionally Dropped" with an explanation that alerting is now an infrastructure concern, not an application concern.

## Auth & RBAC

[Identity provider, roles (admin, operator, viewer at minimum), service-to-service auth with scoped IAM. Audit logging on sensitive operations.]

## External Dependencies & Contracts

[Inventory of every external dependency with classification and contract details.]

For each dependency:
- **Name and type:** [service name — managed service / adjacent repo / third-party API / shared infrastructure]
- **Direction:** [outbound (this service calls it) / inbound (it calls this service) / bidirectional]
- **Interface:** [REST, gRPC, SDK, direct DB, message queue, event stream]
- **Contract status:** [documented / undocumented — if undocumented, document it here]
- **Inside/outside rebuild boundary:** [inside = being rebuilt / outside = treat as external service]
- **Fallback behavior:** [what happens if this dependency is unavailable — degrade, queue, fail]
- **SLA expectation:** [expected availability and latency of this dependency]
- **Integration tests:** [what contract tests verify this boundary]

[If the application is self-contained with no external dependencies, state so. Unknown inbound consumers should be listed as a risk with a mitigation strategy (e.g., backward-compatible API response shapes).]

## Infrastructure Migration Plan

[Only include this section if the rebuild involves a cloud provider change or significant infrastructure transformation. Omit for rebuilds that stay on the same provider and infrastructure.]

### Provider Migration
- Source: [current cloud provider]
- Target: [target cloud provider]
- Rationale: [business and technical reasons for the move]

### Managed Service Mapping
| Current | Target | Migration Approach |
|---|---|---|
| [e.g., RDS PostgreSQL 14] | [Cloud SQL PostgreSQL 14] | [data export/import, DMS, CDC, etc.] |
| [e.g., ElastiCache Redis 7] | [Memorystore Redis 7] | [cache is ephemeral — no migration needed] |
| [e.g., SQS] | [Pub/Sub] | [queue interface abstraction — application code change only] |

### Application Code Changes for Provider Migration
[Specific code modules that reference current-provider SDKs, APIs, or services. For each: what changes, what the target equivalent is, and whether it requires an abstraction layer.]

### Dependencies That Stay Behind
[Services or infrastructure components that cannot move to the target provider. For each:]
- **What:** [service name and type]
- **Why it stays:** [reason — shared by other teams, vendor lock-in, not in rebuild scope]
- **Connectivity:** [how the rebuilt app reaches it — VPN, public API, Cloud Interconnect, etc.]
- **Risk:** [latency, availability, cost implications of cross-cloud connectivity]

### IaC Strategy
[Target IaC tool, state backend, module structure. If migrating from another IaC tool (e.g., CloudFormation → Terraform), describe the approach.]

### Infrastructure Migration Phases
[How infrastructure changes are sequenced relative to the application rebuild. Does infra move first? In parallel? After the app is rebuilt?]

## Data Migration Plan

[How existing data transitions to the new system]

## Rollout Plan

[How this gets deployed — phased rollout, feature flags, parallel run, etc.]

## Success Criteria

[How you know the rebuild succeeded — metrics, tests, user feedback, SLO targets met]

## ADRs Required

[List the architecture decisions that need ADRs before implementation begins — e.g., cloud provider, database, auth provider, API versioning approach]

## Open Questions

[Unresolved decisions that need input]
