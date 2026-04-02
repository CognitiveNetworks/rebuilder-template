# Legacy Rebuild Process

**Type:** Executable Process — Single-Shot
**Version:** 2.0

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
- Adjacent repositories (if listed in scope.md) — related codebases included in the rebuild scope

## Process

Execute the following steps in order. Do not ask for approval between steps. Run the entire process and write all output files when complete.

> **Phase structure:** Steps 1–11 (Analyze) produce analysis artifacts, PRD,
> agent configs, ADRs, and mapping documents — executed by `run.sh` in a single
> automated pass. Steps 12–18 (Build) validate code, generate documentation,
> and capture feedback — executed during interactive development sessions after
> code is written.

### Parallel Execution

Some steps share inputs but produce independent outputs. When the execution
environment supports sub-agents, steps inside a **parallel window** MAY be
dispatched concurrently. Each sub-agent receives shared input artifacts and
writes its own output — no sub-agent depends on another's output.

| Window | After | Parallel Steps | Shared Input |
|--------|-------|---------------|--------------|
| **W1** | Step 1 | Steps 2 + 3 | `legacy_assessment.md`, `scope.md`, `input.md`, `repo/` |
| **W2** | Step 6 | Steps 7 + 8 + 9 + 10 + 11 | `prd.md`, all Step 1–5 outputs, `scope.md`, `input.md`, `repo/`, template files |
| **W3** | Step 12 | Steps 13a + 13b + 14 + 15 | Built codebase + `prd.md` + Step 12 audit results |

After each window, a **consistency check** verifies cross-artifact coherence.
If sub-agents are not available, execute steps sequentially — identical results.

**Detection:** Check whether a sub-agent dispatch tool is available (e.g.,
`runSubagent` in VS Code Copilot). If so, use parallel dispatch. If not,
execute sequentially. Check for the capability, not the brand.

**W2 parallel-safe referencing rule:** Sub-agents MUST NOT reference other W2
outputs by name or number. ADRs must not assert what feature-parity contains.
Feature parity must describe decisions by PRD section, not ADR number. Agent
configs must not use ADR numbers in TODOs. Step 11a reconciles cross-references
after all sub-agents complete.

**Sub-agent failure:** Re-run the failed step sequentially with the same inputs.
Do not re-run steps that succeeded.

---

### Step 1: Legacy Assessment

> **Step 1a — Capture Prompt**: Before any analysis, copy the user's original
> rebuild request verbatim into `input.md § Original Prompt`. Preserve exact
> wording — do not summarize.

Analyze the current application described in `../scope.md` and `input.md`.

Evaluate across these dimensions (rate each Good / Acceptable / Poor / Critical):

| Dimension | Key Questions |
|-----------|--------------|
| **Architecture Health** | Appropriate for scale? Separation of concerns? Component coupling? |
| **Code & Dependency Health** | Dependency age/maintenance? EOL/deprecated/CVE deps? How far behind LTS? |
| **API Surface Health** | APIs documented (OpenAPI)? Versioned? Testable via API alone? |
| **Observability & SRE** | Monitoring, logging, alerting, tracing? SLOs/SLAs? Golden Signals? Diagnostic endpoints? |
| **Auth & Access Control** | Auth mechanism? RBAC or all-or-nothing? Shared creds? Service-to-service auth scoped? |
| **Operational Health** | Deployment reproducible? Testing/coverage/CI/CD? Monitoring gaps? |
| **Data Health** | Schema normalized? Migration scripts exist? Migration complexity? |
| **Developer Experience** | Time to productive? Tribal knowledge? Local dev setup? |
| **Infrastructure Health** | Cloud provider(s)? Containerized? IaC? Managed services? Portability? Provider lock-in? Cloud-specific SDKs in code? |
| **External Dependencies** | Runtime API calls? Known consumers? Shared DBs/caches/queues? Internal libraries? Data feeds? Tight coupling? |

**Adjacent Repository Analysis** (only if adjacent repos are provided):

For each adjacent repo, analyze: purpose, tech stack, integration points with primary, shared state, coupling assessment, and rebuild recommendation (absorb / keep separate / rebuild independently). Document cross-repo integration summary.

**Output:** Write to `output/legacy_assessment.md` using the template at `rebuild/templates/legacy_assessment.md`.

### Step 2: Component Overview

Write a **Component Overview** that explains the current application for a non-developer audience — product managers, architects, team leads, and new engineers.

This describes the **current software as it exists today**, not the rebuilt version.

> **Critical constraint:** Zero references to the target state, the rebuild, or any planned changes. If a feature exists in legacy (even if deprecated), describe it as-is. Target state is in the PRD and ADRs.

**Audience:** Someone who has never seen the codebase. Plain language. No code snippets. Define domain terms where first used.

**Required Sections:**

