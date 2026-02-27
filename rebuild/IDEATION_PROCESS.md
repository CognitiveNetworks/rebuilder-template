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

Execute the following steps sequentially. Do not ask for approval between steps. Run the entire process and write all output files when complete.

### Step 1: Legacy Assessment

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

**Audience:** Someone who has never seen the codebase. Write in plain language. Avoid code snippets. Define domain terms where first used.

**Required Sections:**

1. **What Is This?** — One-paragraph plain-language summary of what the component does.
2. **Why Does It Exist?** — Business context: what problem it solves and why the platform needs it.
3. **Key Concepts** — Domain glossary explaining terms that appear throughout the codebase (e.g., tokens, zoos, UMPs, CDB). Each concept gets a heading with a 2-3 sentence definition.
4. **What It Does** — Description of each major functional area or domain module. For each, state its purpose, what data it manages, and who uses it. Written for comprehension, not as an API reference.
5. **Pure Utility Functions** (if applicable) — Table of standalone functions with plain-language descriptions. Note that these have no infrastructure dependencies.
6. **CLI Tools** (if applicable) — Table of command-line entry points with descriptions.
7. **How It Fits in the Platform** — ASCII diagram showing where this component sits relative to upstream and downstream systems, with a narrative data flow summary.
8. **How Teams Consume It** — Table of consumption modes (library import, API call, event subscription, etc.) with audience and prerequisites for each.
9. **Technology** — Table of current stack choices with brief notes.
10. **Deployment** — How the application is currently deployed, configured, and operated.
11. **Known Limitations** — Table of current limitations and gaps (from the legacy assessment findings).
12. **Codebase** — Repository link, approximate size, package structure, dependency count.

**Guidance:**
- Keep it under 300 lines — this is an overview, not a specification.
- Include at least one ASCII architecture diagram.
- Domain terms should be defined where first used, not assumed.
- Draw from the legacy assessment findings, `scope.md`, `input.md`, and the source code.

Write results to `docs/component-overview.md` inside the rebuilt application directory.

### Step 3: Modernization Opportunities

Using the legacy assessment and the pain points from scope.md, identify the top modernization opportunities.

An opportunity qualifies ONLY if:
- It directly addresses a pain point identified in scope.md or discovered in Steps 1-2
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

Write results to `output/modernization_opportunities.md`.

### Step 4: Feasibility Analysis

For each modernization opportunity rated High or Critical impact, validate:

1. **Effort:** Can this be completed by the team described in scope.md within the stated constraints? Estimate in t-shirt sizes (S/M/L/XL) with rationale.
2. **Risk:** What could go wrong? Data loss, downtime, feature regression, integration breakage. Rate: Low / Medium / High.
3. **Dependencies:** Does this block or get blocked by other opportunities? What order should things happen?
4. **Rollback:** If this fails, can you revert? How?

**Feasibility verdict per opportunity:** Go / Caution / No-Go. No-Go opportunities do not become rebuild candidates.

Write results to `output/feasibility.md`.

### Step 5: Rebuild Approach Candidates

For each feasible opportunity (or logical grouping of related opportunities), create a separate output file: `output/candidate_N.md` where N is 1, 2, 3, etc.

Each candidate file uses this structure:

