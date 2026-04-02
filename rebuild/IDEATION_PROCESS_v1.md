# Legacy Rebuild Process

**Type:** Executable Process — Single-Shot
**Version:** 1.0

## How to Run

1. Create a project working directory: `mkdir -p rebuild-inputs/my-project`
2. Clone the primary legacy repo into it: `git clone <url> rebuild-inputs/my-project/repo`
3. Copy `../scope.md` and `input.md` into the working directory (do not modify the templates).
4. Fill out both copies with the current and target state of the application.
5. Run `./run.sh ../rebuild-inputs/my-project`
6. AI executes all steps and writes all results into the project directory.
7. Read output files and decide which rebuild approach to pursue.

## Input

Read the provided `scope.md` and `input.md` files. Extract:
- The current application and its stack
- Known pain points and technical debt
- Target state and constraints
- Any optional context from the developer
- Adjacent repositories (if listed in scope.md) — these are related codebases included in the rebuild scope

## Process

Execute the following steps in order. Do not ask for approval between steps. Run the entire process and write all output files when complete.

> **Phase structure:** Steps 1–11 (Analyze) produce the analysis artifacts,
> PRD, agent configs, ADRs, and mapping documents. These are executed by
> `run.sh` in a single automated pass. Steps 12–18 (Build) validate the code,
> generate remaining documentation, and capture process feedback. These are
> executed during interactive development sessions with the developer agent
> after the service code is written.

### Parallel Execution Windows

Some steps within each phase share inputs but produce independent outputs.
When the execution environment supports sub-agents (e.g., `runSubagent` in
VS Code Copilot, parallel Cascade sessions), steps inside a **parallel
window** MAY be dispatched concurrently to reduce wall-clock time and token
consumption. Each sub-agent receives the shared input artifacts and writes
its own output file — no sub-agent depends on another sub-agent's output.

| Window | After | Parallel Steps | Shared Input | Token Savings |
|--------|-------|---------------|--------------|---------------|
| **W1** | Step 1 completes | Steps 2 + 3 | `legacy_assessment.md`, `scope.md`, `input.md`, `repo/` | Moderate — two medium docs |
| **W2** | Step 6 completes | Steps 7 + 8 + 9 + 10 + 11 | `prd.md`, `legacy_assessment.md`, `modernization_opportunities.md`, `feasibility.md`, `candidate_*.md`, `scope.md`, `input.md`, `repo/`, template files | **High** — five independent outputs, avoids carrying full conversation history |
| **W3** | Step 12 completes | Steps 13a + 14 + 15 | Built codebase + `prd.md` + Step 12 audit results | Moderate — three independent doc/test tasks |

After each parallel window, a **consistency check** verifies cross-artifact
coherence (terminology, service names, endpoint lists, schema references).
See the consistency check steps below.

If sub-agents are not available, execute steps sequentially as before — the
process produces identical results either way. Parallel execution is an
optimization, not a requirement.

**Detection:** Before the first parallel window, check whether a sub-agent
dispatch tool is available in your execution environment (e.g., `runSubagent`
in VS Code Copilot agent mode). If it is, use parallel dispatch for steps in
W1, W2, and W3. If it is not, execute all steps sequentially. Do not hardcode
IDE names in detection logic — check for the capability, not the brand.

### Step 1: Legacy Assessment

> **Step 1a — Capture Prompt**: Before any analysis, copy the user's original
> rebuild request verbatim into `input.md § Original Prompt`. This is the
> source-of-truth for what was asked. Preserve the exact wording — do not
> summarize or paraphrase.

Analyze the current application described in `../scope.md` and `input.md`.

Evaluate the application across these dimensions:

**Architecture Health**
- Is the architecture appropriate for the application's current scale and requirements?
- Are there clear separation of concerns, or is it a tangled monolith?
- How coupled are the components? Can pieces be replaced independently?

**Code & Dependency Health**
- What is the age and maintenance status of key dependencies?
- Are there dependencies that are EOL, deprecated, or have known CVEs?
- How far behind is the stack from current LTS/stable versions?

**API Surface Health**
- Does the application expose APIs? Are they documented (OpenAPI spec)?
- Are APIs versioned? Are there consumers beyond the frontend?
- Can functionality be tested and validated through API calls alone, or is it locked behind UI-only workflows?

**Observability & SRE Readiness**
- What monitoring, logging, alerting, and tracing exists?
- Are there defined SLOs/SLAs? Are Golden Signals (latency, traffic, errors, saturation) instrumented?
- Are there operational endpoints for diagnostics, or is SSH the only way to understand system state?

**Auth & Access Control**
- How do users authenticate? Is there RBAC or is it all-or-nothing access?
- Are there shared credentials, hardcoded API keys, or service accounts with excessive permissions?
- Is service-to-service auth scoped, or do services use a single shared key?

**Operational Health**
- How is the application deployed? Is it reproducible?
- What does the testing story look like? Coverage? CI/CD?
- Are there monitoring, logging, and alerting gaps?

**Data Health**
- Is the data model normalized and well-structured, or has it accumulated drift?
- Are there migration scripts or is the schema managed manually?
- How complex would a data migration be?

**Developer Experience**
- How long does it take a new developer to get productive?
- Are there undocumented tribal knowledge dependencies?
- What is the local development setup like?

**Infrastructure Health**
- What cloud provider(s) does the application run on? Are there components spread across providers or a mix of cloud and on-prem?
- Is the application containerized? If so, what orchestration is used (ECS, EKS, GKE, Docker Compose, none)?
- Is infrastructure defined as code (Terraform, CloudFormation, Pulumi)? Or are resources hand-created?
- What managed services does the application depend on? (RDS, Cloud SQL, ElastiCache, Memorystore, SQS, Pub/Sub, etc.)
- How portable is the application? Could it move to a different cloud provider without rewriting application code? What creates provider lock-in?
- Are there cloud-provider-specific SDKs, APIs, or services embedded in the application code (e.g., boto3 for AWS, google-cloud-* for GCP)?
- If scope.md specifies a cloud migration, what managed services need equivalents on the target provider? What has no direct equivalent?

**External Dependencies & Integration Health**
- What external services or APIs does this application call at runtime? Are those interfaces documented?
- What services or systems consume this application's API? Are the consumers known or unknown?
- Does the application share databases, caches, message queues, or storage with other repos?
- Does the application depend on internal libraries or packages from repos the organization owns?
- Do other systems read from or write to this application's data (ETL, CDC, data warehouse feeds)?
- For each dependency: is it loosely coupled (can be stubbed behind an interface) or tightly coupled (requires modifying the dependency to rebuild this app)?
- Are any dependencies undocumented, unstable, or owned by teams outside the rebuild scope?

**Adjacent Repository Analysis (only if adjacent repos are provided)**

If adjacent codebases were provided alongside the primary repo, read and analyze each one. For each adjacent repo:

- What does it do? What is its tech stack?
- How does it integrate with the primary repo? (API calls, shared database, shared cache, message queue, direct imports)
- What state is shared between them? (tables, schemas, cache keys, queue topics)
- Where is the coupling? Identify every integration point — API endpoints called, database tables accessed, shared auth, common config.
- Can the adjacent repo's functionality be absorbed into the rebuilt service, or should it remain a separate service with a clean interface?
- What breaks if you rebuild the primary without changing the adjacent repo?

The adjacent repos are in scope — their code can be read and their behavior can be incorporated into the rebuild. Dependencies NOT provided as adjacent repos remain outside the rebuild boundary and are treated as external services.

Write results to `output/legacy_assessment.md` using this structure:

```
# Legacy Assessment

> **Reference document.** This is analysis output from the ideation process. It informs decisions but does not override {lang}-developer-agent/skill.md.

## Application Overview
[Summary from scope.md and input.md]

## Architecture Health
- Rating: [Good / Acceptable / Poor / Critical]
- [Findings]

## API Surface Health
- Rating: [Good / Acceptable / Poor / Critical]
- [Findings]

## Observability & SRE Readiness
- Rating: [Good / Acceptable / Poor / Critical]
- [Findings]

## Auth & Access Control
- Rating: [Good / Acceptable / Poor / Critical]
- [Findings]

## Code & Dependency Health
- Rating: [Good / Acceptable / Poor / Critical]
- [Findings]

## Operational Health
- Rating: [Good / Acceptable / Poor / Critical]
- [Findings]

## Data Health
- Rating: [Good / Acceptable / Poor / Critical]
- [Findings]

## Developer Experience
- Rating: [Good / Acceptable / Poor / Critical]
- [Findings]

## Infrastructure Health
- Rating: [Good / Acceptable / Poor / Critical]
- Cloud Provider(s): [current provider(s)]
- Containerized: [Yes/No — current container and orchestration status]
- IaC: [Terraform / CloudFormation / Pulumi / None]
- Managed Services: [list of cloud-managed services the app depends on — RDS, ElastiCache, SQS, etc.]
- Provider Lock-in: [Low / Medium / High — what ties the app to the current provider]
- Cloud Migration Impact: [Only if scope.md specifies a provider change. What managed services need equivalents? What SDK/API references exist in code? What has no direct equivalent on the target provider?]
- [Findings]

## External Dependencies & Integration Health
- Rating: [Good / Acceptable / Poor / Critical]
- Outbound Dependencies: [list of services this app calls, or "None"]
- Inbound Consumers: [list of known consumers, or "Unknown — risk finding"]
- Shared Infrastructure: [databases, caches, queues shared with other repos, or "None"]
- Internal Libraries: [shared repos or packages, or "None"]
- Data Dependencies: [ETL, CDC, warehouse feeds, or "None"]
- Tightly Coupled: [dependencies that cannot be stubbed — scope escalation required, or "None"]
- [Findings and risk assessment]

## Adjacent Repository Analysis
[Include this section only if adjacent repos were provided. Omit entirely for single-repo rebuilds.]

### [Adjacent Repo Name]
- **Purpose:** [what it does]
- **Tech Stack:** [language, framework, database]
- **Integration Points:** [how it connects to the primary repo — API calls, shared DB, shared cache, queues]
- **Shared State:** [specific tables, schemas, cache keys, queue topics shared with primary]
- **Coupling Assessment:** [tight / moderate / loose] — [explanation]
- **Rebuild Recommendation:** [absorb into primary rebuild / keep as separate service / rebuild independently]

### Cross-Repo Integration Summary
- **Total integration points:** [count]
- **Shared databases/schemas:** [list]
- **Shared infrastructure:** [caches, queues, storage]
- **Risk if rebuilt independently:** [what breaks if primary is rebuilt without changing adjacent repos]

## Summary
- Overall Risk Level: [Low / Medium / High / Critical]
- Top 3 Risks: [list]
- Strongest Assets to Preserve: [list — what's working well and should carry forward]
```

### Step 2: Component Overview

Using the legacy assessment from Step 1 and the source code in `repo/`, write a **Component Overview** document that explains the current application for a non-developer audience — product managers, architects, team leads, and new engineers who need to understand what this system does without reading code.

This document describes the **current software as it exists today**, not the rebuilt version.