1. **What Is This?** — One-paragraph summary
2. **Why Does It Exist?** — Business context
3. **Key Concepts** — Domain glossary (2-3 sentences per term)
4. **What It Does** — Each major functional area: purpose, data, consumers
5. **Pure Utility Functions** (if applicable) — Table with descriptions
6. **CLI Tools** (if applicable) — Table of entry points
7. **How It Fits in the Platform** — Mermaid diagram + narrative data flow
8. **How Teams Consume It** — Table of consumption modes
9. **Technology** — Current stack table
10. **Deployment** — Current deployment and operations
11. **Known Limitations** — Table of gaps (from legacy assessment)
12. **Codebase** — Repo link, size, package structure, dep count

**Guidance:** Keep under 300 lines. Include at least one mermaid diagram. Draw from legacy assessment, `scope.md`, `input.md`, and source code.

**Output:** Write to `docs/component-overview.md` inside the rebuilt application directory.

> **W1:** Steps 2 and 3 share inputs and produce independent outputs. Dispatch concurrently if sub-agents available. Step 4 depends on Step 3.

### Step 3: Modernization Opportunities

Identify the top modernization opportunities from the legacy assessment and scope.md pain points.

An opportunity qualifies ONLY if it:
- Directly addresses an identified pain point
- Has a clear, measurable before/after
- Is technically feasible given scope.md constraints
- Would meaningfully improve the application

**Infrastructure migration** qualifies as an opportunity if scope.md specifies a provider change — but only if it addresses real pain points. Do not treat migration as an excuse to change everything.

For each opportunity, document: what changes and why, current state (specifics, not "it's slow"), target state, migration path, and risks.

**No hypothetical improvements.** Every opportunity must trace to a real finding.

**Output:** Write to `output/modernization_opportunities.md`. Begin with the reference document header.

### Step 4: Feasibility Analysis

For each opportunity rated High or Critical impact, validate:

1. **Effort:** T-shirt size (S/M/L/XL) with rationale
2. **Risk:** Data loss, downtime, feature regression, integration breakage. Rate: Low / Medium / High.
3. **Dependencies:** Blocking relationships and ordering
4. **Rollback:** Reversion strategy

**Verdict per opportunity:** Go / Caution / No-Go. No-Go opportunities do not become candidates.

**Output:** Write to `output/feasibility.md`. Begin with the reference document header.

### Step 5: Rebuild Approach Candidates

For each feasible opportunity (or logical grouping), create `output/candidate_N.md` (N = 1, 2, 3, etc.) using the template at `rebuild/templates/candidate.md`.

### Step 6: PRD Generation

For the candidate that best addresses the highest-priority pain points, generate a PRD.

**Output:** Write to `output/prd.md` using the template at `rebuild/templates/prd.md`.

---

### Steps 7–11: Post-PRD Artifacts

> **W2:** Steps 7–11 all depend on the PRD but are completely independent of
> each other. This is the highest-value parallelization point. Each sub-agent
> starts fresh with only the PRD + its template — dramatically smaller context
> than carrying the full conversation history.

### Step 7: SRE Agent Configuration

Populate the SRE agent's `skill.md` and `config.md` (paths provided by the runner) from the PRD's Tech Stack section.

**⚠️ STRICT TEMPLATE POPULATION RULES** (apply to Steps 7 and 8):

1. **PRESERVE EVERY SECTION.** Do not delete, merge, skip, or summarize any section.
2. **ONLY REPLACE PLACEHOLDERS.** Find `*[brackets]*` or `[brackets]` and replace with real values.
3. **DO NOT REPHRASE** instructional comments (lines starting with `>`).
4. **DO NOT ADD SECTIONS.**
5. **KEEP FORMATTING IDENTICAL** — heading levels, table columns, list styles, code blocks.
6. **IF UNKNOWN**, leave placeholder as-is with `<!-- TODO: fill after infra provisioning -->`.
7. **DIFF CHECK.** Only differences should be placeholder → real value.

**skill.md fields:** Cloud Provider, Orchestration, Backend, Database, Cache, Additional (queues, CDNs, APIs).

**config.md fields:**
| Section | What to populate |
|---------|-----------------|
| Tech Stack | Same values as skill.md |
| Service Registry | Service names from PRD; URLs as `*[TODO: URL after infra provisioning]*` |
| SLO Thresholds | From PRD Observability section (if defined) |
| PagerDuty, Escalation, Auth, Runtime | Leave template placeholders — populated during deployment |

**LLM Provider:** GCP → Vertex AI (Gemini) with Application Default Credentials. AWS → set `LLM_API_KEY` and `LLM_API_BASE_URL`.

### Step 8: Developer Agent Configuration

Populate the developer and QA agent configs so teams start with accurate settings from day one.