```
# Rebuild Candidate: [Working Title]

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
- Tightly Coupled: [Yes/No — if Yes, scope escalation required per WINDSURF.md Dependency Boundaries]
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

### Step 7: SRE Agent Configuration

After the PRD is generated, update the SRE agent's tech stack to match the chosen rebuild candidate.

**⚠️ STRICT TEMPLATE POPULATION RULES — apply to both WINDSURF_SRE.md and config.md:**

1. **PRESERVE EVERY SECTION.** Do not delete, merge, skip, or summarize any section from the template. Every heading, table, list, and block must appear in the output.
2. **ONLY REPLACE PLACEHOLDERS.** Find text wrapped in `*[brackets]*` or `[brackets]` and replace it with the real value. Do not rewrite surrounding prose.
3. **DO NOT REPHRASE.** Keep all instructional comments (lines starting with `>`) exactly as they are. Do not reword them.
4. **DO NOT ADD SECTIONS.** If the template doesn't have a section for something, don't invent one.
5. **KEEP FORMATTING IDENTICAL.** Markdown heading levels, table column counts, list styles, code block languages — all must match the template exactly.
6. **IF A VALUE IS UNKNOWN**, leave the placeholder as-is and add a TODO comment: `<!-- TODO: fill after infra provisioning -->`.
7. **DIFF CHECK.** After generating the output, mentally diff it against the template. The only differences should be placeholder values replaced with real values. If any structural difference exists, fix it before writing the file.

Read the Tech Stack section from the PRD generated in Step 6. Write the matching values into the Tech Stack section of the SRE agent's `WINDSURF_SRE.md` (path provided by the runner), replacing the placeholder values:

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

#### 7a: Populate WINDSURF_DEV.md

Read the PRD generated in Step 6 and update the developer agent's `WINDSURF_DEV.md` (path provided by the runner):

- **Project name** — replace `[project-name]` in the header with the project name from the PRD
- **Architecture section** — replace the placeholder lines with a brief description of the project structure, key directories, and service boundaries based on the PRD's Technical Approach. Keep it to 3-5 bullet points.
- **Development Environment section** — replace the placeholder lines with stack-specific setup commands based on the language/framework. For example, a Python/FastAPI project gets `pip install -r requirements.txt`, `pytest`, `uvicorn main:app --reload`. Include how to run the full stack locally (e.g., `docker compose up`).
- **Logging/tracing placeholder** — replace `[Logging framework and format]` and `[Metrics and tracing setup]` with the logging and observability tools from the PRD's Observability & SRE section (e.g., "Structured JSON logging via Python `logging`" and "OpenTelemetry for distributed tracing, exported to Cloud Trace").

Leave sections that define process standards (coding practices, testing, CI/CD pipeline, environment strategy, service bootstrap, etc.) unchanged — these are universal and not project-specific.

#### 7b: Populate config.md

Read the PRD generated in Step 6 and the rebuild candidate selected in Step 5. Write the matching values into the developer agent's `config.md` (path provided by the runner), replacing the placeholder values:

**Project section:**
- **Project Name** — from the PRD title
- **Repository** — from the PRD's Target Repository (the new repo, not the legacy repo)
- **Primary Language** — from the PRD's Technical Approach / Tech Stack
- **Framework** — from the PRD's Technical Approach / Tech Stack
- **Cloud Provider** — from the PRD's Technical Approach (GCP or AWS)

**Development Commands section:**
- Pre-fill commands based on the language/framework. For example, a Python/FastAPI project gets `pip install -r requirements.txt` for install, `pytest` for tests, `ruff check .` for lint, `docker build` for container build. A Go/Gin project gets `go mod download`, `go test ./...`, `golangci-lint run`, etc.

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

#### 7c: Generate IDE instruction files and place configs in the built repo

The developer agent only works if the IDE can find the instruction files **at the root of the repository the developer opens**. This step ensures every built repo is self-contained — a developer clones it, opens it in any supported IDE, and the agent prompt loads automatically.

**You must create the following files inside the built repository directory** (the repo that will be cloned by developers — e.g., `automate-v3/`, not the project working directory):

| IDE | File | Location in built repo | Auto-load mechanism |
|---|---|---|---|
| **Windsurf** | `.windsurfrules` | repo root | Read on every Cascade session start |
| **VS Code + GitHub Copilot** | `.github/copilot-instructions.md` | `.github/` at repo root | Included in every Copilot Chat interaction |

Both files contain the same instruction: read `developer-agent/WINDSURF_DEV.md` and `developer-agent/config.md` before doing any work. Copy the content from the templates in the project's `developer-agent/` directory.

**You must also copy the populated `developer-agent/` configs into the built repo:**

| File | Source (project working dir) | Destination (built repo) |
|---|---|---|
| `WINDSURF_DEV.md` | `developer-agent/WINDSURF_DEV.md` | `<repo>/developer-agent/WINDSURF_DEV.md` |
| `config.md` | `developer-agent/config.md` | `<repo>/developer-agent/config.md` |

**Checklist — all four files must exist in the built repo root:**

- [ ] `<repo>/.windsurfrules` — points to `developer-agent/WINDSURF_DEV.md` and `developer-agent/config.md`
- [ ] `<repo>/.github/copilot-instructions.md` — same content as `.windsurfrules`
- [ ] `<repo>/developer-agent/WINDSURF_DEV.md` — populated with project-specific values (from Step 8a)
- [ ] `<repo>/developer-agent/config.md` — populated with project-specific values (from Step 8b)

Without these files in the built repo, the developer agent prompt is not loaded — developers would have to manually paste it into every session. **This is the most common gap in previous rebuilds.** The configs get written to the project working directory but never placed inside the repo that developers actually clone.

**This is the mechanism that makes auto-loading work.** Each IDE has its own convention for project-level instructions. The SRE agent has an equivalent mechanism (`agent.py` reads `WINDSURF_SRE.md` from disk and sends it as the system prompt). The developer agent relies on IDE instruction files to achieve the same guarantee for human development sessions.

> **Note:** If your team uses Cursor, the equivalent file is `.cursorrules` at the repo root. The content is identical to `.windsurfrules`.

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

### Step 12: Developer Agent Standards Compliance Audit

After the code is written, perform a line-by-line compliance check against every requirement in `WINDSURF_DEV.md`. Do not rely on memory — open the file and check each item.

**Service Bootstrap — Required from First PR (all must pass):**

- [ ] `Dockerfile` — pinned base image (e.g., `python:3.12-slim`, not `python:3`), non-root `USER`
- [ ] CI/CD pipeline — must include all stages: lint, test, build, **scan** (container vulnerability), auto-deploy to dev on merge, terraform plan on PR
- [ ] Terraform module — `terraform/` with environment-specific variable files for dev, staging, prod
- [ ] `/health` endpoint — must check critical dependencies and **return 503 if unhealthy** (not always 200)
- [ ] `/ops/*` diagnostic endpoints — verify all 6 exist and return real data: `/ops/status`, `/ops/health`, `/ops/metrics`, `/ops/config`, `/ops/dependencies`, `/ops/errors`
- [ ] `/ops/*` remediation endpoints — verify all 5 exist and are functional: `/ops/drain`, `/ops/cache/flush`, `/ops/circuits`, `/ops/loglevel`, `/ops/scale`
- [ ] `/ops/metrics` specifically — must be wired to middleware that records every request. Must return real Golden Signals (latency p50/p95/p99, traffic, errors, saturation) and RED metrics (rate, errors, duration). Placeholder zeros are not compliant.
- [ ] OpenAPI spec — auto-generated or checked into repo
- [ ] OpenAPI response models — every endpoint (GET, POST, PUT, DELETE) must declare a Pydantic `response_model`. No bare `dict` returns anywhere.
- [ ] OpenAPI examples — every request body model and response model must have `json_schema_extra` with realistic `examples` so Swagger UI displays typed schemas and pre-filled "Try it out" payloads
- [ ] Unit and API test scaffolding — tests exist and run
- [ ] `.env.example` — all environment variables documented
- [ ] OTEL instrumentation — tracing, metrics (`MeterProvider` configured), and structured logging
- [ ] `README.md` — how to run locally, how to test, how to deploy
- [ ] `.windsurfrules` — exists at **built repo root** (not just the project working directory), instructs Windsurf to read `developer-agent/WINDSURF_DEV.md` and `developer-agent/config.md` before any work
- [ ] `.github/copilot-instructions.md` — exists at `.github/` in **built repo root** (not just the project working directory), instructs VS Code + GitHub Copilot to read `developer-agent/WINDSURF_DEV.md` and `developer-agent/config.md` before any work
- [ ] `developer-agent/WINDSURF_DEV.md` — exists inside the **built repo** with all placeholders populated
- [ ] `developer-agent/config.md` — exists inside the **built repo** with project-specific values filled in

**CI/CD pipeline rules:**

- [ ] Container scan stage exists (e.g., Trivy) — CRITICAL and HIGH severity block the build
- [ ] Images tagged with commit SHA only — no `latest` tags in any environment
- [ ] Auto-deploy to dev triggers on merge to main (not manual-only)
- [ ] Terraform plan runs on PR and output is posted as a PR comment
- [ ] Sensitive values (credentials, connection strings) are **never** in `.tfvars` files — they come from secrets manager or CI environment variables

**WINDSURF_DEV.md project-specific sections:**

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
4. **Linter output** — full lint results (e.g., `ruff check .`), must show 0 errors
5. **Formatter output** — format check results (e.g., `ruff format --check .`), must show all files formatted
6. **Type checker output** — strict type check results (e.g., `mypy src/`), must show 0 errors

**Extended Gates (mandatory — measured baselines or pass/fail):**

7. **Test coverage** — `pytest-cov` with `--cov-report=term-missing` showing line-level coverage per module. Report overall %, identify modules below 50%, and explain gaps (e.g., "services require running Redis"). Pure logic modules should target ≥80%.
8. **Cyclomatic complexity** — `radon cc src/ -a -s`. Average must be A or B. Any function rated C or higher must be documented with justification.
9. **Maintainability index** — `radon mi src/ -s`. All files must be rated A or B. Any file rated C or lower must be refactored.
10. **Dead code detection** — `vulture src/ --min-confidence 80`. Must show 0 findings. Unused code must be removed, not commented out.
11. **Dependency vulnerabilities** — `pip-audit`. Report all findings. Critical/High CVEs in runtime dependencies must have a documented remediation plan or documented rationale for deferral.
12. **Docstring coverage** — `interrogate src/ -v`. Report coverage percentage. Identify gaps. Public API functions and classes should have docstrings; thin wrappers and internal helpers may be excluded with justification.
13. **Duplicate code (DRY)** — `pylint --disable=all --enable=duplicate-code src/` and `npx jscpd src/ --min-lines 5 --min-tokens 50`. Must show < 3% duplication. Any detected clones must be justified (e.g., intentional structural similarity) or refactored.
14. **Cognitive complexity** — `ruff check src/ --select C901`. Must show 0 issues at default threshold (10).

**Summary and context:**

15. **Quality gate summary table** — one table showing each gate (tests, lint, format, types, coverage, complexity, maintainability, dead code, vulnerabilities, docstrings, duplication, cognitive complexity), threshold, result, and pass/fail status
16. **Bugs found and fixed** — any source or test bugs discovered during validation, with before/after descriptions
17. **Not yet tested** — anything requiring running infrastructure (integration tests, Docker, DAPR sidecar) that cannot be validated offline

**Required tools** (install in dev environment):
```
pip install pytest-cov radon vulture pip-audit interrogate pylint
npx jscpd  # Node.js — for copy-paste detection
```

This file serves as the build's quality receipt. If the report does not exist or shows failures, the build is not complete.

### Step 13: Documentation–Code Consistency Check

After any code change that adds, removes, or modifies API endpoints, verify that **every document** referencing those endpoints is updated. This includes:

- `README.md` — API endpoint table must list every endpoint with method, path, and description
- `docs/deployment-status.md` (or equivalent) — must have a copy-pastable test command for every endpoint
- `docs/dry-run-testing-guide.md` (or equivalent) — validation commands quick reference must cover all endpoints
- SRE playbooks — any playbook referencing `/ops/*` endpoints must reflect the current set

**Rule:** If an endpoint exists in code but not in docs, or exists in docs but not in code, the build is not complete.

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

### Step 15: Container Build for Cloud Targets

When building container images for cloud deployment (Cloud Run, ECS, GKE, etc.):

- Always specify `--platform linux/amd64` in `docker build` commands. Developer machines (especially Apple Silicon Macs) build ARM images by default, which fail on cloud platforms that require AMD64.
- This applies to all build contexts: local development builds, CI pipeline builds, and documentation examples.
- The `Dockerfile`, CI pipeline, and deployment documentation must all consistently specify the target platform.

Example:
```bash
docker build --platform linux/amd64 -t <registry>/<service>:<commit-sha> .
```

### Step 16: Process Feedback Capture

At the end of every rebuild session where the operator provided manual corrections, instructions, or clarifications that the process did not cover:

1. List every manual instruction the operator gave
2. For each, identify why the process didn't handle it
3. Propose specific additions to this process document (IDEATION_PROCESS.md) or to the developer agent standards (WINDSURF_DEV.md) that would prevent the same gap
4. Apply the changes to the process documents after operator approval

**The rebuild process is a living document.** Every manual correction is evidence of a process gap. If an operator has to tell you something that should have been in the process, the process is incomplete.

### Step 17: Summary of Work

After all previous steps are complete, generate a single summary document that communicates the value and scope of the rebuild at a glance. This document is for stakeholders, leadership, and teams evaluating the rebuild approach.

**Gather metrics programmatically.** Count files and lines from both the legacy codebase (`repo/` and any `adjacent/` directories) and the rebuilt codebase. Do not estimate — measure.

Write results to `output/summary-of-work.md` using this structure:

```
# Summary of Work: [Application Name]

## Overview

[3 paragraph executive summary, structured as follows:

Paragraph 1: What the legacy application was, its problems, and why it needed
rebuilding.

Paragraph 2: How the rebuild was executed (spec-driven automated process).

Paragraph 3 ("Bottom line"): Synthesize three things for a non-technical reader:
(1) how long the rebuild would take a human engineer, (2) how long it actually
took with AI-driven automation, and (3) why the rebuilt codebase is more
maintainable going forward (reduced lines, type safety, automated quality gates,
observability, CI/CD enforcement). This paragraph goes here — before the estimate
table — so a VP can read the executive summary without scrolling.

After these paragraphs, include a grounded human time estimate table broken down
by phase (analysis, architecture/design, implementation, testing, compliance/docs)
with total engineer-days range. Testing must be its own row — do not bundle it
into implementation. Cite industry estimation frameworks (e.g., McConnell's
Code Complete, Capers Jones's Applied Software Measurement) if applicable.
State the acceleration factor achieved by the automated process.]

### Key Numbers

[Summary table of headline metrics — placed here so executives see the numbers
without scrolling past the detailed estimate table. Include: source lines
eliminated, code reduction %, dependencies removed, compliance checks passed,
quality gates passed, test coverage, CVEs, new endpoints, ADRs, total files.
Measure programmatically — do not estimate.]

| Metric | Value |
|--------|-------|
| Source lines eliminated | [n] |
| Source code reduction | [n%] |
| ... | ... |
| Total files delivered | [n] |

### Estimated Human Time Equivalent

[Estimate table goes here — see paragraph guidance above.]

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
| Dependency | Issue |
|---|---|
| [name] | [reason — e.g., deprecated since YYYY, unmaintained, Python 2 compat] |

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
| Lint | ruff check | 0 errors | [n errors] | [PASS/FAIL] |
| Format | ruff format | 0 unformatted | [n/n formatted] | [PASS/FAIL] |
| Type Check | mypy (strict) | 0 errors | [n errors in n files] | [PASS/FAIL] |

**Extended Gates (measured baselines):**

| Gate | Tool | Threshold | Result | Status |
|---|---|---|---|---|
| Test Coverage | pytest-cov | measured | [n% overall] | [MEASURED] |
| Cyclomatic Complexity | radon cc | avg ≤ B | [avg rating (n)] | [PASS/FAIL] |
| Maintainability Index | radon mi | all ≥ B | [all n files rated X] | [PASS/FAIL] |
| Dead Code | vulture | 0 findings | [n findings] | [PASS/FAIL] |
| Dependency Vulnerabilities | pip-audit | 0 critical/high | [n CVEs] | [PASS/FLAGGED] |
| Docstring Coverage | interrogate | measured | [n%] | [MEASURED] |
| Duplicate Code (DRY) | pylint + jscpd | < 3% duplication | [n% duplication] | [PASS/FAIL] |
| Cognitive Complexity | ruff C901 | 0 issues | [n issues] | [PASS/FAIL] |

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

## Process Rules

- **No hypotheticals.** Every opportunity must trace to a real pain point or assessment finding.
- **No invented data.** If you cannot determine something from the provided input, say so. Do not fabricate metrics.
- **No gold-plating.** The goal is to rebuild what's needed, not redesign the perfect system. Resist scope creep.
- **Preserve what works.** Not everything needs to change. Identify and protect the parts of the legacy app that are solid.
- **Kill fast.** If an opportunity fails feasibility, drop it. Do not rehabilitate weak candidates.
- **Speed over perfection.** This process should take minutes, not days.