> **Critical constraint:** The component overview must contain **zero references to the target state, the rebuild, or any planned changes.** Do not add blockquotes, notes, or parentheticals about what is being removed, replaced, consolidated, or dropped in the rebuild. If a feature exists in the legacy code today (even if it is deprecated, dead code, or scheduled for removal), describe it as-is. The target state is documented in the PRD, ADRs, and feature parity matrix — not here. This document gives readers a snapshot of the legacy system in its current form so they can understand what exists before reading any rebuild plans.

**Audience:** Someone who has never seen the codebase. Write in plain language. Avoid code snippets. Define domain terms where first used.

**Required Sections:**

1. **What Is This?** — One-paragraph plain-language summary of what the component does.
2. **Why Does It Exist?** — Business context: what problem it solves and why the platform needs it.
3. **Key Concepts** — Domain glossary explaining terms that appear throughout the codebase (e.g., tokens, zoos, UMPs, CDB). Each concept gets a heading with a 2-3 sentence definition.
4. **What It Does** — Description of each major functional area or domain module. For each, state its purpose, what data it manages, and who uses it. Written for comprehension, not as an API reference.
5. **Pure Utility Functions** (if applicable) — Table of standalone functions with plain-language descriptions. Note that these have no infrastructure dependencies.
6. **CLI Tools** (if applicable) — Table of command-line entry points with descriptions.
7. **How It Fits in the Platform** — Mermaid diagram showing where this component sits relative to upstream and downstream systems, with a narrative data flow summary.
8. **How Teams Consume It** — Table of consumption modes (library import, API call, event subscription, etc.) with audience and prerequisites for each.
9. **Technology** — Table of current stack choices with brief notes.
10. **Deployment** — How the application is currently deployed, configured, and operated.
11. **Known Limitations** — Table of current limitations and gaps (from the legacy assessment findings).
12. **Codebase** — Repository link, approximate size, package structure, dependency count.

**Guidance:**
- Keep it under 300 lines — this is an overview, not a specification.
- Include at least one mermaid architecture diagram.
- Domain terms should be defined where first used, not assumed.
- Draw from the legacy assessment findings, `scope.md`, `input.md`, and the source code.

Write results to `docs/component-overview.md` inside the rebuilt application directory.

> **Parallel Window W1:** Steps 2 and 3 share the same inputs (legacy
> assessment, `scope.md`, `input.md`, source code) and produce independent
> outputs. If sub-agents are available, dispatch both concurrently. Step 4
> depends on Step 3's output, so it must wait for Step 3 to complete.

### Step 3: Modernization Opportunities

Using the legacy assessment and the pain points from scope.md, identify the top modernization opportunities.

An opportunity qualifies ONLY if:
- It directly addresses a pain point identified in scope.md or discovered in the legacy assessment (Step 1)
- It has a clear before/after — the improvement is measurable or demonstrable
- It is technically feasible given the constraints in scope.md
- It would meaningfully improve the application for its users or maintainers

**Infrastructure migration as an opportunity:** If scope.md specifies a cloud provider change, evaluate the infrastructure migration as a modernization opportunity. Containerization, IaC adoption, managed service upgrades, and cloud-native replacements for hand-rolled infrastructure are all valid opportunities — but only if they address real pain points or are required by the target infrastructure in scope.md. Do not treat a cloud migration as an excuse to change everything.

For each opportunity, document:
- What changes and why
- What the current state is (with specifics — not just "it's slow")
- What the target state looks like
- What the migration path is
- What could go wrong

**No hypothetical improvements.** Every opportunity must trace back to a real pain point or a concrete finding from the assessment. If the current approach works fine, leave it alone.

Write results to `output/modernization_opportunities.md`. Begin the file with:

```
> **Reference document.** This is analysis output from the ideation process. It informs decisions but does not override {lang}-developer-agent/skill.md.
```

### Step 4: Feasibility Analysis

For each modernization opportunity rated High or Critical impact, validate:

1. **Effort:** Can this be completed by the team described in scope.md within the stated constraints? Estimate in t-shirt sizes (S/M/L/XL) with rationale.
2. **Risk:** What could go wrong? Data loss, downtime, feature regression, integration breakage. Rate: Low / Medium / High.
3. **Dependencies:** Does this block or get blocked by other opportunities? What order should things happen?
4. **Rollback:** If this fails, can you revert? How?

**Feasibility verdict per opportunity:** Go / Caution / No-Go. No-Go opportunities do not become rebuild candidates.

Write results to `output/feasibility.md`. Begin the file with:

```
> **Reference document.** This is analysis output from the ideation process. It informs decisions but does not override {lang}-developer-agent/skill.md.
```

### Step 5: Rebuild Approach Candidates

For each feasible opportunity (or logical grouping of related opportunities), create a separate output file: `output/candidate_N.md` where N is 1, 2, 3, etc.

Each candidate file uses this structure:

```
# Rebuild Candidate: [Working Title]

> **Reference document.** This is analysis output from the ideation process. It informs decisions but does not override {lang}-developer-agent/skill.md.

## One-Sentence Summary

[What does this rebuild accomplish in one sentence?]

## Current State

[What exists today — architecture, stack, problems]

## Target State

[What this looks like after the rebuild]

## Tech Stack

[Specific technologies, frameworks, and versions]

## Migration Strategy

[How you get from current to target — step by step]

## Data Migration

[How data moves from old to new — schema changes, ETL, backfill]

## What Breaks

[Features, integrations, or workflows that will be disrupted during migration]

## Phased Scope

### Phase 1 (MVP — [timeframe])
[What ships first — the minimum viable rebuild]

### Phase 2
[What comes next]

### Phase 3 (if applicable)
[Longer-term improvements]

## Estimated Effort

[T-shirt size with breakdown by phase]

## Biggest Risk

[Single biggest reason this fails]

## API Design

[API-first approach. Target API surface, versioning, OpenAPI spec plan.]

## Observability & SRE

[Golden Signals, RED metrics, SLOs, /ops/* SRE agent endpoints for diagnostics and safe remediation.]

## Auth & RBAC

[Identity provider, roles and permissions, service-to-service auth.]

## Dependency Contracts

[For each external dependency — outbound services, inbound consumers, shared infrastructure, internal libraries, data feeds:]
- Classification: inside rebuild boundary / outside rebuild boundary
- Interface: [REST, gRPC, SDK, direct DB, message queue, etc.]
- Contract: [documented / undocumented — if undocumented, must be documented as part of rebuild]
- Fallback: [behavior if this dependency is unavailable]
- Tightly Coupled: [Yes/No — if Yes, scope escalation required per STANDARDS.md Dependency Boundaries]
- Integration Tests: [what contract tests are needed at this boundary]

[If the application has no external dependencies, state "None — application is self-contained."]

## Infrastructure Migration

[Only include this section if scope.md specifies a cloud provider change or significant infrastructure transformation. Omit for rebuilds that stay on the same provider.]

### Provider Change
- Moving from: [current provider]
- Moving to: [target provider]
- Rationale: [why — from scope.md]

### Managed Service Mapping
| Current Service | Current Provider | Target Equivalent | Target Provider | Migration Notes |
|---|---|---|---|---|
| [e.g., RDS PostgreSQL] | [AWS] | [Cloud SQL PostgreSQL] | [GCP] | [DAPR] |[compatible / requires changes / no equivalent] |

### Application Code Changes
[Cloud-provider-specific code that must change — SDK imports (boto3 → google-cloud-*), API calls, auth mechanisms, storage interfaces. List specific files and modules affected.]

### Cross-Cloud Dependencies
[Services or dependencies that remain on the original provider. For each: what it is, why it cannot move, how the rebuilt app will reach it (VPN, public API, interconnect), and the latency/reliability implications. Include any DAPR notes that affect these items when used]

### IaC Migration
[Current IaC state and target. If moving from CloudFormation to Terraform, or from no IaC to Terraform, describe the scope.]

## Rollback Plan

[How to revert if things go wrong]
```

### Step 6: PRD Generation

For the rebuild candidate that best addresses the highest-priority pain points from scope.md, generate a PRD.

Write it to `output/prd.md` using this structure:

```
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

Do **not** carry forward embedded, vendor-specific monitoring or alerting clients from the legacy codebase (e.g., PagerDuty SDK, Stackdriver client libraries, Datadog agent integrations, New Relic APM, custom StatsD emitters). The rebuilt application emits standardized telemetry via OpenTelemetry (OTEL) — metrics, traces, and structured logs — and exposes `/ops/*` diagnostic endpoints. Alerting, paging, and dashboard integrations are handled **externally** by the SRE agent and the platform's monitoring stack (e.g., Cloud Monitoring alerting policies, Prometheus Alertmanager). If the legacy application contains an embedded alerting client, document it in the feature-parity matrix as "Intentionally Dropped" with an explanation that alerting is now an infrastructure concern, not an application concern. Remove the dependency from `pyproject.toml` / `requirements.txt` and update `config.py`, `.env.example`, and all documentation accordingly.

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
| [e.g., RDS PostgreSQL 14] | [Cloud SQL PostgreSQL 14] | [data export/import, DMS, CDC, etc.] [DAPR]|
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
```

---

> **Parallel Window W2:** Steps 7, 8, 9, 10, and 11 all depend on the PRD
> (Step 6) and earlier analysis artifacts, but are **completely independent of
> each other**. This is the highest-value parallelization point in the process.
>
> If sub-agents are available, dispatch all five concurrently. Each sub-agent
> receives:
> - `output/prd.md` (the PRD from Step 6)
> - `output/legacy_assessment.md` (from Step 1)
> - `output/modernization_opportunities.md` (from Step 3)
> - `output/feasibility.md` (from Step 4)
> - `output/candidate_*.md` (from Step 5 — all candidate files)
> - `scope.md` and `input.md`
> - `repo/` (legacy source code — needed for feature discovery and schema mapping)
> - The relevant template file(s) for its output
>
> Not every sub-agent needs every artifact. Steps 7 and 8 primarily need the
> PRD and templates. Step 9 (ADRs) needs modernization opportunities,
> feasibility, and candidates for the Alternatives Considered sections.
> Step 10 (Feature Parity) and Step 11 (Data Migration) need the legacy
> source code for thorough discovery. Providing the full set to all five
> is simpler than customizing per-step and adds negligible overhead.
>
> **Parallel-safe referencing rule:** When running in parallel, sub-agents
> MUST NOT reference other W2 outputs by name or number. Specifically:
> - ADRs (Step 9) must not assert what other W2 documents contain (e.g.,
>   do not write "the Library Transitions table in feature-parity.md
>   maps every function" — the sub-agent cannot know what Step 10 wrote).
> - Feature Parity (Step 10) and Data Migration (Step 11) must reference
>   decisions by describing them (e.g., "DAI dropped per PRD Non-Goal #3")
>   rather than by ADR number (e.g., "see ADR-009"), since ADR numbers
>   are assigned by the Step 9 sub-agent and are not in the shared inputs.
> - SRE Agent Config (Step 7) and Developer Agent Config (Step 8) must not
>   reference ADR numbers in configuration files or TODO comments (e.g.,
>   do not write `<!-- TODO: finalize per ADR-008 -->` — use a description
>   instead: `<!-- TODO: finalize container platform per PRD §Technical Approach -->`).
> - Step 11a (consistency check) will reconcile cross-references after all
>   sub-agents complete — inserting ADR numbers and navigation links.
>
> Each sub-agent writes its output to the prescribed location. After all five
> complete, execute **Step 11a: Cross-Artifact Consistency Check** before
> proceeding to the Build phase.
>
> **Token savings:** In sequential execution, by Step 11 the context window
> contains the full conversation history from Steps 1–10. Each sub-agent
> starts fresh with only the PRD + its template — dramatically smaller
> context. For large legacy codebases with adjacent repos, this can be the
> difference between staying within context limits and hitting them.
>
> **Sub-agent failure:** If any W2 sub-agent fails or produces incomplete
> output, re-run that step sequentially using the same shared inputs. Do not
> re-run steps that succeeded — their outputs are already written to disk.
> If the Step 9 sub-agent fails, re-run it first since Check 7 depends on
> `docs/adr/adr-index.yaml` for cross-reference insertion.

### Step 7: SRE Agent Configuration

After the PRD is generated, update the SRE agent's tech stack to match the chosen rebuild candidate.

**⚠️ STRICT TEMPLATE POPULATION RULES — apply to both skill.md and config.md:**

1. **PRESERVE EVERY SECTION.** Do not delete, merge, skip, or summarize any section from the template. Every heading, table, list, and block must appear in the output.
2. **ONLY REPLACE PLACEHOLDERS.** Find text wrapped in `*[brackets]*` or `[brackets]` and replace it with the real value. Do not rewrite surrounding prose.
3. **DO NOT REPHRASE.** Keep all instructional comments (lines starting with `>`) exactly as they are. Do not reword them.
4. **DO NOT ADD SECTIONS.** If the template doesn't have a section for something, don't invent one.
5. **KEEP FORMATTING IDENTICAL.** Markdown heading levels, table column counts, list styles, code block languages — all must match the template exactly.
6. **IF A VALUE IS UNKNOWN**, leave the placeholder as-is and add a TODO comment: `<!-- TODO: fill after infra provisioning -->`.
7. **DIFF CHECK.** After generating the output, mentally diff it against the template. The only differences should be placeholder values replaced with real values. If any structural difference exists, fix it before writing the file.

Read the Tech Stack section from the PRD generated in Step 6. Write the matching values into the Tech Stack section of the SRE agent's `skill.md` (path provided by the runner), replacing the placeholder values:

- **Cloud Provider** — from the PRD's Technical Approach
- **Orchestration** — from the PRD's Technical Approach
- **Backend** — language and framework from the PRD's Tech Stack
- **Database** — engine, managed service, and version from the PRD's Tech Stack
- **Cache** — engine and managed service from the PRD's Tech Stack
- **Additional** — any queues, CDNs, service discovery, or third-party APIs referenced in the PRD

Also update the SRE agent's `config.md` (path provided by the runner):
- Populate the Tech Stack section with the same values.
- Pre-fill the Service Registry with service names from the PRD's architecture description. Use `*[TODO: URL after infra provisioning]*` as the Base URL — these are populated after Terraform provisions the infrastructure (Cloud Run URL, load balancer endpoint, etc.).
- Set SLO Thresholds from the PRD's Observability & SRE section if SLO targets are defined.
- Leave the PagerDuty Integration, Escalation Contacts, Agent Auth, Cloud Platform Access, and Runtime Configuration sections with their template placeholders — these are populated during deployment, not during the rebuild process.

**LLM Provider:** If the target cloud is GCP, the SRE agent should use **Vertex AI** (Gemini) as its LLM provider. This is a GCP-native integration that uses Application Default Credentials — no API key needed. The Cloud Run service account authenticates automatically. Deploy with `--vertex-ai --gcp-direct` flags. If the target cloud is AWS or the project uses a non-GCP LLM, set `LLM_API_KEY` and `LLM_API_BASE_URL` accordingly.

This ensures the SRE agent is configured for the exact stack being built from day one — not backfilled after the first incident. The Service Registry URLs are the one piece that gets filled in post-deployment, once the service has a reachable endpoint. Before wiring PagerDuty, verify each URL responds to `/ops/status`.

### Step 8: Developer Agent Configuration

After the PRD is generated, populate the developer agent's per-project configuration so teams start with accurate, project-specific settings from day one.

**Target Language Selection:** Determine the target language from the PRD's
Technical Approach / Tech Stack section (or from `scope.md` if specified
explicitly). The language determines which agent directory and template repo
to use:

| Language | Developer Agent | QA Agent | Template Repo |
|---|---|---|---|
| Python | `python-developer-agent/` | `python-qa-agent/` | `rebuilder-evergreen-template-repo-python` |
| C | `c-developer-agent/` | `c-qa-agent/` | `rebuilder-evergreen-template-repo-c` |
| Go | `go-developer-agent/` | `go-qa-agent/` | `rebuilder-evergreen-template-repo-go` |

Throughout Steps 8a–8d below, `{lang}` refers to the target language prefix
(e.g., `python`, `c`, `go`). Replace `{lang}` with the actual value in all
file paths and references.

**Three skill.md Files — Distinct Roles:**

Every rebuilt service uses three `skill.md` files. They serve different purposes, are loaded at different times, and come from different sources. All three must be explicitly followed.

|  | `template/skill.md` | `{lang}-developer-agent/skill.md` | `{lang}-qa-agent/skill.md` |
|---|---|---|---|
| **Purpose** | Universal build standard — HOW TO BUILD | Project-specific coding rules — HOW TO WRITE CODE | Verification procedures — HOW TO CHECK |
| **Scope** | Same for every Evergreen Python rebuild | Populated per project | Populated per project |
| **Loaded** | Auto-loaded every IDE session via `.windsurfrules` + explicitly before Build phase and QA audit | Auto-loaded every IDE session via `.windsurfrules` | On demand via `/qa` workflow or Step 12 |
| **Format** | Checkboxes (auditable punch list) | Prose rules (behavioral instructions) | Verification procedures + acceptance criteria |
| **Mutability** | Immutable — org-wide standard | Customized per project | Customized per project |
| **Source** | `rebuilder-evergreen-template-repo-{lang}` | Built on demand from `rebuilder-template` (Step 8a) | Built on demand from `rebuilder-template` (Step 8d) |

> **Key distinction:** `template/skill.md` defines the structural requirements every service must meet (Dockerfile pattern, entrypoint pattern, Helm charts, CI pipeline, required files, tooling). `{lang}-developer-agent/skill.md` defines how to write code for a specific project (architecture, coding practices, testing, observability). `{lang}-qa-agent/skill.md` defines how to verify the developer agent's output meets quality standards.
>
> All three files must exist in the built repo. `template/skill.md` and `{lang}-developer-agent/skill.md` are auto-loaded via `.windsurfrules` every session. `{lang}-qa-agent/skill.md` is loaded on demand when quality verification is needed.

#### 8a: Populate skill.md

Read the PRD generated in Step 6 and update the developer agent's `skill.md` (path provided by the runner):

- **Project name** — replace `[project-name]` in the header with the project name from the PRD
- **Architecture section** — replace the placeholder lines with a brief description of the project structure, key directories, and service boundaries based on the PRD's Technical Approach. Keep it to 3-5 bullet points.
- **Development Environment section** — replace the placeholder lines with stack-specific setup commands based on the language/framework. For example, a Python/FastAPI project gets `pip install -r requirements.txt`, `pytest`, `uvicorn main:app --reload`. Include how to run the full stack locally (e.g., `docker compose up`).
- **Logging/tracing placeholder** — replace `[Logging framework and format]` and `[Metrics and tracing setup]` with the logging and observability tools from the PRD's Observability & SRE section (e.g., "Structured JSON logging via Python `logging`" and "OpenTelemetry for distributed tracing, exported to Cloud Trace").

Leave sections that define process standards (coding practices, testing, CI/CD pipeline, environment strategy, service bootstrap, etc.) unchanged — these are universal and not project-specific.

#### 8b: Populate config.md

Read the PRD generated in Step 6 and the rebuild candidate selected in Step 5. Write the matching values into the developer agent's `config.md` (path provided by the runner), replacing the placeholder values:

**Project section:**
- **Project Name** — from the PRD title
- **Repository** — from the PRD's Target Repository (the new repo, not the legacy repo)
- **Primary Language** — from the PRD's Technical Approach / Tech Stack
- **Framework** — from the PRD's Technical Approach / Tech Stack
- **Cloud Provider** — from the PRD's Technical Approach (GCP or AWS)

**Development Commands section:**
- Pre-fill commands based on the language/framework. For example, a Python/FastAPI project gets `pip install -r requirements.txt` for install, `pytest` for tests, `pylint src tests` for lint, `black --check .` for format, `docker build` for container build. A Go/Gin project gets `go mod download`, `go test ./...`, `golangci-lint run`, etc.

**CI/CD section:**
- **Pipeline Tool** — infer from the PRD or default to GitHub Actions
- **Container Registry** — infer from cloud provider (GCR/Artifact Registry for GCP, ECR for AWS)
- **Image Tag Strategy** — always commit SHA

**Environments section:**
- Pre-fill the environment table with dev/staging/prod rows
- Set Terraform workspace/directory based on the project structure

**Terraform section:**
- **State Backend** — `gs://` for GCP, `s3://` for AWS, with project name placeholder
- **Terraform Directory** — default to `terraform/`
- **Variable Files** — default to `envs/dev.tfvars`, `envs/staging.tfvars`, `envs/prod.tfvars`

**Services section:**
- Pre-fill the service table with service names from the PRD's architecture description (e.g., api, worker, web)

**SRE Agent Integration section:**
- Set the SRE Agent Config path to `../sre-agent/config.md`
- Pre-fill Service Registry entries based on the services identified above

Leave sections that require runtime-specific information as placeholders with clear `[TODO]` markers:
- Secrets (specific secret manager keys)
- Monitoring (dashboard URLs, PagerDuty service IDs)
- External dependencies (specific third-party docs links)
- Environment URLs (not known until infrastructure is provisioned)

This ensures the developer agent has working project-level configuration before the first line of code is written — not populated piecemeal as teams discover what's missing.

#### 8c: Generate IDE instruction files and place configs in the built repo

The developer agent only works if the IDE can find the instruction files **at the root of the repository the developer opens**. This step ensures every built repo is self-contained — a developer clones it, opens it in any supported IDE, and the agent prompt loads automatically.

**You must create the following files inside the built repository directory** (the repo that will be cloned by developers — e.g., `automate-v3/`, not the project working directory):

| IDE | File | Location in built repo | Auto-load mechanism |
|---|---|---|---|
| **Windsurf** | `.windsurfrules` | repo root | Read on every Cascade session start |
| **VS Code + GitHub Copilot** | `.github/copilot-instructions.md` | `.github/` at repo root | Included in every Copilot Chat interaction |

Both files contain the same instruction: read `{lang}-developer-agent/skill.md`, `{lang}-developer-agent/config.md`, and `template/skill.md` before doing any work. Copy the content from the templates in the project's `{lang}-developer-agent/` directory.

> **Critical:** `template/skill.md` **must** be in the `.windsurfrules` required reading list — not just the developer agent files. This is the only mechanism that guarantees the template compliance checklist is read in every session. Without it, agents will follow the developer agent's coding standards but skip the template's structural requirements (Dockerfile pattern, entrypoint pattern, environment-check, Helm charts, CI pipeline jobs, required files, etc.). This was the root cause of missed compliance in the evergreen-tvevents rebuild.

**You must also copy the populated `{lang}-developer-agent/` configs and the template repo's `skill.md` into the built repo:**

| File | Source (project working dir) | Destination (built repo) |
|---|---|---|
| `skill.md` | `{lang}-developer-agent/skill.md` | `<repo>/{lang}-developer-agent/skill.md` |
| `config.md` | `{lang}-developer-agent/config.md` | `<repo>/{lang}-developer-agent/config.md` |
| `skill.md` | `template/skill.md` | `<repo>/template/skill.md` |

**Checklist — all five files must exist in the built repo root:**

- [ ] `<repo>/.windsurfrules` — points to `{lang}-developer-agent/skill.md`, `{lang}-developer-agent/config.md`, and `template/skill.md`
- [ ] `<repo>/.github/copilot-instructions.md` — same content as `.windsurfrules`
- [ ] `<repo>/{lang}-developer-agent/skill.md` — populated with project-specific values (from Step 8a)
- [ ] `<repo>/{lang}-developer-agent/config.md` — populated with project-specific values (from Step 8b)
- [ ] `<repo>/template/skill.md` — copied from the cloned template repo. The QA agent validates every checkbox in this file during verification. Do not remove it post-rebuild.

Without these files in the built repo, the developer agent prompt is not loaded — developers would have to manually paste it into every session. **This is the most common gap in previous rebuilds.** The configs get written to the project working directory but never placed inside the repo that developers actually clone.

**This is the mechanism that makes auto-loading work.** Each IDE has its own convention for project-level instructions. The SRE agent has an equivalent mechanism (`agent.py` reads `skill.md` from disk and sends it as the system prompt). The developer agent relies on IDE instruction files to achieve the same guarantee for human development sessions.

> **Note:** For cross-tool compatibility, `AGENTS.md` at the repo root provides the same instructions for tools that support it (Claude Code, etc.). See the IDE Compatibility section in `README.md` for supported IDEs.

#### 8d: Populate QA Agent Configuration

The QA agent verifies that the developer agent's output meets quality standards. It does **not** replace the developer agent — it is a check on it. The QA agent reads the same `{lang}-developer-agent/skill.md` and `{lang}-developer-agent/config.md` as the developer; `{lang}-qa-agent/skill.md` adds the verification procedures and acceptance criteria.

Read the PRD generated in Step 6 and the developer agent config populated in Steps 8a–8b. Write the matching values into the QA agent's `config.md` (path provided by the runner), replacing the `[TODO]` placeholders:

**Project section:**
- **Project Name** — from the PRD title (same as `{lang}-developer-agent` config)
- **Repository** — from the PRD's Target Repository
- **Original Legacy Repo** — the legacy repo being rebuilt

**Required Environment Variables for Tests:**
- Pre-fill the test env var table with every variable from the project's `environment-check.sh` `always_required_vars` array, plus app-specific variables. Each gets a safe test default value.

**Acceptance Criteria — App-Specific:**
- **API Endpoints to Verify** — list every endpoint from the PRD or `{lang}-developer-agent` config (method, path, expected status code)
- **Event Types to Verify** — list every event type the service handles with validation rules and output shape
- **Environment Variable Mapping** — document all renames from the original legacy service (e.g., `FLASK_ENV` → removed, `RDS_HOST` → same)

**External Dependency Mocking:**
- Map each infrastructure dependency (RDS, Kafka, Redis, etc.) to its mock strategy in tests

Leave the Comparison Checklist items unchecked — the QA agent checks them off during verification.

**Copy the populated `{lang}-qa-agent/` into the built repo:**

| File | Source (project working dir) | Destination (built repo) |
|---|---|---|
| `skill.md` | `{lang}-qa-agent/skill.md` | `<repo>/{lang}-qa-agent/skill.md` |
| `config.md` | `{lang}-qa-agent/config.md` | `<repo>/{lang}-qa-agent/config.md` |
| `TEST_RESULTS_TEMPLATE.md` | `{lang}-qa-agent/TEST_RESULTS_TEMPLATE.md` | `<repo>/{lang}-qa-agent/TEST_RESULTS_TEMPLATE.md` |
| `examples/` | `{lang}-qa-agent/examples/` | `<repo>/{lang}-qa-agent/examples/` |

The QA agent is activated on demand (via the `/qa` Windsurf workflow or during Step 12), not auto-loaded on every session. Human operators customize `{lang}-qa-agent/config.md` with project-specific acceptance criteria after the initial population.

### Step 9: Architecture Decision Records

Generate the initial ADRs identified in the PRD's "ADRs Required" section. Write each ADR to the `docs/adr/` directory (path provided by the runner) using the naming convention `NNN-<short-title>.md` (e.g., `001-use-postgresql.md`).

Each ADR uses this structure:

```
# ADR NNN: [Decision Title]

## Status

Accepted

## Context

[What is the situation? What forces are at play? What problem does this decision address?]

## Decision

[What is the decision that was made?]

## Alternatives Considered

[What other options were evaluated? Why were they rejected?]

## Consequences

[What are the positive and negative outcomes of this decision? What trade-offs were accepted?]
```

For each ADR:
- **Context** comes from the legacy assessment (Step 1), the modernization opportunities (Step 3), and the PRD (Step 6)
- **Decision** comes from the rebuild candidate (Step 5) and the PRD
- **Alternatives Considered** should reference at least one alternative from the rebuild candidates or feasibility analysis
- **Consequences** should be honest about trade-offs — if the decision has downsides, state them

At minimum, generate ADRs for:
- **Cloud provider** — GCP vs AWS choice and rationale
- **Primary database** — engine, managed service, and why
- **Backend language and framework** — what was chosen and why it fits the team and workload
- **Container orchestration** — Kubernetes, Cloud Run, ECS, or other, and why

If the rebuild involves a cloud provider migration (identified in scope.md and the PRD's Infrastructure Migration Plan), also generate ADRs for:
- **Cloud migration rationale** — why the organization is changing providers, what alternatives were considered (staying on current provider, multi-cloud, hybrid), and what trade-offs were accepted
- **Cross-cloud connectivity** — how the rebuilt app connects to dependencies that remain on the original provider, what connectivity option was chosen (VPN, interconnect, public API) and why
- **Managed service mapping** — for each managed service being replaced (e.g., RDS → Cloud SQL), why the target equivalent was chosen and what compatibility risks exist

Additional ADRs depend on the PRD's "ADRs Required" list. Generate every ADR listed there.

**ADR Index (parallel execution only):** When running as a W2 sub-agent, also
generate `docs/adr/adr-index.yaml` — a machine-readable mapping from decision
topics to ADR numbers. Step 11a uses this index for deterministic cross-reference
insertion (no fuzzy NLP matching required). Format:

```yaml
# Auto-generated by Step 9. Used by Step 11a Check 7 for cross-reference insertion.
adrs:
  - number: "ADR-001"
    title: "Use GCP as Cloud Provider"
    prd_sections: ["Technical Approach", "Infrastructure Migration Plan"]
    topics: ["cloud provider", "GCP", "cloud-agnostic"]
  - number: "ADR-009"
    title: "Replace ZeroMQ with DAPR Pub/Sub"
    prd_sections: ["Non-Goals #3"]
    topics: ["DAI", "ZeroMQ", "DAPR pub/sub"]
```

Each entry maps: ADR number, title, the PRD sections that motivated it, and
short topic keywords that other artifacts might use to describe the same
decision. This file is consumed only by Step 11a — it is not a deliverable.

### Step 10: Feature Parity Matrix

Using the legacy assessment (Step 1), the PRD (Step 6), and the rebuild candidate (Step 5), produce a complete feature parity matrix. Write it to `docs/feature-parity.md` (path provided by the runner).

Catalog every user-facing feature, integration, and workflow discovered in the legacy application. For each feature:

- **Feature** — name of the feature or workflow
- **Legacy Behavior** — how it works today (be specific — not just "user login" but "username/password login with session cookie, no MFA, no OAuth")
- **Status** — one of: Must Rebuild, Rebuild Improved, Intentionally Dropped, Deferred
- **Target Behavior** — how it should work after the rebuild (from the PRD)
- **Acceptance Criteria** — how you verify the feature works in the rebuilt system
- **Notes** — phase, dependencies, or migration considerations

Use this structure:

```
# Feature Parity Matrix

> Complete list of every user-facing feature, integration, and workflow in the legacy application.
> Each feature gets a status. The rebuild is not complete until every **Must Rebuild** and **Rebuild Improved** feature passes acceptance testing.

## Features

| Feature | Legacy Behavior | Status | Target Behavior | Acceptance Criteria | Notes |
|---|---|---|---|---|---|
| [feature] | [current behavior] | [status] | [target behavior] | [how to verify] | [notes] |

### Status Definitions

- **Must Rebuild** — feature must exist in the target with equivalent behavior
- **Rebuild Improved** — feature will be rebuilt with specific improvements
- **Intentionally Dropped** — feature will not be rebuilt (requires documented justification below)
- **Deferred** — feature will be rebuilt in a later phase

## Intentionally Dropped — Justifications

| Feature | Justification |
|---|---|
| [feature] | [why it is being dropped] |

## Integrations

| Integration | Legacy Mechanism | Status | Target Mechanism | Notes |
|---|---|---|---|---|
| [integration] | [current mechanism] | [status] | [target mechanism] | [notes] |
```

Rules:
- Every feature must have a status. No unknowns.
- Features marked **Intentionally Dropped** require a justification in the Justifications table.
- Include integrations (external APIs, webhooks, data feeds) as a separate section.
- The matrix must be complete enough to serve as the acceptance checklist for the rebuild.

**Library Transition Mapping:**

When the rebuild replaces a shared library (e.g., cnlib → cntools-dapr, cncontrol → absorbed into target modules), the feature parity matrix must include a **Library Transitions** section that explicitly maps every function or module consumed from the legacy library to its replacement in the target. This prevents the summary of work or dependency cleanup from using language like "removed [library]" without explanation — which creates the impression that functionality was lost.

For each legacy library consumed by the application:

```
## Library Transitions

| Legacy Library | Legacy Function/Module | Target Replacement | Confirmed |
|---|---|---|---|
| [library name] | [function or module used by this app] | [target library or module that provides the same functionality] | [Yes / No — verified in target codebase] |
```

Rules for library transitions:
- **Never say "removed" without a replacement.** If a library is replaced, the replacement must be named explicitly. Use language like "replaced by [target]" or "functionality provided by [target]", not just "removed".
- **Every function consumed must be mapped.** If the legacy app imports `hash_mac()` from cnlib, the matrix must show where that function lives in the target (e.g., `cntools-dapr utils.token_hash.hash_mac()`).
- **Uncertain replacements must be flagged.** If a replacement is not yet confirmed, use "No" in the Confirmed column and add an acceptance criterion. Do not use hedging language like "if supported" in the target behavior column — either confirm the replacement exists or flag it as a gap.

### Step 11: Data Migration Mapping

Using the legacy assessment's Data Health section (Step 1) and the PRD's Data Migration Plan (Step 6), produce the schema mapping between legacy and target. Write it to `docs/data-migration-mapping.md` (path provided by the runner).

Document every table, column, and transformation. For each mapping:

- **Legacy Table / Column / Type** — the source schema as it exists today
- **Target Table / Column / Type** — the target schema from the PRD
- **Transformation** — what changes during migration (type conversion, rename, split, merge, computed, dropped)

Use this structure:

```
# Data Migration Mapping

> Schema mapping between the legacy application and the target system.

## Source: [Legacy Database Engine and Name]

| Legacy Table | Legacy Column | Type | Target Table | Target Column | Type | Transformation |
|---|---|---|---|---|---|---|
| [table] | [column] | [type] | [table] | [column] | [type] | [description or "direct copy"] |

## Mapping Notes

- [Schema changes, type conversions, or data transformations]
- [Columns intentionally dropped and why]
- [New columns in the target that have no legacy equivalent]

## Edge Cases

- [Null handling — how are legacy nulls treated in the target?]
- [Encoding — character set conversions, timezone handling]
- [Truncation — fields that change max length]
- [Default values — what fills new required columns for migrated rows?]

## Reconciliation Queries

> Queries to validate data integrity after migration.

| Check | Legacy Query | Target Query | Expected |
|---|---|---|---|
| Total row count per table | [query] | [query] | Match |
| [additional checks] | [query] | [query] | [expected result] |
```

Rules:
- Every legacy table and column must appear in the mapping. Nothing is silently dropped.
- If a column is intentionally dropped, document it in Mapping Notes with justification.
- If the legacy schema cannot be fully determined from the provided input, state what is known and flag gaps.
- Reconciliation queries must be concrete enough to run against real databases — not pseudocode.

### Step 11a: Cross-Artifact Consistency Check

After Steps 7–11 complete (whether run in parallel or sequentially), verify
cross-artifact coherence before proceeding to the Build phase. This step
catches terminology drift, naming mismatches, and reference errors that can
occur when artifacts are produced independently.

**Check 1: Service Name Consistency**
- Extract service names from: `prd.md` (Technical Approach), `sre-agent/config.md` (Service Registry), `{lang}-developer-agent/config.md` (Services table), `docs/feature-parity.md` (if service-scoped features exist)
- All must use identical names. Flag any mismatches and normalize to the PRD's names.

**Check 2: Endpoint Inventory**
- Extract all API endpoints from the PRD's API Design section
- Verify every endpoint appears in: `docs/feature-parity.md` (as a feature or integration), `sre-agent/config.md` (if `/ops/*` endpoints are listed)
- Flag any endpoint in one document but missing from another.

**Check 3: Technology Stack Alignment**
- Compare the tech stack entries in: `prd.md`, `sre-agent/skill.md`, `sre-agent/config.md`, `{lang}-developer-agent/skill.md`, `{lang}-developer-agent/config.md`
- All must reference the same language, framework, database, cache, and cloud provider. Flag any version or name discrepancies.

**Check 4: Data Schema Coherence**
- If `docs/data-migration-mapping.md` references target tables or columns, verify they align with the PRD's Data Migration Plan and the database technology in the ADRs.
- Flag any target schema references in the mapping that contradict the PRD.

**Check 5: ADR Cross-References**
- Each ADR should reference the PRD section that motivated it
- The PRD's "ADRs Required" list should match the ADRs actually generated in `docs/adr/`
- Flag any PRD-listed ADR that was not generated, or any generated ADR not listed in the PRD.

**Check 6: Terminology Consistency**
- Scan all generated artifacts for domain terms (identified in Step 2's Component Overview)
- Flag cases where the same concept uses different names across documents (e.g., "device token" in one doc vs. "auth token" in another when referring to the same thing)

**Check 7: Cross-Artifact Navigation Links (parallel execution only)**

When Steps 7–11 ran in parallel, sub-agents could not reference each other's
outputs by name or number. This check reconciles those references:

- **ADR number insertion:** Read `docs/adr/adr-index.yaml` (generated by
  Step 9). Scan `docs/feature-parity.md` and `docs/data-migration-mapping.md`
  for decision references that describe PRD sections or use topic keywords
  from the index. Use the index for deterministic matching — look up the
  `prd_sections` and `topics` fields to find the corresponding ADR number,
  then insert it as a cross-reference (e.g., "DAI dropped — see ADR-009").
  This avoids fuzzy NLP matching: if a reference matches an index entry's
  `prd_sections` or `topics`, insert the ADR number; if no index entry
  matches, leave the reference as-is and flag it for manual review.
- **Forward references in ADRs:** Scan ADRs for assertions about other W2
  outputs (e.g., "the Library Transitions table in feature-parity.md maps
  every function"). Verify the assertion is true. If the referenced content
  exists, keep the reference. If it does not exist, reword to remove the
  assertion.
- **Navigational links:** Add "Related Documents" cross-links between W2
  artifacts where appropriate (e.g., ADRs linking to the feature parity
  entries they affect, data migration mapping linking to relevant ADRs).
- **Agent config ADR references:** Scan `sre-agent/` and `{lang}-developer-agent/`
  config files for ADR number references (e.g., `ADR-008` in TODO comments).
  Replace each with the corresponding PRD section description (e.g.,
  `<!-- TODO: finalize container platform per PRD §Technical Approach -->`).

This check is a lightweight post-processing pass, not a rewrite. The
substantive content of each artifact is unchanged — only navigation and
numbering are reconciled.

**Output:** If all checks pass, state "Cross-artifact consistency check: PASS" and proceed. If any check fails, fix the inconsistency in the affected artifact(s) before proceeding. Document any fixes made in `output/process-feedback.md`.

### Step 11b: Automated Output Validation (Phase 1)

Run the output validator to confirm every Phase 1 artifact exists and contains
its required sections:

```bash
./rebuild/validate.sh rebuild-inputs/<project> analyze
```

This checks that every file from Steps 1–11 exists, verifies each file contains
the required markdown headings from its template, and flags files that are
suspiciously short (indicating the agent may have produced a truncated version).

**This gate is mandatory.** Do not proceed to Phase 2 until `validate.sh analyze`
reports zero failures. Warnings should be reviewed but do not block.

If `run.sh` is executing the process automatically, validation runs at the end
of the Analyze phase before returning control to the operator.

---

## Phase 2: Build (Steps 12–18)

Steps 1–11a above produce the analysis artifacts, PRD, agent configs, ADRs,
mapping documents, and a verified consistency baseline. Steps 12–18 below are
executed **during the build phase** — after the developer agent has written the
service code. They validate the code against the standards, generate remaining
documentation, and capture process feedback. The `run.sh` runner invokes Steps
1–11a automatically; Steps 12–18 are executed during interactive development
sessions with the developer agent.

### Template Repo Checklist (required before writing code)

> **Before writing any code in the Build phase**, read `template/skill.md` from
> the cloned template repo at `rebuild-inputs/<project>/template/`. This file is
> the authoritative checklist for how the rebuilt service must be structured — it
> defines the required tooling, CI pipeline, Dockerfile pattern, entrypoint and
> environment-check scripts, Helm chart templates, coding practices, and all
> supporting files.
>
> **Complete every checkbox in `template/skill.md` during the Build phase.** Do
> not invent your own tooling, configs, or patterns — match what the template repo
> specifies. If an item does not apply to the target service, mark it N/A with a
> justification.
>
> **Ongoing enforcement:** Step 8c copies `template/skill.md` into the built repo
> and adds it to `.windsurfrules`. This means every subsequent development session
> — not just the initial build — will read the template checklist. This prevents
> drift: if a developer modifies the Dockerfile, entrypoint, CI pipeline, or any
> structural component, the agent will validate it against the template checklist
> automatically.
>
> The template repo is **not** an adjacent repo. Adjacent repos (`adjacent/`) are
> production code dependencies analyzed for integration points. The template repo
> (`template/`) is the build standard — it defines *how* to build, not *what* to
> build. It is never absorbed into the rebuilt service.

---

### Step 12: Developer Agent Standards Compliance Audit

After the code is written, perform a line-by-line compliance check against every requirement in `skill.md`. Do not rely on memory — open the file and check each item.

**Service Bootstrap — Required from First PR (all must pass):**

- [ ] `Dockerfile` — pinned base image (e.g., `python:3.12-slim`, `gcc:12-bookworm`, `golang:1.22-bookworm`), non-root `USER`
- [ ] CI/CD pipeline — must include all stages: lint, test, build, **scan** (container vulnerability), auto-deploy to dev on merge, terraform plan on PR
- [ ] Terraform module — `terraform/` with environment-specific variable files for dev, staging, prod
- [ ] `/health` endpoint — must check critical dependencies and **return 503 if unhealthy** (not always 200)
- [ ] `/ops/*` diagnostic endpoints — verify all 6 exist and return real data: `/ops/status`, `/ops/health` (includes dependency health with latency), `/ops/metrics`, `/ops/config`, `/ops/errors`, `/ops/cache`
- [ ] `/ops/*` remediation endpoints — verify all exist and are functional: `/ops/cache/flush`, `/ops/cache/refresh`, `/ops/circuits`, `/ops/loglevel`, `/ops/log-level`
- [ ] `/ops/metrics` specifically — must be wired to middleware that records every request. Must return real Golden Signals (latency p50/p95/p99, traffic, errors, saturation) and RED metrics (rate, errors, duration). Placeholder zeros are not compliant.
- [ ] OpenAPI spec — auto-generated or checked into repo
- [ ] OpenAPI response models — every endpoint (GET, POST, PUT, DELETE) must declare a Pydantic `response_model`. No bare `dict` returns anywhere.
- [ ] OpenAPI examples — every request body model and response model must have `json_schema_extra` with realistic `examples` so Swagger UI displays typed schemas and pre-filled "Try it out" payloads
- [ ] Unit and API test scaffolding — tests exist and run
- [ ] `.env.example` — all environment variables documented
- [ ] OTEL instrumentation — tracing, metrics (`MeterProvider` configured), and structured logging
- [ ] `README.md` — how to run locally, how to test, how to deploy
- [ ] `.windsurfrules` — exists at **built repo root** (not just the project working directory), instructs Windsurf to read `{lang}-developer-agent/skill.md` and `{lang}-developer-agent/config.md` before any work
- [ ] `.github/copilot-instructions.md` — exists at `.github/` in **built repo root** (not just the project working directory), instructs VS Code + GitHub Copilot to read `{lang}-developer-agent/skill.md` and `{lang}-developer-agent/config.md` before any work
- [ ] `{lang}-developer-agent/skill.md` — exists inside the **built repo** with all placeholders populated
- [ ] `{lang}-developer-agent/config.md` — exists inside the **built repo** with project-specific values filled in
- [ ] `{lang}-qa-agent/skill.md` — exists inside the **built repo** (universal QA standards — not project-specific)
- [ ] `{lang}-qa-agent/config.md` — exists inside the **built repo** with project-specific acceptance criteria filled in (endpoints, event types, env var mapping, mock strategy)
- [ ] `{lang}-qa-agent/TEST_RESULTS_TEMPLATE.md` — exists inside the **built repo**
- [ ] `{lang}-qa-agent/examples/` — exists inside the **built repo** with example test patterns

**QA Agent Verification (independent quality check):**

The QA agent is a second opinion on the developer agent's work. After the developer agent claims compliance, activate the QA agent (via `/qa` workflow) and have it independently verify:

- [ ] Re-run all quality gates (language-appropriate tools per `{lang}-qa-agent/skill.md`) — compare results against the developer agent's `TEST_RESULTS.md`
- [ ] Verify every `/ops/*` endpoint returns the required fields per the SRE contract in `{lang}-qa-agent/skill.md`
- [ ] Verify `environment-check.sh` accounts for every original env var (using the mapping in `{lang}-qa-agent/config.md`)
- [ ] Verify Dockerfile, entrypoint.sh, and Helm chart match template patterns
- [ ] Verify every checkbox in `template/skill.md` has been completed — open the file, walk each item, and confirm it is satisfied by the built code. Mark any N/A items with a justification.
- [ ] Generate an independent `tests/TEST_RESULTS.md` from the QA agent's own gate runs
- [ ] Flag any discrepancies between the developer agent's claims and the QA agent's findings

**CI/CD pipeline rules:**

- [ ] Container scan stage exists (e.g., Trivy) — CRITICAL and HIGH severity block the build
- [ ] Images tagged with commit SHA only — no `latest` tags in any environment
- [ ] Auto-deploy to dev triggers on merge to main (not manual-only)
- [ ] Terraform plan runs on PR and output is posted as a PR comment
- [ ] Sensitive values (credentials, connection strings) are **never** in `.tfvars` files — they come from secrets manager or CI environment variables

**skill.md project-specific sections:**

- [ ] All placeholder lines (marked with `*[...]*`) are filled in with project-specific values
- [ ] Logging and metrics/tracing descriptions are populated (not template text)

**config.md:**

- [ ] Project details, commands, CI/CD, services, dependencies, and secrets sections are populated
- [ ] Environment URLs are filled in for any deployed environments (use `[TODO]` only for environments not yet provisioned)

If any item fails, fix it before proceeding. Do not defer compliance to a follow-up task.

**Quality Gate Verification and Test Results Report:**

After all compliance items pass, run the full quality suite and produce a test results report at `tests/TEST_RESULTS.md`. This file is a machine-verified proof that the codebase passes all quality gates. It must include:

**Core Gates (mandatory — all must pass):**

1. **Tool versions** — Python, pytest, linter, formatter, type checker, and all analysis tool versions used
2. **Codebase metrics** — source file count, source line count, test file count, test line count
3. **pytest output** — full verbose test output (`pytest -v --tb=short`), with pass/fail summary and breakdown by test suite
4. **Linter output** — full lint results (e.g., `pylint src tests`), must show 0 errors
5. **Formatter output** — format check results (e.g., `black --check .`), must show all files formatted
6. **Type checker output** — strict type check results (e.g., `mypy src/`), must show 0 errors

**Extended Gates (mandatory — measured baselines or pass/fail):**

7. **Test coverage** — `pytest-cov` with `--cov-report=term-missing` showing line-level coverage per module. Report overall %, identify modules below 50%, and explain gaps (e.g., "services require running Redis"). Pure logic modules should target ≥80%.
8. **Dependency vulnerabilities** — `pip-audit`. Report all findings. Critical/High CVEs in runtime dependencies must have a documented remediation plan or documented rationale for deferral.
10. **Docstring coverage** — `interrogate src/ -v`. Report coverage percentage. Identify gaps. Public API functions and classes should have docstrings; thin wrappers and internal helpers may be excluded with justification.
11. **Duplicate code (DRY)** — `pylint --disable=all --enable=duplicate-code src/` and `npx jscpd src/ --min-lines 5 --min-tokens 50`. Must show < 3% duplication. Any detected clones must be justified (e.g., intentional structural similarity) or refactored.
12. **Cognitive complexity** — `complexipy src -mx 15`. Must show 0 issues at threshold 15.

**Summary and context:**

13. **Quality gate summary table** — one table showing each gate (tests, lint, format, types, coverage, dead code, vulnerabilities, docstrings, duplication, cognitive complexity), threshold, result, and pass/fail status
14. **Bugs found and fixed** — any source or test bugs discovered during validation, with before/after descriptions
15. **Not yet tested** — anything requiring running infrastructure (integration tests, Docker, DAPR sidecar) that cannot be validated offline

**Required tools** (install in dev environment):
```
pip install pytest-cov pip-audit interrogate pylint complexipy
npx jscpd  # Node.js — for copy-paste detection
```

This file serves as the build's quality receipt. If the report does not exist or shows failures, the build is not complete.

### Step 12a: Template Repository Component Checklist

After the compliance audit passes, verify that **every structural component** from the template repository (`rebuilder-evergreen-template-repo-python`) exists in the built repo. This step catches missing files, directories, and tooling that are part of the organizational standard but not covered by the `{lang}-developer-agent` compliance checks.

**Why this step exists:** During the automate rebuild, several template components were missed — `hooks/pre-commit`, `charts/tests/`, `tests/test-helm-template.sh`, and `cves/` — because the compliance audit only checks `{lang}-developer-agent` standards, not the template repo's full file inventory. This step closes that gap.

**Procedure:**

1. Read the template repository's `README.md` to identify all documented tooling, scripts, and structural conventions.
2. List the template repo's top-level directories and key files.
3. For each item, verify it exists (or has a justified equivalent) in the built repo.

**Required components checklist:**

- [ ] `hooks/pre-commit` — git pre-commit hook running all quality gates (lint, format, test, type check, complexity, helm lint/template/unittest). Adapt source directory names to match the project layout.
- [ ] `charts/` — Helm chart directory with `Chart.yaml`, `values.yaml`, and `templates/` containing all standard templates (Deployment, Service, HTTPRoute, ExternalSecret, Namespace, OtelCollector, PodDisruptionBudget, ScaledObject, ServiceAccount, Dapr, and all helper `_*.tpl` files).
- [ ] `charts/tests/` — Helm unittest YAML files (at minimum: `deployment_test.yaml`, `service_test.yaml`, `httproute_test.yaml`).
- [ ] `tests/test-helm-template.sh` — Script that renders Helm templates across environments (dev, qa, prod, pr) to verify rendering correctness.
- [ ] `cves/` — Directory for VEX (Vulnerability Exploitability Exchange) JSON files. May contain `.gitkeep` if no CVEs have been filed yet.
- [ ] `scripts/lock.sh` — Dependency locking script using `pip-tools` / `pip-compile` with `--generate-hashes`.
- [ ] `scripts/entrypoint.sh` — Container entrypoint script sourcing `environment-check.sh` and starting the application.
- [ ] `scripts/environment-check.sh` or `environment-check.sh` — Environment variable validation script.
- [ ] `.actrc` — Configuration for running GitHub Actions locally with `act` (specifies `--container-architecture linux/amd64`).
- [ ] `env.list` — Example environment variables for local container execution.
- [ ] `monitored-paths.txt` — List of paths that trigger CI pipeline runs.
- [ ] `.pylintrc` — Pylint configuration file.
- [ ] `.python-version` — Python version pinning file.
- [ ] `catalog-info.yaml` — Backstage service catalog descriptor.
- [ ] `docker-compose.yml` — Full local development stack with all infrastructure dependencies (PostgreSQL, Kafka, Redis, etc.), adjacent module mounts, healthchecks, and `depends_on` with `condition: service_healthy`. Must allow `docker compose up --build` to start a working environment.
- [ ] `template/skill.md` — Copied from the cloned template repo (Step 8c). The QA agent validates every checkbox in this file. Must be referenced in `.windsurfrules`.
- [ ] `.github/scripts/pod-identity-generator/` — Pod identity management scripts (create, delete, find).
- [ ] `.github/scripts/workflow-runner.sh` — Dynamic workflow execution helper.

**Required development tooling checklist:**

The template repository mandates the following tools in every rebuilt service. Each must be (a) listed as a dependency in `pyproject.toml` (under `[project.optional-dependencies.dev]` or equivalent), (b) configured (in `pyproject.toml`, `.pylintrc`, or dedicated config files), and (c) runnable with the commands below.

| Tool | Purpose | Template command | Adaptation notes |
|---|---|---|---|
| **pylint** | Static analysis and code quality | `pylint src tests` | Adjust source dirs to match project layout |
| **mypy** | Static type checking | `mypy src/ tests/` | Must run clean (0 errors) on both src and tests |
| **black** | Code formatting | `black src tests` | `black` is the organizational standard formatter. |
| **pytest** | Unit and integration testing | `pytest` | Must include `pytest-cov` for coverage reporting |
| **complexipy** | Cognitive complexity analysis | `complexipy src -mx 15 -d low` and `complexipy tests -mx 15 -d low` | Run separately for src and tests |
| **Helm Unittest** | Helm chart unit testing | `helm unittest ./charts` | Requires helm plugin: `helm plugin install https://github.com/helm-unittest/helm-unittest.git` |
| **Helm lint** | Helm chart validation | `helm lint ./charts` | Must pass with 0 errors |
| **Helm template** | Helm chart rendering verification | `helm template ./charts` | Must render without errors |
| **pip-audit** | Dependency vulnerability scanning | `pip-audit` | Critical/High CVEs must have remediation plan |
| **interrogate** | Docstring coverage measurement | `interrogate src/ -v` | Report coverage percentage |

**Verification:** For each tool in the table above, run the command and confirm it executes without import errors or missing-tool failures. If a tool is not installed, add it to `pyproject.toml` dev dependencies and regenerate locked requirements via `scripts/lock.sh`.

**CI pipeline alignment:** Every tool in the table above must also have a corresponding job or step in the CI pipeline (`.github/workflows/ci.yml`). Cross-reference the CI workflow jobs against this table and flag any tool that runs locally but is missing from CI, or vice versa.

**Pre-commit hook alignment:** The `hooks/pre-commit` script must invoke every tool in the table above (or a justified subset). Cross-reference the pre-commit hook against this table and flag any tool missing from the hook.

**Adaptation rules:**
- Components may be adapted for the specific project (e.g., different service names in `values.yaml`, project-specific source directories in tool commands).
- Components that are genuinely not applicable (e.g., `Dapr.yaml` if the service does not use DAPR) may be omitted with documented justification in `output/process-feedback.md`.
- Components must **not** be silently skipped. If a component is missing, either create it or document why it was omitted.
- Tools must **not** be silently omitted. If a tool from the table is not used, document why in `output/process-feedback.md`.

**Output:** If all components and tooling are present or justified, state "Template component checklist: PASS" and proceed. If any component or tool is missing without justification, create/install it before proceeding.

### Step 13: Documentation–Code Consistency Check

After any code change that adds, removes, or modifies API endpoints, verify that **every document** referencing those endpoints is updated. This includes:

- `README.md` — API endpoint table must list every endpoint with method, path, and description
- `docs/deployment-status.md` (or equivalent) — must have a copy-pastable test command for every endpoint
- `docs/dry-run-testing-guide.md` (or equivalent) — validation commands quick reference must cover all endpoints
- SRE playbooks — any playbook referencing `/ops/*` endpoints must reflect the current set

**Rule:** If an endpoint exists in code but not in docs, or exists in docs but not in code, the build is not complete.

> **Parallel Window W3:** Steps 13a, 14, and 15 share the same inputs (built
> codebase, PRD, Step 12 audit results) and produce independent outputs. If
> sub-agents are available, dispatch all three concurrently. Step 13
> (Documentation–Code Consistency) must complete first since it may trigger
> code changes. Step 13b (Docker Runtime) depends on code being finalized.
> After W3 completes, run **Step 15a: Build Phase Consistency Check**.

### Step 13a: Domain-Realistic Test Scenarios

AI-generated tests often reveal themselves through generic test data (`"abc123"`, `"token"`, `"item-001"`) and class names that describe code paths rather than business flows. An engineer reviewing the test suite should see **domain expertise**, not placeholder-driven coverage.

**Test Data Requirements:**

- Use **realistic identifiers** from the problem domain. If the service handles IoT devices, tests should use real hardware model numbers, MAC-derived token hashes, production-format hostnames, realistic firmware versions, and properly formatted serial numbers. If it handles financial transactions, use realistic account numbers, currency codes, and transaction amounts.
- **Never use `abc123`, `test-token`, `foo`, or `placeholder`** as test identifiers. If the real system processes 32-character hex tokens derived from MAC addresses, the test token should be a 32-character hex string.
- Test data should make the **domain model self-documenting**. A reader should understand what the system processes by reading the test fixtures alone.

**Test Naming and Structure:**

- Test **class names** should describe a real-world scenario, not a code path. Use `TestDeviceCheckinLifecycle` instead of `TestControlEndpoint`. Use `TestNewUserOnboarding` instead of `TestPostEndpoint`.
- Test **method docstrings** should tell the story of a client-to-server interaction: what the caller sends, what the service does, and what response the caller receives. Example: `"""Device sends first check-in → service returns retry interval while provisioning completes."""`
- Test **method names** should describe the scenario from the caller's perspective: `test_new_device_first_checkin_gets_retry_interval` instead of `test_unknown_user_returns_200`.

**Response Validation:**

- Assert on **business-meaningful values**, not just status codes. If a client receives a retry interval, assert the specific interval value. If a client receives a redirect, assert the redirect URL contains the expected target hostname.
- Validate response **shapes** against what the real client (device firmware, admin console, internal service) actually parses. If the client expects an INI-format or XML response, assert structural markers are present.

**Why This Matters:**

Code that uses realistic domain data passes the "engineer review" test — it looks like it was written by someone who understands the problem space, not by an AI that was given a spec. This is the difference between code that a team trusts and code that a team rewrites.

### Step 13b: Docker Runtime Validation

After unit tests pass and code is compliant, validate the full stack runs in Docker. This step catches categories of bugs that unit tests cannot: missing runtime dependencies, configuration mismatches, sidecar connectivity, and data store initialization.

**Pre-flight Checklist:**

1. `docker compose up --build -d` — all containers must start without errors
2. All service containers must reach `healthy` status within their healthcheck `start_period`
3. All sidecar containers (DAPR, Envoy, etc.) must be running
4. All infrastructure containers (Redis, PostgreSQL, OTEL Collector) must be healthy

**Common Docker Runtime Failures (fix before proceeding):**

| Symptom | Root Cause | Fix |
|---|---|---|
| `executable not found in $PATH` (e.g., `opentelemetry-instrument`) | Package installed with `pip install --target` which doesn't create console scripts | Use `pip install --prefix=/install` in Dockerfile build stage |
| Pydantic `SettingsError` on `list[str]` fields | `pydantic-settings` tries to JSON-parse env var strings as lists **before** field validators run | Use `str` type with `@property` that splits on comma |
| Sidecar `TimeoutError` on health check | All services reading same default port from `.env` but each sidecar uses unique ports | Add per-service `DAPR_HTTP_PORT` / `DAPR_GRPC_PORT` overrides in docker-compose.yml |
| Sidecar `NoCredentialProviders` errors | AWS/GCP bindings fail without cloud credentials in local dev | Add `ignoreErrors: true` to DAPR component specs for cloud-only bindings |
| `httpx` / runtime dependency `ImportError` | Package listed in dev-only dependencies but used in production health checks | Move to main `[project.dependencies]` in `pyproject.toml` |
| PostgreSQL `role does not exist` | Seed script uses wrong user/database | Match seed script credentials to `POSTGRES_USER`/`POSTGRES_DB` in docker-compose.yml |

**Seed Data Validation:**

- Seed data scripts (`scripts/seed_data.sh`) must seed **all** data stores — not just the primary database. If the application uses Redis, PostgreSQL, and an S3 bucket, the seed script must populate all three.
- After seeding, verify data exists: `docker compose exec redis redis-cli -n 0 KEYS '*'`

**Smoke Test Validation:**

- Run the integration smoke test (`tests/integration/smoke_test.sh`) against the running stack
- All smoke test endpoints must return expected HTTP status codes
- **Smoke test `curl` commands must not use `-f` (fail) flag** when checking HTTP status codes — the `-f` flag causes `curl` to exit non-zero on 4xx/5xx responses, which triggers the fallback `|| echo "000"` and results in corrupted status codes like `401000` or `400000`

### Step 14: Observability Documentation — Service Metrics vs Application Metrics

Every deployed service has **two distinct types of metrics**. Documentation must explain both and provide query examples for each:

**1. Service metrics (platform-managed)**
- These are infrastructure metrics collected automatically by the platform (Cloud Run, ECS, GKE, etc.)
- Include: CPU utilization, memory utilization, request count, request latency, instance count, network I/O
- Queried via the cloud provider's monitoring API (e.g., `gcloud monitoring time-series list`) or console
- Persist for weeks/months in the provider's monitoring backend

**2. Application metrics (app-instrumented)**
- These are business-logic metrics measured inside the application by middleware
- Include: Golden Signals (latency p50/p95/p99, traffic rate, error rate, saturation) and RED method (rate, errors, duration)
- Queried via `/ops/metrics` (pull-based, on-demand) and optionally exported to Cloud Monitoring via OTEL (push-based, time-series)
- In-process counters reset on instance restart; OTEL-exported metrics persist in the monitoring backend

Documentation must include:
- Example `curl` commands for `/ops/metrics`
- Example `gcloud monitoring` (or equivalent) commands for platform metrics
- A table or explanation distinguishing what each measures and when to use which

### Step 15: Target Architecture Documentation

After completing the code, tests, and observability, produce a standalone
architecture document that describes the **end state** of the rebuilt service.
This document is for architects, team leads, and engineers who need to
understand how the rebuilt system works without reading source code.

Write results to `docs/target-architecture.md` using this structure:

1. **What Changed** — Table mapping each legacy component to its target module.
   Include what each module does. Make the consolidation explicit.

2. **System Architecture** — Full component diagram (mermaid) showing:
   - External callers (TVs, admin tools, internal services)
   - Entry points (load balancer, endpoints grouped by auth model)
   - Domain modules inside the service
   - Shared library layer (if applicable — e.g., cntools-dapr)
   - Infrastructure integration (DAPR sidecar, Redis, Kafka, etc.)
   - Clear separation of what goes through the sidecar vs. direct connections

3. **Data Flow Diagrams** — One mermaid sequence diagram per major request flow.
   Show the caller, the service layer, any library calls, and the data store
   interactions. Include at minimum:
   - The primary read path (most common request)
   - The primary write path
   - Any async/event-driven flows (pub/sub, queues)
   - Any auth-gated flows (admin, internal tools)

4. **Library Relationship** (if applicable) — When the service depends on a
   shared library (e.g., cntools-dapr), explain:
   - How it is consumed (library import vs. HTTP)
   - What it provides (service classes, connection pooling, config, utilities)
   - Why this consumption model was chosen (reference relevant ADR)
   - Diagram showing the in-process boundary between app code and library code

5. **What Changed and What Didn't** — Table comparing legacy vs. target across
   dimensions: deployable units, repos, data stores, URL paths, response
   formats, connection management, message queues, frameworks, auth, shared
   libraries, observability, IaC, containers, health checks, diagnostics.

6. **Deployment Architecture** — Diagram showing the container runtime,
   sidecar, probes, and how the service is exposed.

7. **Features Intentionally Removed** — Table of legacy features not carried
   forward, with justification and ADR reference for each.

8. **Related Documents** — Links to component overview (legacy), feature
   parity, PRD, relevant ADRs, observability docs, and data migration mapping.

**Critical constraint:** This document describes the **target state only** —
what the rebuilt service looks like and how it works. For the legacy state,
reference `docs/component-overview.md`. Do not mix legacy description into
this document beyond the comparison table.

### Step 15a: Build Phase Consistency Check

After Steps 13a, 14, and 15 complete (whether run in parallel or sequentially),
verify that the build-phase documentation is consistent with the code and with
Phase 1 artifacts.

**Check 1: Endpoint Inventory vs. Code**
- Extract all route definitions from the source code (e.g., `@app.get`, `@app.post`, `@router.*`)
- Compare against: `README.md` endpoint table, `docs/target-architecture.md` endpoint lists, SRE playbooks referencing `/ops/*` endpoints
- Flag any endpoint in code but not in docs, or in docs but not in code.

**Check 2: Test Coverage Alignment**
- Verify that every endpoint defined in code has at least one test in the test suite
- Verify that test class/method names follow the domain-realistic naming from Step 13a (no `TestPostEndpoint`, no `test_abc123`)

**Check 3: Observability Documentation vs. Code**
- Verify `/ops/metrics` endpoint returns the Golden Signals and RED metrics documented in Step 14
- Verify middleware metric collection described in Step 14 is actually wired in the application startup

**Check 4: Architecture Documentation vs. Code**
- Verify the module structure in `docs/target-architecture.md` (Step 15) matches the actual directory/module layout
- Verify dependency flow diagrams match actual import relationships

**Output:** If all checks pass, state "Build phase consistency check: PASS" and proceed. If any check fails, fix the inconsistency before proceeding. Document any fixes in `output/process-feedback.md`.

### Step 16: Container Build for Cloud Targets

When building container images for cloud deployment (Cloud Run, ECS, GKE, etc.):

- Always specify `--platform linux/amd64` in `docker build` commands. Developer machines (especially Apple Silicon Macs) build ARM images by default, which fail on cloud platforms that require AMD64.
- This applies to all build contexts: local development builds, CI pipeline builds, and documentation examples.
- The `Dockerfile`, CI pipeline, and deployment documentation must all consistently specify the target platform.

Example:
```bash
docker build --platform linux/amd64 -t <registry>/<service>:<commit-sha> .
```

### Step 17: Process Feedback Capture

At the end of every rebuild session where the operator provided manual corrections, instructions, or clarifications that the process did not cover:

1. List every manual instruction the operator gave
2. For each, identify why the process didn't handle it
3. Propose specific additions to this process document (IDEATION_PROCESS.md) or to the developer agent standards (skill.md) that would prevent the same gap
4. Apply the changes to the process documents after operator approval

**The rebuild process is a living document.** Every manual correction is evidence of a process gap. If an operator has to tell you something that should have been in the process, the process is incomplete.

### Step 18: Summary of Work

After all previous steps are complete, generate a single summary document that communicates the value and scope of the rebuild at a glance. This document is for stakeholders, leadership, and teams evaluating the rebuild approach.

**Gather metrics programmatically.** Count files and lines from both the legacy codebase (`repo/` and any `adjacent/` directories) and the rebuilt codebase. Do not estimate — measure.

Write results to `output/summary-of-work.md` using this structure:

```
# Summary of Work: [Application Name]

> **Reference document.** This is a summary generated during the ideation process. It informs decisions but does not override {lang}-developer-agent/skill.md.

## Overview

[Two-column layout using an HTML table. Left column (55%) contains the 3
executive summary paragraphs. Right column (45%) contains the Key Numbers table.
This keeps the narrative and metrics side-by-side so executives see both at a
glance without scrolling.]

<table>
<tr>
<td width="55%" valign="top">

[Paragraph 1: What the legacy application was, its problems, and why it needed
rebuilding.]

[Paragraph 2: How the rebuild was executed (spec-driven automated process).]

[Paragraph 3 ("Bottom line"): Synthesize three things for a non-technical reader:
(1) how long the rebuild would take a human engineer, (2) how long it actually
took with AI-driven automation, and (3) why the rebuilt codebase is more
maintainable going forward (reduced lines, type safety, automated quality gates,
observability, CI/CD enforcement).]

</td>
<td width="45%" valign="top">

**Key Numbers**

[Summary table of headline metrics. Include: source lines eliminated, code
reduction %, dependencies removed, compliance checks passed, quality gates
passed, test coverage, CVEs, new endpoints, ADRs, total files. Measure
programmatically — do not estimate. Keep metric labels concise for column fit.]

| Metric | Value |
|--------|-------|
| Source lines eliminated | [n] |
| Source code reduction | [n%] |
| ... | ... |
| Total files delivered | [n] |

</td>
</tr>
</table>

### Estimated Human Time Equivalent

[Grounded human time estimate with **two engineer profiles**: a senior engineer
already familiar with the legacy codebase ("Familiar Engineer") and an engineer
new to the codebase who must first build context ("Unfamiliar Engineer"). Both
assume full-time work (8h days). This dual-column format is required for every
rebuild to give stakeholders an honest range.

Use this exact table structure:]

| Phase | Deliverables | Familiar Engineer | Unfamiliar Engineer | Basis |
|-------|-------------|-------------------|---------------------|-------|
| **Legacy analysis** (Steps 1–3) | [artifacts produced] | **[n–n days]** | **[n–n days]** | [justification with LOC counts, file counts, domain complexity. Cite review rate references.¹] |
| **Architecture & design** (Steps 4–8) | [artifacts produced] | **[n–n days]** | **[n–n days]** | [justification citing ADR count, PRD complexity, agent config work. Explain why unfamiliar takes longer.²] |
| **Feature parity & data mapping** (Steps 9–10) | [artifacts produced] | **[n–n days]** | **[n–n days]** | [justification citing feature count, data store complexity, library transition mapping.] |
| **Implementation** | [file count, line count, module count] | **[n–n days]** | **[n–n days]** | [justification citing production LOC and productivity references.³] |
| **Testing** | [test file count, test count, quality gate count] | **[n–n days]** | **[n–n days]** | [justification citing test LOC, fixture design complexity, quality gate configuration.⁴] |
| **Compliance & docs** (Steps 11–16) | [audit scope, doc count] | **[n–n days]** | **[n–n days]** | [justification citing compliance check count, cross-referencing effort.] |
| **Total** | **[total files]** | **[n–n days]** | **[n–n days]** | **[~n–n weeks (familiar) / ~n–n weeks (unfamiliar)]** |

[After the table, state:]
- The AI-driven pipeline compressed this into [timeframe] of human oversight
- **Estimated acceleration:** [n–n×] for familiar, [n–n×] for unfamiliar
- Human role shifted from execution to review and judgment

[Include numbered footnotes citing industry estimation frameworks. Required citations:]

> ¹ McConnell, Steve. *Code Complete* (2004), Ch. 20 — code review rates
> and unfamiliarity overhead.
>
> ² Jones, Capers. *Applied Software Measurement* (2008) — architectural
> decision productivity and domain familiarity impact.
>
> ³ Jones, Capers. *Applied Software Measurement* (2008) — lines per day
> for experienced (100–150) vs. unfamiliar (50–80) engineers.
>
> ⁴ Meszaros, Gerard. *xUnit Test Patterns* (2007) — test design effort
> multiplier for services with external dependencies.

[Do not use a single "Engineer-Days" column. The dual-column format is mandatory
to show stakehold­ers the range of effort depending on team familiarity. This
ensures consistency across all rebuild summaries.]

## Spec-Driven Approach

[Table showing each step in the IDEATION_PROCESS.md that was executed and what
artifact it produced. Emphasize that all specifications, architecture decisions,
and compliance standards were defined before code was written.]

| Step | Name | Output |
|---|---|---|
| 1 | Legacy Assessment | output/legacy_assessment.md |
| 2 | Component Overview | docs/component-overview.md |
| ... | ... | ... |

## Source Code Metrics

### Legacy Codebase
| Metric | Value |
|---|---|
| Source files | [count from repo/ and adjacent/] |
| Total lines | [count] |
| Test files | [count] |
| Test lines | [count] |

### Rebuilt Codebase
| Metric | Value |
|---|---|
| Source files | [count] |
| Total lines | [count] |
| Test files | [count] |
| Test lines | [count] |

### Comparison
| Metric | Legacy | Rebuilt | Change |
|---|---|---|---|
| Source files | [n] | [n] | [% change] |
| Source lines | [n] | [n] | [% change] |
| Test files | [n] | [n] | [% change] |
| Largest file (lines) | [name: n] | [name: n] | [comparison] |

## Dependency Cleanup

### Removed
| Dependency | Issue | Replacement |
|---|---|---|
| [name] | [reason — e.g., deprecated since YYYY, unmaintained, Python 2 compat] | [what replaced it — e.g., "cntools-dapr (MCPService, TVCService, etc.)" or "functionality absorbed into target modules". **Never leave blank** — every removed dependency must state its replacement or "No replacement needed (dead code)".] |

### Current
| Dependency | Version | Purpose |
|---|---|---|
| [name] | [version] | [what it does] |

| Metric | Legacy | Rebuilt |
|---|---|---|
| Runtime dependencies | [n] | [n] |
| Pinned versions | [Yes/No] | [Yes/No] |

## Legacy Health Scorecard

[Reproduce the ratings from the legacy assessment. Show baseline state.]

| Dimension | Rating |
|---|---|
| Architecture Health | [rating] |
| API Surface Health | [rating] |
| Observability & SRE | [rating] |
| Auth & Access Control | [rating] |
| Code & Dependency Health | [rating] |
| Operational Health | [rating] |
| Data Health | [rating] |
| Developer Experience | [rating] |
| Infrastructure Health | [rating] |
| External Dependencies | [rating] |

## New Capabilities

[Table of everything the rebuilt application has that the legacy did not.]

| Capability | Legacy | Rebuilt |
|---|---|---|
| HTTP API | [status] | [status] |
| OpenAPI Spec | [status] | [status] |
| Structured Logging | [status] | [status] |
| Distributed Tracing | [status] | [status] |
| Health Checks | [status] | [status] |
| Container Image | [status] | [status] |
| Infrastructure as Code | [status] | [status] |
| CI/CD Pipeline | [status] | [status] |
| SRE Diagnostic Endpoints | [status] | [status] |
| [additional capabilities] | ... | ... |

## Compliance Result

[Summary from the Developer Agent Standards Compliance Audit (Step 12).]

| Category | Checks | Passed | Failed |
|---|---|---|---|
| [category] | [n] | [n] | [n] |
| ... | ... | ... | ... |
| **Total** | **[n]** | **[n]** | **[n]** |

## Extended Quality Gate Results

[Summary from the Quality Gate Verification and Test Results Report (`tests/TEST_RESULTS.md`) produced in Step 12. Include both core and extended gates.]

**Core Gates (all must pass):**

| Gate | Tool | Threshold | Result | Status |
|---|---|---|---|---|
| Unit Tests | pytest | 0 failures | [n passed, n failed] | [PASS/FAIL] |
| Lint | pylint | 0 errors | [n errors] | [PASS/FAIL] |
| Format | black | 0 unformatted | [n/n formatted] | [PASS/FAIL] |
| Type Check | mypy (strict) | 0 errors | [n errors in n files] | [PASS/FAIL] |

**Extended Gates (measured baselines):**

| Gate | Tool | Threshold | Result | Status |
|---|---|---|---|---|
| Test Coverage | pytest-cov | measured | [n% overall] | [MEASURED] |
| Dependency Vulnerabilities | pip-audit | 0 critical/high | [n CVEs] | [PASS/FLAGGED] |
| Docstring Coverage | interrogate | measured | [n%] | [MEASURED] |
| Duplicate Code (DRY) | pylint + jscpd | < 3% duplication | [n% duplication] | [PASS/FAIL] |
| Cognitive Complexity | complexipy | 0 issues | [n issues] | [PASS/FAIL] |

[Include brief notes on coverage gaps (e.g., "services require running infrastructure"), any flagged vulnerabilities with remediation plan, and any justified exceptions (e.g., intentional structural similarity in clone detection).]

**Full machine-verified output:** [`tests/TEST_RESULTS.md`](../[built-repo]/tests/TEST_RESULTS.md)

## Architecture Decisions

[Summary table of all ADRs produced.]

| ADR | Title | Decision | Key Trade-off |
|---|---|---|---|
| 001 | [title] | [chosen option] | [what was traded] |
| ... | ... | ... | ... |

## File Inventory

[Tree view of all delivered files, organized by category.]

### Source
[file tree]

### Tests
[file tree]

### Infrastructure
[file tree]

### Documentation
[file tree]
```

### Step 18a: Automated Output Validation (Phase 2)

After Step 18, run the full output validator to confirm every artifact from both
phases exists and contains its required sections:

```bash
./rebuild/validate.sh rebuild-inputs/<project> all
```

This is the final gate. It checks:
- Every file from Steps 1–18 exists at its expected path
- Every file contains the required markdown headings from its template
- `summary-of-work.md` has all 14 required sections (Overview, Estimated Human
  Time, Spec-Driven Approach, Source Code Metrics, Dependency Cleanup, Legacy
  Health Scorecard, New Capabilities, Compliance Result, Extended Quality Gate
  Results, Architecture Decisions, File Inventory)
- `TEST_RESULTS.md` has core and extended quality gate sections
- Files meet minimum length thresholds (catches truncated agent output)

**The rebuild is not complete until `validate.sh all` reports zero failures.**

If any step was missed or any output is structurally incomplete, fix it before
declaring the rebuild done. This prevents the exact failure mode where an agent
produces a shortened version of a template-specified document.

## Process Rules

- **No hypotheticals.** Every opportunity must trace to a real pain point or assessment finding.
- **No invented data.** If you cannot determine something from the provided input, say so. Do not fabricate metrics.
- **No gold-plating.** The goal is to rebuild what's needed, not redesign the perfect system. Resist scope creep.
- **Preserve what works.** Not everything needs to change. Identify and protect the parts of the legacy app that are solid.
- **Kill fast.** If an opportunity fails feasibility, drop it. Do not rehabilitate weak candidates.
- **Speed over perfection.** This process should take minutes, not days. Parallel execution windows reduce wall-clock time without sacrificing quality.
- **Consistency after concurrency.** Any time steps run in parallel (W1, W2, W3), the subsequent consistency check is mandatory — not optional. Artifacts produced independently must be verified as coherent before downstream steps consume them.
- **Validate after each phase.** Run `rebuild/validate.sh` after Phase 1 (Step 11b) and after Phase 2 (Step 18a). Do not proceed past a phase boundary or declare completion with validation failures outstanding.