**Target Language Selection:** Determine from PRD's Technical Approach or `scope.md`:

| Language | Developer Agent | QA Agent | Template Repo |
|---|---|---|---|
| Python | `python-developer-agent/` | `python-qa-agent/` | `rebuilder-evergreen-template-repo-python` |
| C | `c-developer-agent/` | `c-qa-agent/` | `rebuilder-evergreen-template-repo-c` |
| Go | `go-developer-agent/` | `go-qa-agent/` | `rebuilder-evergreen-template-repo-go` |

`{lang}` below refers to the target language prefix.

**Three skill.md Files — Distinct Roles:**

|  | `template/skill.md` | `{lang}-developer-agent/skill.md` | `{lang}-qa-agent/skill.md` |
|---|---|---|---|
| **Purpose** | Universal build standard | Project-specific coding rules | Verification procedures |
| **Scope** | Same for every rebuild | Populated per project | Populated per project |
| **Loaded** | Auto-loaded every session | Auto-loaded every session | On demand via `/qa` |
| **Mutability** | Immutable — org-wide | Customized per project | Customized per project |

#### 8a: Populate skill.md

From the PRD, update `{lang}-developer-agent/skill.md`:

| Field | Source |
|-------|--------|
| Project name | PRD title → replace `[project-name]` in header |
| Architecture section | PRD Technical Approach → 3-5 bullet points (structure, key dirs, service boundaries) |
| Development Environment | Stack-specific setup commands (install, test, lint, run, verify) |
| Logging/tracing | PRD Observability section → replace placeholders |

Leave universal process sections (coding practices, testing, CI/CD, etc.) unchanged.

#### 8b: Populate config.md

From the PRD, update `{lang}-developer-agent/config.md`:

| Section | Fields to populate |
|---------|-------------------|
| Project | Name, Repository (new repo), Language, Framework, Cloud Provider |
| Development Commands | Pre-fill per language/framework (install, test, lint, format, build) |
| CI/CD | Pipeline Tool (default GitHub Actions), Container Registry (GCR/ECR), Image Tag Strategy (commit SHA) |
| Environments | dev/staging/prod rows |
| Terraform | State Backend (`gs://` or `s3://`), Directory (`terraform/`), Variable Files |
| Services | Service table from PRD architecture |
| SRE Integration | Config path, Service Registry entries |

Leave runtime-specific sections as `[TODO]` (secrets, monitoring URLs, external dep docs, environment URLs).

#### 8c: Generate IDE instruction files and place configs in built repo

Create these files in the **built repository** (the repo developers clone):

| File | Purpose |
|------|---------|
| `.windsurfrules` | Read `{lang}-developer-agent/skill.md`, `config.md`, and `template/skill.md` every session |
| `.github/copilot-instructions.md` | Same content for VS Code + GitHub Copilot |
| `{lang}-developer-agent/skill.md` | Populated from Step 8a |
| `{lang}-developer-agent/config.md` | Populated from Step 8b |
| `template/skill.md` | Copied from template repo — QA validates every checkbox |

> **Critical:** `template/skill.md` **must** be in `.windsurfrules` — this is
> the only mechanism that guarantees the template checklist is read every session.
> Without it, agents follow coding standards but skip structural requirements.

#### 8d: Populate QA Agent Configuration

From the PRD and developer agent config, update `{lang}-qa-agent/config.md`:

| Section | Fields to populate |
|---------|-------------------|
| Project | Name, Repository, Original Legacy Repo |
| Required Env Vars for Tests | Every variable from `environment-check.sh` `always_required_vars` + app-specific, with safe test defaults |
| API Endpoints to Verify | Every endpoint from PRD (method, path, expected status) |
| Event Types to Verify | Every event type with validation rules and output shape |
| Environment Variable Mapping | All renames from legacy (e.g., `FLASK_ENV` → removed) |
| External Dependency Mocking | Each infra dependency → mock strategy |

**Copy into built repo:**

| Source | Destination |
|--------|------------|
| `{lang}-qa-agent/skill.md` | `<repo>/{lang}-qa-agent/skill.md` |
| `{lang}-qa-agent/config.md` | `<repo>/{lang}-qa-agent/config.md` |
| `{lang}-qa-agent/TEST_RESULTS_TEMPLATE.md` | `<repo>/{lang}-qa-agent/TEST_RESULTS_TEMPLATE.md` |
| `{lang}-qa-agent/examples/` | `<repo>/{lang}-qa-agent/examples/` |

### Step 9: Architecture Decision Records

Generate initial ADRs from the PRD's "ADRs Required" section. Write each to `docs/adr/NNN-<short-title>.md`.

**ADR structure:**

```
# ADR NNN: [Decision Title]
## Status
Accepted
## Context
[Situation, forces, problem]
## Decision
[What was decided]
## Alternatives Considered
[Other options and why rejected]
## Consequences
[Positive and negative outcomes, trade-offs]
```

**Sources:** Context from Steps 1/3/6, Decision from Steps 5/6, Alternatives from candidates/feasibility.

**Minimum ADRs:** Cloud provider, primary database, backend language/framework, container orchestration. If cloud migration: migration rationale, cross-cloud connectivity, managed service mapping.

**ADR Index (parallel execution only):** Generate `docs/adr/adr-index.yaml` mapping topics to ADR numbers for Step 11a cross-reference insertion:

```yaml
adrs:
  - number: "ADR-001"
    title: "Use GCP as Cloud Provider"
    prd_sections: ["Technical Approach", "Infrastructure Migration Plan"]
    topics: ["cloud provider", "GCP"]
```

### Step 10: Feature Parity Matrix

Catalog every user-facing feature, integration, and workflow from the legacy application. Write to `docs/feature-parity.md`.

| Column | Description |
|--------|-------------|
| Feature | Name of feature or workflow |
| Legacy Behavior | How it works today (be specific) |
| Status | Must Rebuild / Rebuild Improved / Intentionally Dropped / Deferred |
| Target Behavior | How it works after rebuild (from PRD) |
| Acceptance Criteria | How to verify it works |
| Notes | Phase, dependencies, migration considerations |

**Rules:**
- Every feature has a status. No unknowns.
- **Intentionally Dropped** requires justification in a dedicated table.
- Include integrations (APIs, webhooks, data feeds) as a separate section.
- Must be complete enough to serve as the acceptance checklist.

**Library Transition Mapping:** When replacing a shared library, include a Library Transitions table mapping every consumed function to its replacement. Never say "removed" without naming the replacement. Every function must be mapped. Uncertain replacements flagged as "No" in Confirmed column.

### Step 11: Data Migration Mapping

Produce the schema mapping between legacy and target. Write to `docs/data-migration-mapping.md` using the template at `rebuild/templates/data_migration.md`.

**Rules:**
- Every legacy table and column must appear. Nothing silently dropped.
- Dropped columns documented with justification.
- Reconciliation queries must be runnable — not pseudocode.

### Step 11a: Cross-Artifact Consistency Check

After Steps 7–11 complete, verify cross-artifact coherence:

| Check | What to verify |
|-------|---------------|
| **1. Service Names** | Identical across PRD, SRE config, developer config, feature parity |
| **2. Endpoint Inventory** | Every PRD endpoint appears in feature parity and SRE config |
| **3. Tech Stack Alignment** | Same language/framework/DB/cache/cloud across PRD, SRE skill/config, developer skill/config |
| **4. Data Schema Coherence** | Migration mapping target tables align with PRD and ADRs |
| **5. ADR Cross-References** | PRD "ADRs Required" list matches generated ADRs |
| **6. Terminology** | Same concept uses same name across all documents |
| **7. Navigation Links** (parallel only) | Insert ADR numbers using `adr-index.yaml`, verify forward references, add cross-links, replace ADR numbers in agent configs with PRD section descriptions |

**Output:** "Cross-artifact consistency check: PASS" or fix inconsistencies. Document fixes in `output/process-feedback.md`.

### Step 11b: Automated Output Validation (Phase 1)

```bash
./rebuild/validate.sh rebuild-inputs/<project> analyze
```

**Mandatory gate.** Do not proceed to Phase 2 until zero failures.

---

## Phase 2: Build (Steps 12–18)

Steps 12–18 are executed **during the build phase** — after the developer agent has written the service code.

### Clean Start (required before writing any code)

The destination directory (from `scope.md` → Destination Directory → Local Path) must be empty except for `.git/`. If running via `/run-replicator`, Step 1c already handled this. If running manually, clean it now:

```bash
find <destination-dir> -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +
```

**Do not skip this step.** Old code from a prior build will cause the agent to make incorrect assumptions about what already exists, leading to partial updates instead of clean implementations.

### Template Repo Checklist (required before writing code)

> Read `template/skill.md` from `rebuild-inputs/<project>/template/`. Complete
> every checkbox during the Build phase. Do not invent your own tooling, configs,
> or patterns — match the template. Mark N/A items with justification.
>
> The template repo is **not** an adjacent repo. Adjacent repos are production
> dependencies. The template repo defines *how* to build, not *what* to build.

---

### Step 12: Developer Agent Standards Compliance Audit

After code is written, perform a line-by-line compliance check against `skill.md`.

**Service Bootstrap — all must pass before first PR:**

- [ ] `Dockerfile` — pinned base image, non-root `USER`
- [ ] CI/CD pipeline — lint, test, build, scan, auto-deploy to dev, terraform plan on PR
- [ ] Terraform module — `terraform/` with env-specific variable files
- [ ] `/health` — checks critical deps, returns 503 if unhealthy
- [ ] `/ops/*` diagnostic endpoints (6): `/ops/status`, `/ops/health`, `/ops/metrics`, `/ops/config`, `/ops/errors`, `/ops/cache`
- [ ] `/ops/*` remediation endpoints: `/ops/cache/flush`, `/ops/cache/refresh`, `/ops/circuits`, `/ops/loglevel`, `/ops/log-level`
- [ ] `/ops/metrics` — wired to middleware, real Golden Signals + RED metrics (no placeholder zeros)
- [ ] OpenAPI spec — auto-generated or checked in
- [ ] OpenAPI response models — every endpoint has Pydantic `response_model`, no bare `dict`
- [ ] OpenAPI examples — every model has `json_schema_extra` with realistic examples
- [ ] Unit and API test scaffolding
- [ ] `.env.example`
- [ ] OTEL instrumentation — tracing, metrics, structured logging
- [ ] `README.md`
- [ ] `.windsurfrules` at built repo root (reads developer agent + template skill.md)
- [ ] `.github/copilot-instructions.md` at built repo root
- [ ] `{lang}-developer-agent/skill.md` and `config.md` in built repo (populated)
- [ ] `{lang}-qa-agent/skill.md`, `config.md`, `TEST_RESULTS_TEMPLATE.md`, `examples/` in built repo

**QA Agent Verification:**

After developer agent claims compliance, activate QA agent (`/qa` workflow) to independently verify: re-run all quality gates, verify `/ops/*` endpoints, verify `environment-check.sh`, verify Dockerfile/entrypoint/Helm match template, walk every `template/skill.md` checkbox, generate independent `tests/TEST_RESULTS.md`, flag discrepancies.

**CI/CD pipeline rules:**

- [ ] Container scan (e.g., Trivy) — CRITICAL/HIGH block build
- [ ] Images tagged with commit SHA only — no `latest`
- [ ] Auto-deploy to dev on merge to main
- [ ] Terraform plan on PR with output as PR comment
- [ ] Sensitive values never in `.tfvars` — from secrets manager or CI env vars

**Quality Gate Verification — `tests/TEST_RESULTS.md`:**

Run the full quality suite and produce a test results report. Must include:

**Core Gates (mandatory):**

| # | Gate | Tool | Requirement |
|---|------|------|-------------|
| 1 | Tool versions | — | Python, pytest, linter, formatter, type checker versions |
| 2 | Codebase metrics | — | Source/test file and line counts |
| 3 | Tests | pytest | Full verbose output, 0 failures |
| 4 | Lint | pylint | 0 errors |
| 5 | Format | black | All files formatted |
| 6 | Type check | mypy | 0 errors |

**Extended Gates (mandatory):**

| # | Gate | Tool | Requirement |
|---|------|------|-------------|
| 7 | Coverage | pytest-cov | `--cov-report=term-missing`, modules below 50% explained |
| 8 | Dependency vulns | pip-audit | Critical/High must have remediation plan |
| 10 | Docstring coverage | interrogate | Report %, identify gaps |
| 11 | Duplicate code | pylint + jscpd | < 3% duplication |
| 12 | Cognitive complexity | complexipy | `-mx 15`, 0 issues |

Plus: quality gate summary table, bugs found/fixed, and not-yet-tested items.

### Step 12a: Template Repository Component Checklist

Verify every structural component from the template repo exists in the built repo. This catches missing files not covered by developer agent compliance checks.

**Required components:**

- [ ] `hooks/pre-commit` — runs all quality gates
- [ ] `charts/` — Helm chart with all standard templates
- [ ] `charts/tests/` — Helm unittest YAML files
- [ ] `tests/test-helm-template.sh` — renders across environments
- [ ] `cves/` — VEX JSON files (may contain `.gitkeep`)
- [ ] `scripts/lock.sh` — pip-tools locking with `--generate-hashes`
- [ ] `scripts/entrypoint.sh` — sources environment-check, starts app
- [ ] `scripts/environment-check.sh` — env var validation
- [ ] `.actrc`, `env.list`, `monitored-paths.txt`, `.pylintrc`, `.python-version`, `catalog-info.yaml`
- [ ] `docker-compose.yml` — full local dev stack with healthchecks
- [ ] `template/skill.md` — copied from template repo, referenced in `.windsurfrules`

**File permissions verification:** IDE file-creation tools write all files as `100644` (non-executable). After staging, verify every `.sh` file and `hooks/*` file is `100755` in the git index:

```bash
# Check — all should show 100755
git ls-files -s -- '*.sh' 'hooks/*'

# Fix any that show 100644
chmod +x <file>
git update-index --chmod=+x <file>
```
- [ ] `.github/scripts/pod-identity-generator/`, `.github/scripts/workflow-runner.sh`

**Required tooling** (each must be in pyproject.toml dev deps, configured, and in CI):

| Tool | Command | Purpose |
|------|---------|---------|
| pylint | `pylint {src} tests` | Static analysis |
| mypy | `mypy {src}/` | Type checking |
| black | `black {src} tests` | Formatting |
| pytest | `pytest` | Testing (with pytest-cov) |
| complexipy | `complexipy {src} -mx 15` | Cognitive complexity |
| helm unittest | `helm unittest ./charts` | Helm chart testing |
| helm lint | `helm lint ./charts` | Helm validation |
| pip-audit | `pip-audit` | Dependency vulnerability scanning |
| interrogate | `interrogate {src}/ -v` | Docstring coverage |

Cross-reference against CI pipeline and `hooks/pre-commit`. Flag any tool missing from either.

**Adaptation rules:** Components may be adapted for the project. N/A components documented in `output/process-feedback.md`. Nothing silently skipped.

### Step 13: Documentation–Code Consistency Check

After any code change adding/removing/modifying endpoints, verify every document referencing them is updated: `README.md`, deployment docs, testing guides, SRE playbooks.

**Rule:** If an endpoint exists in code but not in docs, or in docs but not in code, the build is not complete.

> **W3:** Steps 13a, 13b, 14, and 15 produce independent outputs. Dispatch
> concurrently if sub-agents available. Step 13 must complete first (may trigger
> code changes). 13b (legacy endpoint compatibility) is a merge blocker —
> do not proceed to 13c (Docker validation) until 13b passes. After W3, run Step 15a.

### Step 13a: Domain-Realistic Test Scenarios

AI-generated tests reveal themselves through generic data (`"abc123"`, `"token"`, `"item-001"`). An engineer reviewing tests should see domain expertise.

**Requirements:**
- **Realistic identifiers** from the problem domain (real model numbers, MAC-derived hashes, production-format hostnames) — never `abc123`, `test-token`, `foo`
- **Test class names** describe real-world scenarios (`TestDeviceCheckinLifecycle`, not `TestControlEndpoint`)
- **Test method docstrings** tell client-to-server interaction stories
- **Test method names** describe the scenario from caller's perspective
- **Assert on business-meaningful values**, not just status codes
- **Validate response shapes** against what real clients parse

### Step 13b: Legacy Endpoint Compatibility Verification

The rebuilt service must be **wire-compatible** with the legacy service for all existing endpoints. External integration test suites (e.g., unitE) and upstream clients (load balancers, monitoring, other services) call the legacy API and expect identical response formats. Any deviation causes integration test failures or production incidents.

**Required checks for every endpoint that existed in the legacy service:**

| # | Check | What to verify |
|---|-------|----------------|
| 1 | **Response format** | Same content type (plain text vs JSON), same body structure, same HTTP status codes |
| 2 | **Error response shape** | Same JSON keys and value semantics — e.g., if legacy returns `{"error": "ClassName", "message": "details"}`, the rebuilt service must return the same shape, not `{"error": "details", "detail": null}` |
| 3 | **Required parameters** | Same set of required parameters with same names and validation behavior — if legacy requires `EventType` and `timestamp`, the rebuilt service must too |
| 4 | **Query parameters** | If legacy reads params from URL query string (`?tvid=X&event_type=Y`), the rebuilt service must read the same query params |
| 5 | **Cross-validation** | If legacy cross-validates URL params vs body params (logging mismatches), the rebuilt service must do the same |
| 6 | **Exception class names** | If legacy returns exception class names in error responses (e.g., `TvEventsMissingRequiredParamError`), the rebuilt service must return matching names |

**How to verify:**

1. Read every route handler in the legacy service. For each endpoint, document: HTTP method, path, query params read, body format, success response, error response(s).
2. Compare against the rebuilt service's corresponding handler. Every item above must match.
3. If an external integration test suite exists (e.g., unitE), deploy the rebuilt service to a PR environment and run the suite. All tests must pass before merge.

**Common mistakes that break integration tests:**

| Legacy (Flask) | Rebuilt (FastAPI) — WRONG | Fix |
|----------------|--------------------------|-----|
| `return "OK"` (plain text) | `return JSONResponse({"status": "ok"})` | Use `PlainTextResponse("OK")` |
| `{"error": "ClassName", "message": "..."}` | `{"error": "...", "detail": null}` | Match legacy key names and values |
| `request.args.get('tvid')` (URL query param) | Ignores query params | Add `Query(default=None)` params |
| Required: `tvid, client, h, EventType, timestamp` | Required: `tvid, client, h` only | Include all legacy required params |

> **This step is a merge blocker.** A rebuilt service that passes all unit tests but breaks integration tests is not production-ready. Wire compatibility with the legacy service's API contract is non-negotiable.

### Step 13c: Docker Runtime Validation

Validate the full stack runs in Docker after unit tests pass.

**Pre-flight:** `docker compose up --build -d` — all containers healthy, all sidecars running, all infrastructure healthy.

**Common failures:**

| Symptom | Fix |
|---------|-----|
| `executable not found` (e.g., `opentelemetry-instrument`) | Use `pip install --prefix=/install` in Dockerfile build stage |
| Pydantic `SettingsError` on `list[str]` | Use `str` type with `@property` that splits on comma |
| Sidecar `TimeoutError` | Add per-service `DAPR_HTTP_PORT`/`DAPR_GRPC_PORT` overrides |
| Sidecar `NoCredentialProviders` | Add `ignoreErrors: true` to DAPR component specs for cloud-only bindings |
| Runtime dependency `ImportError` | Move from dev to main `[project.dependencies]` |
| PostgreSQL `role does not exist` | Match seed script credentials to docker-compose.yml |

**Seed data:** Must seed all data stores (not just primary DB). Verify data exists after seeding.

**Smoke test:** Run integration smoke test. All endpoints return expected status codes. Do not use `curl -f` when checking HTTP status codes.

### Step 14: Observability Documentation

Every deployed service has two types of metrics. Documentation must explain both:

| Type | Source | Examples | Query Method |
|------|--------|----------|-------------|
| **Service metrics** | Platform (Cloud Run, ECS, GKE) | CPU, memory, request count/latency, instance count | Cloud provider monitoring API/console |
| **Application metrics** | App middleware | Golden Signals (latency p50/p95/p99, traffic, errors, saturation), RED | `/ops/metrics` (pull) + OTEL export (push) |

Include example `curl` commands for `/ops/metrics` and platform monitoring commands. Explain what each measures and when to use which.

### Step 15: Target Architecture Documentation

Produce a standalone architecture document describing the **end state** of the rebuilt service. Write to `docs/target-architecture.md`.

**Required sections:**

1. **What Changed** — Table: legacy component → target module
2. **System Architecture** — Mermaid component diagram (callers, entry points, domain modules, library layer, infrastructure)
3. **Data Flow Diagrams** — Mermaid sequence diagrams: primary read, primary write, async/event flows, auth-gated flows
4. **Library Relationship** (if applicable) — How shared libraries are consumed, what they provide, why this model was chosen
5. **What Changed and What Didn't** — Legacy vs target comparison table
6. **Deployment Architecture** — Container runtime, sidecar, probes diagram
7. **Features Intentionally Removed** — Table with justification and ADR reference
8. **Related Documents** — Links to component overview, feature parity, PRD, ADRs, observability docs, data migration mapping

> Describes **target state only**. For legacy state, reference `docs/component-overview.md`.

### Step 15a: Build Phase Consistency Check

| Check | What to verify |
|-------|---------------|
| **1. Endpoints vs Code** | Every route in source code appears in README, target-architecture, SRE playbooks — and vice versa |
| **2. Test Coverage** | Every endpoint has ≥1 test; names follow domain-realistic convention |
| **3. Observability vs Code** | `/ops/metrics` returns documented Golden Signals/RED; middleware wired in startup |
| **4. Architecture vs Code** | Module structure in docs matches actual directory layout; dependency flow diagrams match imports |

**Output:** "Build phase consistency check: PASS" or fix and document in `output/process-feedback.md`.

### Step 16: Container Build for Cloud Targets

Always specify `--platform linux/amd64` in `docker build` commands — developer machines (Apple Silicon) build ARM images by default, which fail on cloud platforms. Applies to local builds, CI, and documentation.

### Step 17: Process Feedback Capture

At session end, for every manual correction the operator gave:
1. List every manual instruction
2. Identify why the process didn't handle it
3. Propose specific additions to IDEATION_PROCESS.md or skill.md
4. Apply after operator approval

### Step 18: Summary of Work

After all previous steps are complete, generate a single summary document that
communicates the value and scope of the rebuild at a glance. This document is
for stakeholders, leadership, and teams evaluating the rebuild approach.

**Gather metrics programmatically.** Count files and lines from both the legacy
codebase (`repo/` and any `adjacent/` directories) and the rebuilt codebase.
Do not estimate — measure.

**Output:** Write to `output/summary-of-work.md` using the template at
`rebuild/templates/summary_of_work.md`. Copy the template, then populate every
placeholder with real values. The template is the **authoritative structure** —
do not add, remove, or reorder sections.

#### Section-by-Section Population Guide

**Overview (two-column HTML table):**
- Left column (55%): Three executive summary paragraphs.
  - Paragraph 1: What the legacy application was, its problems, and why it
    needed rebuilding.
  - Paragraph 2: How the rebuild was executed (spec-driven automated process).
  - Paragraph 3 ("Bottom line"): Synthesize for a non-technical reader:
    (1) how long the rebuild would take a human engineer, (2) how long it
    actually took with AI-driven automation, and (3) why the rebuilt codebase
    is more maintainable going forward.
- Right column (45%): Key Numbers table with headline metrics measured
  programmatically (source lines eliminated, code reduction %, dependencies
  removed, compliance checks passed, quality gates passed, test coverage,
  CVEs, new endpoints, ADRs, total files).

**Estimated Human Time Equivalent:**
- Two engineer profiles are **mandatory**: "Familiar Engineer" (senior, knows
  the legacy codebase) and "Unfamiliar Engineer" (new to the codebase, must
  build context first). Both assume full-time 8h days.
- Use the exact table structure from the template with phases: Legacy analysis
  (Steps 1–3), Architecture & design (Steps 4–8), Feature parity & data
  mapping (Steps 9–10), Implementation, Testing, Compliance & docs (Steps
  11–16), Total.
- Each row must include: deliverables, day ranges for both profiles, and a
  basis column with justification citing LOC counts, file counts, and domain
  complexity.
- After the table: state the actual AI-driven pipeline time (use real
  conversation timestamps — never fabricate), estimated acceleration factor
  for each profile, and that the human role shifted from execution to review.
- Include the four numbered footnotes from the template (McConnell, Jones ×2,
  Meszaros).
- **Do not use a single "Engineer-Days" column.** The dual-column format is
  mandatory for consistency across all rebuild summaries.

**Spec-Driven Approach:** Table showing each step in IDEATION_PROCESS.md that
was executed and what artifact it produced.

**Source Code Metrics:** Three sub-tables — Legacy Codebase, Rebuilt Codebase,
and Comparison. All values measured programmatically (`find`, `wc -l`, etc.).

**Dependency Cleanup:** Two sub-tables — Removed (with issue and replacement —
**never leave the replacement column blank**) and Current (with version and
purpose). Include the runtime dependency count comparison.

**Legacy Health Scorecard:** Reproduce ratings from the legacy assessment
(Step 1) for all 10 dimensions.

**New Capabilities:** Table comparing legacy vs. rebuilt for each capability
(HTTP API, OpenAPI Spec, Structured Logging, Distributed Tracing, Health
Checks, Container Image, IaC, CI/CD, SRE Diagnostic Endpoints, plus any
additional capabilities).

**Compliance Result:** Summary from the Developer Agent Standards Compliance
Audit (Step 12) with category, checks, passed, and failed counts.

**Extended Quality Gate Results:** Core gates (pytest, pylint, black, mypy)
and extended gates (coverage, pip-audit, interrogate, duplicate code,
complexipy) from `tests/TEST_RESULTS.md`. Include brief notes on coverage
gaps, flagged vulnerabilities, and justified exceptions.

**Architecture Decisions:** Summary table of all ADRs with number, title,
decision, and key trade-off.

**File Inventory:** Tree view of all delivered files organized by category:
Source, Tests, Infrastructure, Documentation.

### Step 18a: Automated Output Validation (Phase 2)

```bash
./rebuild/validate.sh rebuild-inputs/<project> all
```

**Final gate.** The rebuild is not complete until zero failures.

---

## Process Rules

- **No hypotheticals.** Every opportunity must trace to a real finding.
- **No invented data.** If you cannot determine something, say so.
- **No gold-plating.** Rebuild what's needed, not the perfect system.
- **Preserve what works.** Identify and protect solid parts of the legacy app.
- **Kill fast.** If an opportunity fails feasibility, drop it.
- **Speed over perfection.** This process should take minutes, not days.
- **Consistency after concurrency.** Parallel windows require subsequent consistency checks — not optional.
- **Validate after each phase.** Run `rebuild/validate.sh` after Phase 1 (Step 11b) and Phase 2 (Step 18a). Do not proceed past a phase boundary with failures outstanding.
- **Workspace isolation.** The replicator reads **only** from `rebuild-inputs/<project>/repo/` (legacy), `rebuild-inputs/<project>/template/` (build standard), and `rebuild-inputs/<project>/adjacent/` (if listed in scope.md). Never read from, reference, or import code from any other `rebuilder-*` repository in the workspace. Other rebuilder repos may be in any state — partially built, stale, or from a different project. Referencing them contaminates the build. The destination directory is wiped clean before every run; do not read from it expecting prior state.
- **Clean destination.** Before Phase 2 writes any code, the destination directory (specified in `scope.md` → Destination Directory) must be wiped clean (preserving `.git/`). No file from a prior build may survive into the new build. The `/run-replicator` workflow handles this cleanup; if running manually, execute: `find <dest> -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +`
