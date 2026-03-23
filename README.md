# Rebuilder Template

Structured process for analyzing legacy applications, producing rebuild and infrastructure migration plans, and generating the agent configurations that carry those standards into development and operations.

## What This Is

A three-phase workflow for legacy application rebuilds:

1. **Analyze** — Point an AI coding agent at a legacy codebase (and optionally its adjacent repos). It fills out the input documents, runs an 18-step analysis (IDEATION_PROCESS.md), and produces a PRD, architecture decision records, and auto-populated agent configs.
2. **Build** — Create a new repo for the rebuilt application. Copy the populated agent configs into it. Use the developer agent instructions to build the service from the PRD.
3. **Operate** — Deploy the SRE agent. It receives alerts from your monitoring platform (GCP Cloud Monitoring, New Relic, Datadog, etc.), diagnoses issues using the `/ops/*` endpoints your service exposes, takes safe remediation actions, and escalates to humans via PagerDuty when it cannot confidently resolve an issue.

This is **not** for greenfield products. It assumes you already have a running application and want to rebuild it with a modern stack, better architecture, or improved observability.

All rebuilt services follow an **API-first** design — every feature is exposed and testable through APIs. Services include **SRE agent endpoints** (`/ops/*`) for automated diagnostics and safe remediation, instrumented with **Google SRE best practices** (Golden Signals, RED method, SLOs with error budgets).

## Contents

- [How the Template Files Relate](#how-the-template-files-relate) — diagrams, file reference table
- [Repository Structure](#repository-structure) — full directory tree
- [How to Use](#how-to-use) — quick start for Windsurf and VS Code, phase-by-phase guide
- [What Gets Generated](#what-gets-generated) — output artifacts from the rebuild process
- [Developer Agent](#developer-agent) — coding standards, testing, CI/CD, observability
- [QA Agent](#qa-agent) — quality gates, verification procedures, acceptance criteria
- [SRE Agent](#sre-agent) — incident response, diagnostics, remediation, runtime service
- [IDE Compatibility](#ide-compatibility) — Windsurf, VS Code, Enterprise, cross-tool support

## How the Template Files Relate

Each phase feeds into the next. The overview shows the big picture; the per-phase diagrams show every file.

> **[Download all diagrams as PDF](docs/rebuilder-architecture-diagrams.pdf)**

#### Overview — Three Phases

```mermaid
flowchart LR
    subgraph P1 ["Phase 1 — Analyze"]
        direction TB
        IN["scope.md + input.md<br/>repo/ + adjacent/"]
        RUN["run.sh → IDEATION_PROCESS.md<br/>(18 steps)"]
        OUT["PRD, ADRs, agent configs,<br/>feature parity, data mapping"]
        IN --> RUN --> OUT
    end

    subgraph P2 ["Phase 2 — Build"]
        direction TB
        COPY["Copy configs →<br/>new target repo"]
        SHIM["IDE shim auto-loads<br/>developer-agent/skill.md<br/>+ config.md"]
        BUILD["AI agent builds service<br/>from PRD + standards"]
        COPY --> SHIM --> BUILD
    end

    subgraph P3 ["Phase 3 — Operate"]
        direction TB
        ALERT["Monitoring alert fires"]
        SRE["SRE agent diagnoses<br/>via /ops/* endpoints"]
        ACT["Remediates or<br/>escalates to PagerDuty"]
        ALERT --> SRE --> ACT
    end

    OUT -->|"populated configs + PRD"| COPY
    BUILD -->|"deployed service with<br/>/ops/* endpoints"| ALERT

    style P1 fill:#e8f4f8,stroke:#2c7bb6
    style P2 fill:#e8f0e4,stroke:#4daf4a
    style P3 fill:#fef3e0,stroke:#ff7f00
```

---

#### Phase 1 — Analyze (detail)

`run.sh` copies templates into the project directory and invokes the AI agent, which follows `IDEATION_PROCESS.md` to produce all outputs.

```mermaid
flowchart TB
    subgraph INPUTS ["Inputs  (auto-populated, human-reviewed)"]
        REPO["repo/<br/>Legacy codebase"]
        ADJ["adjacent/<br/>Related repos (optional)"]
        SCOPE["scope.md<br/>Current + target state"]
        INPUT["input.md<br/>Tech stack, APIs, pain points"]
    end

    RUNNER["rebuild/run.sh<br/>Creates output dirs, copies templates"]
    PROCESS["IDEATION_PROCESS.md<br/>18-step prescribed process"]
    STANDARDS["STANDARDS.md<br/>Architecture & migration standards"]

    subgraph TEMPLATES ["Templates  (copied by run.sh — never edited in place)"]
        DEV_TPL["developer-agent/<br/>skill.md + config.md"]
        QA_TPL["qa-agent/<br/>skill.md + config.md<br/>+ examples/"]
        SRE_TPL["sre-agent/<br/>skill.md + config.md"]
        DOC_TPL["docs/ templates<br/>cutover-report, disaster-recovery,<br/>feature-parity, data-migration"]
    end

    subgraph OUTPUTS ["Outputs  (written to rebuild-inputs/project/)"]
        ASSESS["output/<br/>legacy_assessment.md<br/>modernization_opportunities.md<br/>feasibility.md · candidate_N.md"]
        PRD["output/prd.md"]
        ADRS["docs/adr/*.md"]
        FP["docs/feature-parity.md<br/>docs/data-migration-mapping.md"]
        DEV_POP["developer-agent/<br/>skill.md + config.md<br/>(populated)"]
        QA_POP["qa-agent/<br/>config.md (populated)<br/>skill.md + examples/ (universal)"]
        SRE_POP["sre-agent/<br/>skill.md + config.md<br/>(populated)"]
    end

    SCOPE & INPUT --> RUNNER
    RUNNER -->|"copies"| TEMPLATES
    RUNNER -->|"launches AI agent"| PROCESS
    REPO & ADJ --> PROCESS
    SCOPE & INPUT --> PROCESS
    STANDARDS --> PROCESS
    PROCESS -->|"Steps 1–5"| ASSESS
    ASSESS -->|"Step 6"| PRD
    PRD -->|"Steps 7–8"| DEV_POP & QA_POP & SRE_POP
    DEV_TPL -.->|"template for"| DEV_POP
    QA_TPL -.->|"template for"| QA_POP
    SRE_TPL -.->|"template for"| SRE_POP
    DOC_TPL -.->|"template for"| FP
    PRD -->|"Steps 9–11"| ADRS & FP

    style INPUTS fill:#dceefb,stroke:#2c7bb6
    style TEMPLATES fill:#fff3cd,stroke:#d4a017
    style OUTPUTS fill:#d4edda,stroke:#28a745
```

---

#### Phase 2 — Build (detail)

Phase 1 outputs are copied into a new repo. IDE shim files auto-load the developer and QA agent standards on every session.

```mermaid
flowchart TB
    PRD["output/prd.md<br/>(from Phase 1)"]
    DEV_POP["developer-agent/<br/>skill.md + config.md<br/>(populated in Phase 1)"]
    QA_POP["qa-agent/<br/>skill.md + config.md<br/>(populated in Phase 1)"]
    SRE_POP["sre-agent/ configs<br/>(populated in Phase 1)"]
    ADRS["docs/adr/*.md<br/>(from Phase 1)"]
    FP["docs/ mappings<br/>(from Phase 1)"]

    COPY["Copy all into<br/>new target repo"]
    NEW_REPO["New target repo"]

    subgraph IDE_LOAD ["IDE auto-loading  (happens on every session)"]
        SHIM[".windsurfrules<br/>.github/copilot-instructions.md<br/>AGENTS.md"]
        DEV_AGENT["Developer agent reads<br/>developer-agent/skill.md + config.md"]
        QA_AGENT["QA agent reads<br/>qa-agent/skill.md + config.md"]
        SHIM -->|"IDE auto-reads<br/>on session start"| DEV_AGENT & QA_AGENT
    end

    CODE["Built codebase<br/>API-first service, /ops/* endpoints,<br/>tests, Terraform, CI/CD, OTEL"]
    AUDIT["Steps 12–18<br/>Compliance audit, TEST_RESULTS.md,<br/>QA verification, summary-of-work.md"]

    PRD & DEV_POP & QA_POP & SRE_POP & ADRS & FP --> COPY --> NEW_REPO --> IDE_LOAD
    DEV_AGENT -->|"builds from PRD<br/>following standards"| CODE
    CODE --> AUDIT
    QA_AGENT -->|"verifies developer<br/>agent's output"| AUDIT

    style IDE_LOAD fill:#fff3cd,stroke:#d4a017
```

---

#### Phase 3 — Operate (detail)

The SRE agent receives monitoring alerts, diagnoses issues via the service's `/ops/*` endpoints, and remediates or escalates.

```mermaid
flowchart TB
    ALERTS["Monitoring alerts<br/>(Cloud Monitoring, New Relic, Datadog)"]
    SRE_RUNTIME["sre-agent/runtime/<br/>FastAPI webhook receiver<br/>+ agentic diagnostic loop"]
    SRE_SKILL["sre-agent/skill.md<br/>(loaded as system prompt)"]
    SRE_CONFIG["sre-agent/config.md<br/>Service registry, SLOs, PagerDuty"]
    PLAYBOOKS["sre-agent/playbooks/<br/>high-error-rate · high-latency<br/>dependency-failure · saturation<br/>service-down · certificate-expiry"]
    OPS["Service /ops/* endpoints<br/>(built in Phase 2)"]
    INCIDENTS["sre-agent/incidents/<br/>Incident reports"]
    PD["PagerDuty escalation"]

    ALERTS --> SRE_RUNTIME
    SRE_SKILL -->|"system prompt"| SRE_RUNTIME
    SRE_CONFIG --> SRE_RUNTIME
    PLAYBOOKS --> SRE_RUNTIME
    SRE_RUNTIME -->|"calls for diagnosis<br/>& remediation"| OPS
    SRE_RUNTIME --> INCIDENTS
    SRE_RUNTIME -->|"escalates<br/>when unsure"| PD
```

### Quick Reference: Which File Does What

The rebuilder is a fully automated process — the AI agent reads the legacy codebase and populates all files. Humans review and adjust before proceeding, but do not need to fill anything out manually.

| File | Role | When It's Used |
|---|---|---|
| `scope.md` | Defines current app + target state | Auto-populated from legacy code; human reviews/adjusts before proceeding |
| `rebuild/input.md` | Detailed tech stack, APIs, pain points | Auto-populated from legacy code; human reviews/adjusts before proceeding |
| `rebuild/run.sh` | Creates output dirs, copies templates, launches AI agent | Start of Phase 1 |
| `rebuild/IDEATION_PROCESS.md` | 18-step prescribed analysis + build process | AI agent follows during Phases 1 & 2 |
| `STANDARDS.md` | Architecture, scaling, security, testing standards | Referenced throughout all phases |
| `AGENTS.md` | Cross-tool agent bootstrap — points all AI tools to agent files | Always-on in Windsurf; depends on tool support elsewhere |
| `.windsurfrules` | IDE shim — tells Windsurf to read developer-agent + qa-agent skill.md and config.md | Auto-read by Windsurf on every session start |
| `.github/copilot-instructions.md` | IDE shim — tells VS Code Copilot to read developer-agent + qa-agent skill.md and config.md | Auto-included in every Copilot Chat interaction |
| `.windsurf/skills/legacy-rebuild/` | Windsurf Skill — progressive disclosure entry point for the rebuild process | Invoked on demand when user says "rebuild" or "replicator" |
| `developer-agent/skill.md` | Dev coding standards (template → populated) | Template in Phase 1; auto-loaded by IDE shims in Phase 2 |
| `developer-agent/config.md` | Project-specific dev config (template → populated) | Template in Phase 1; auto-loaded by IDE shims in Phase 2 |
| `qa-agent/skill.md` | QA verification procedures + quality gates (universal) | Template in Phase 1; auto-loaded by IDE shims in Phase 2 |
| `qa-agent/config.md` | Project-specific QA config (template → populated) | Template in Phase 1; auto-loaded by IDE shims in Phase 2 |
| `sre-agent/skill.md` | SRE diagnostic workflow + safety constraints | Template in Phase 1; system prompt in Phase 3 |
| `sre-agent/config.md` | Service registry, SLOs, PagerDuty config | Template in Phase 1; runtime config in Phase 3 |
| `sre-agent/playbooks/*.md` | Remediation runbooks by incident type | Phase 3 — agent follows during incidents |
| `sre-agent/runtime/` | Deployable FastAPI service for alert handling | Phase 3 — receives webhooks, runs agentic loop |
| `docs/*.md` | Migration planning templates (feature parity, data mapping, DR, cutover) | Templates copied in Phase 1; filled during Phases 1–2 |
| `output/*.md` | Analysis artifacts + PRD | Written by AI agent in Phase 1 |

## Repository Structure

```
rebuilder-template/
├── STANDARDS.md                # Migration reference — architecture, data migration, cutover, DR, ADRs
├── README.md                  # This file
├── spec-driven-development.md # Leadership doc — reproducibility, agent architecture
├── spec-process-overview.md   # Process overview — high-level summary of the rebuild workflow
├── scope.md                   # Scope template — copy to a working directory before filling out
├── prompting.md               # Audit trail of prompting commands and outcomes
├── AGENTS.md                  # Cross-tool agent bootstrap (Windsurf, Claude Code, others)
├── .gitignore                 # Python, Terraform, IDE, OS ignores + rebuild-inputs/
├── .windsurfrules             # Windsurf IDE — loads developer-agent + qa-agent skill.md and config.md
├── .github/
│   ├── copilot-instructions.md    # VS Code Copilot — loads developer-agent + qa-agent skill.md and config.md
│   └── PULL_REQUEST_TEMPLATE.md   # PR template — engineer sign-off
├── rebuild/
│   ├── IDEATION_PROCESS.md    # The rebuild analysis process definition (18 steps)
│   ├── input.md               # Input template — copy to a working directory before filling out
│   └── run.sh                 # Runner script — creates output structure in the input directory
├── rebuild-inputs/            # Per-project working directories (gitignored)
│   └── <project-name>/       # One directory per rebuild project
│       ├── repo/                         # Cloned primary legacy codebase
│       ├── adjacent/                     # Optional: related repos included in rebuild scope
│       │   └── <related-repo>/
│       ├── scope.md                      # Filled-out scope
│       ├── input.md                      # Filled-out input
│       ├── output/                       # Steps 1-6: analysis artifacts and PRD
│       │   ├── legacy_assessment.md
│       │   ├── modernization_opportunities.md
│       │   ├── feasibility.md
│       │   ├── candidate_N.md
│       │   ├── prd.md
│       │   ├── summary-of-work.md         # Build summary — what was built, commits, quality gates
│       │   ├── compliance-audit.md        # Compliance audit results
│       │   └── process-feedback.md        # Process improvement notes
│       ├── developer-agent/              # Step 8: populated dev agent config
│       │   ├── skill.md
│       │   └── config.md
│       ├── qa-agent/                     # Step 8d: populated QA agent config
│       │   ├── skill.md
│       │   ├── config.md
│       │   ├── TEST_RESULTS_TEMPLATE.md
│       │   └── examples/
│       ├── sre-agent/                    # Step 7: populated SRE agent config
│       │   ├── skill.md
│       │   └── config.md
│       └── docs/
│           ├── adr/                      # Step 9: architecture decision records
│           │   └── *.md
│           ├── feature-parity.md         # Step 10: feature parity matrix
│           ├── data-migration-mapping.md  # Step 11: schema mapping
│           ├── cutover-report.md         # Template — filled post-cutover
│           └── disaster-recovery.md      # Template — filled during ops setup
├── docs/                      # Migration planning document templates
│   ├── data-migration-mapping.md  # Schema mapping between legacy and target
│   ├── feature-parity.md         # Feature parity matrix and status tracking
│   ├── cutover-report.md         # Post-cutover documentation
│   ├── disaster-recovery.md      # DR plan — RTO/RPO, backups, runbooks
│   ├── rebuilder-architecture-diagrams.pdf  # Downloadable PDF of all mermaid diagrams
│   ├── adr/                      # Template directory (generated ADRs go in rebuild-inputs/)
│   └── postmortems/              # Incident postmortems
├── developer-agent/
│   ├── README.md              # Developer agent overview
│   ├── skill.md               # Daily dev instructions template — coding, testing, CI/CD, environments, bootstrap
│   ├── config.md              # Per-project config template — commands, environments, services, CI/CD
│   ├── .windsurfrules         # Windsurf IDE hook — reads developer-agent + qa-agent on session start
│   └── .github/
│       └── copilot-instructions.md  # VS Code Copilot hook — reads developer-agent + qa-agent
├── qa-agent/
│   ├── README.md              # QA agent overview — activation, customization, IDE usage
│   ├── skill.md               # QA verification procedures — quality gates, test strategy, /ops/* contract
│   ├── config.md              # Per-project QA config template — thresholds, env vars, acceptance criteria
│   ├── TEST_RESULTS_TEMPLATE.md  # Quality gate report template
│   └── examples/              # Example test patterns for rebuilt services
│       ├── conftest.py        # Fixtures — OTEL disable, env vars, sys.modules mocks
│       ├── test_routes.py     # API endpoint tests — status, health, main endpoint
│       ├── test_ops_endpoints.py  # /ops/* SRE contract tests (14 endpoints)
│       └── e2e/               # E2E shell scripts for live instance verification
│           ├── test_health.sh
│           ├── test_ops_contract.sh
│           └── test_smoke.sh
├── sre-agent/
│   ├── README.md              # SRE agent overview
│   ├── skill.md               # SRE agent instructions template — diagnostic workflow and response framework
│   ├── config.md              # Per-project config template — service registry, SLOs, PagerDuty, escalation
│   ├── playbooks/             # Remediation playbooks by incident type
│   │   ├── high-error-rate.md
│   │   ├── high-latency.md
│   │   ├── dependency-failure.md
│   │   ├── saturation.md
│   │   ├── service-down.md
│   │   └── certificate-expiry.md
│   ├── incidents/             # Agent-written incident reports
│   └── runtime/               # SRE agent runtime service
│       ├── README.md          # Architecture, setup, and deployment guide
│       ├── main.py            # FastAPI webhook receiver + alert intake pipeline
│       ├── agent.py           # Agentic loop — OpenAI-compatible LLM orchestration
│       ├── tools.py           # Tool definitions and executor
│       ├── intake.py          # Alert dedup, service serialization, priority queue
│       ├── config.py          # Configuration from environment variables
│       ├── models.py          # Pydantic models for alert payloads
│       ├── state.py           # Runtime state tracking for Golden Signals
│       ├── telemetry.py       # OpenTelemetry instruments
│       ├── pagerduty_setup.py # PagerDuty service/escalation bootstrapper
│       ├── deploy.sh          # Deployment script
│       ├── requirements.txt   # Python dependencies
│       ├── requirements-dev.txt # Dev dependencies — pytest, ruff
│       ├── pyproject.toml     # Linter and test configuration
│       ├── .env.example       # Environment variable template
│       ├── Dockerfile         # Container image
│       ├── tests/             # Unit and API tests
│       └── terraform/         # Cloud Run deployment
│           ├── main.tf
│           ├── variables.tf
│           ├── outputs.tf
│           └── deploy.auto.tfvars
└── .windsurf/
    ├── skills/                # Windsurf Skills — progressive disclosure, auto-invoked
    │   └── legacy-rebuild/    # @legacy-rebuild — rebuild process entry point
    │       └── SKILL.md
    └── workflows/             # Windsurf workflow definitions
        ├── developer.md       # /developer — reload developer + QA agent mid-session
        ├── qa.md              # /qa — run all quality gates and generate verification report
        ├── populate-templates.md
        └── run-replicator.md  # /run-replicator — invokes @legacy-rebuild skill
```

## How to Use

### Quick Start (Windsurf)

Open this repo in Windsurf and tell Cascade what you want to rebuild:

> **"Rebuild evergreen-tvevents"**

Cascade invokes the `@legacy-rebuild` skill, sets up the project directory, and runs the 18-step analysis. You review the outputs and guide the build.

### Quick Start (VS Code + Copilot)

Open this repo in VS Code. Copilot auto-loads `.github/copilot-instructions.md`, which reads the developer and QA agent files. Tell Copilot:

> **"Read rebuild/IDEATION_PROCESS.md and rebuild evergreen-tvevents"**

VS Code does not have Windsurf's `/run-replicator` workflow or `@legacy-rebuild` skill, so you reference the process file directly. The agent follows the same 18-step process — it just needs the explicit pointer.

### Phase 1: Analyze

Tell the agent which legacy repo to rebuild. It clones the repo, creates the project directory, copies templates, and executes Steps 1–11.

#### Windsurf

| What you want | What to say |
|---|---|
| Rebuild a single service | *"Rebuild my-service"* |
| Rebuild with related repos | *"Rebuild my-service with adjacent repos auth-api and worker-app"* |
| Use the workflow directly | `/run-replicator` on my-service |

#### VS Code + Copilot

| What you want | What to say |
|---|---|
| Rebuild a single service | *"Read rebuild/IDEATION_PROCESS.md and rebuild my-service. The repo is at github.com/your-org/my-service."* |
| Rebuild with related repos | *"Read rebuild/IDEATION_PROCESS.md and rebuild my-service with adjacent repos auth-api and worker-app."* |

All outputs land in `rebuild-inputs/<project>/`.

> [!IMPORTANT]
> Review the outputs — especially `scope.md` Target State and `output/prd.md`. The Current Application section comes from the code; the Target State comes from your decisions. Adjust before proceeding to the build phase.

### Phase 2: Build

After reviewing the Phase 1 outputs, create a new repo and ask the agent to build it:

> *"Create a new repo for the rebuilt service and build it from the PRD."*

This prompt works in both Windsurf and VS Code. The agent copies the populated agent configs, PRD, ADRs, and docs into the new repo. In the new repo, the developer and QA agents auto-load via `.windsurfrules` (Windsurf) or `.github/copilot-instructions.md` (VS Code).

After the code is written:
- **Windsurf:** Run `/qa` to independently verify quality gates.
- **VS Code:** Ask Copilot: *"Read qa-agent/skill.md and run the full QA verification."*

### Phase 3: Operate

Deploy the SRE agent from `sre-agent/runtime/`. Fill in `sre-agent/config.md` with service registry URLs and PagerDuty escalation config. The agent receives monitoring webhooks, diagnoses issues via `/ops/*` endpoints, and escalates when it can't resolve. See `sre-agent/runtime/README.md` for deployment instructions.

### Quick Reference

| Action | Windsurf | VS Code + Copilot |
|---|---|---|
| Rebuild a service | *"Rebuild my-service"* | *"Read rebuild/IDEATION_PROCESS.md and rebuild my-service"* |
| Run QA verification | `/qa` | *"Read qa-agent/skill.md and run QA verification"* |
| Reload agent standards | `/developer` | *"Re-read developer-agent/skill.md and qa-agent/skill.md"* |
| Explore the rebuild process | *"@legacy-rebuild what steps are in the process?"* | *"Read rebuild/IDEATION_PROCESS.md and summarize the steps"* |

## What Gets Generated

All outputs are written into the project directory under `rebuild-inputs/<project-name>/`:

| Output | Location | Description |
|---|---|---|
| Legacy assessment | `output/legacy_assessment.md` | Architecture, code, ops, data, infrastructure, and DX health ratings |
| Modernization opportunities | `output/modernization_opportunities.md` | Ranked list tied to real pain points (includes infra migration if applicable) |
| Feasibility analysis | `output/feasibility.md` | Effort, risk, dependencies, rollback per opportunity |
| Rebuild candidates | `output/candidate_N.md` | Concrete proposals with stack choices, phased scope, infrastructure migration plan, and DAPR integration notes |
| PRD | `output/prd.md` | Product requirements including infrastructure migration plan and DAPR integration if changing providers |
| Summary of work | `output/summary-of-work.md` | Build summary — what was built, commits, quality gates |
| Compliance audit | `output/compliance-audit.md` | Compliance audit results |
| Process feedback | `output/process-feedback.md` | Process improvement notes |
| ADRs | `docs/adr/*.md` | Architecture decision records |
| Feature parity matrix | `docs/feature-parity.md` | Every feature cataloged with rebuild status |
| Data migration mapping | `docs/data-migration-mapping.md` | Schema mapping between legacy and target |
| Developer agent config | `developer-agent/skill.md` + `config.md` | Project name, architecture, commands, CI/CD, environments |
| QA agent config | `qa-agent/skill.md` + `config.md` + `TEST_RESULTS_TEMPLATE.md` + `examples/` | QA verification procedures, project-specific acceptance criteria, example test patterns |
| SRE agent config | `sre-agent/skill.md` + `config.md` | Tech stack, service registry, SLO thresholds |

## Developer Agent

The `developer-agent/` directory contains the daily development instructions for AI-assisted coding sessions. It ensures every service and component in the rebuild is built to the same standards.

**What it covers:**
- **Coding practices** — error handling, security, input validation, dependency management, removal of outdated code (DP2.5, Stackdriver), no SRE Agent for library repos
- **Testing** — unit, API, integration, contract, E2E expectations
- **CI/CD pipeline** — lint → test → build → scan → deploy-to-dev → integration tests → promote-to-staging → E2E → promote-to-prod
- **Environment strategy** — dev/staging/prod with promotion flow, environment parity, rollback via image SHA
- **Service bootstrap** — checklist of what every new service ships with from its first PR (Dockerfile, CI pipeline, Terraform, `/ops/*` endpoints, OpenAPI spec, tests)
- **Terraform workflow** — plan on PR, apply on merge, remote state, environment-specific variables
- **Observability** — Golden Signals, RED method, SLOs, `/ops/*` endpoints as definition of done

**Components:**
- **`skill.md`** — the development instructions. Loaded automatically via IDE instruction files (`.windsurfrules`, `.github/copilot-instructions.md`).
- **`config.md`** — per-project configuration: dev commands, CI/CD pipeline, environments, services, secrets references, monitoring links.

> [!TIP]
> **How it connects to the rebuild:** The rebuild process (`run.sh`) auto-populates `skill.md` and `config.md` from the PRD and chosen rebuild candidate (Step 7). Project name, architecture, development commands, CI/CD pipeline, Terraform settings, and observability config are filled in before the first line of code is written. Copy both files into the target repo, and the AI agent will follow the standards defined by the rebuild process.

## QA Agent

The `qa-agent/` directory contains quality verification procedures for rebuilt services. The QA agent independently verifies that the developer agent's output meets quality standards — it does **not** replace the developer agent, it checks it.

**What it does:**
1. **Re-runs every quality gate independently** — pytest, coverage, ruff, mypy, radon, vulture, pip-audit, interrogate, pylint, jscpd, C901. Compares results against the developer agent's `TEST_RESULTS.md` and flags discrepancies.
2. **Verifies `/ops/*` endpoint compliance** — checks that every required diagnostic and remediation endpoint exists and returns the correct fields per the SRE contract.
3. **Checks template conformance** — Dockerfile, entrypoint.sh, Helm chart, environment-check.sh, IDE instruction files must match template patterns.
4. **Produces an independent quality report** — generates `TEST_RESULTS.md` from its own gate runs, not from the developer agent's claims.
5. **Flags gaps for human review** — categorizes findings as Critical / Important / Minor. Does not silently fix business logic.

**Components:**
- **`skill.md`** — QA verification procedures: 5-level test strategy, 11 quality gates, `/ops/*` contract verification, acceptance criteria framework, comparison workflow, and bug reporting protocol. This file is universal — the same standards apply to every rebuilt service.
- **`config.md`** — per-project QA configuration: test commands, quality gate thresholds, env var mapping, mock strategy, endpoint list, event types, and acceptance criteria. **Human operators customize this file** to add app-specific checks and adjust thresholds.
- **`TEST_RESULTS_TEMPLATE.md`** — template for the quality gate report. Includes sections for tool versions, codebase metrics, core and extended gate results, bugs found, untestable items, and template conformance.
- **`examples/`** — example test patterns including `conftest.py` (fixtures), `test_routes.py` (API tests), `test_ops_endpoints.py` (`/ops/*` contract tests), and E2E shell scripts for live instance verification.

**How it's activated:**
- **Always-on** — IDE instruction files (`.windsurfrules`, `.github/copilot-instructions.md`) load both developer and QA agent files on every session, giving the AI assistant awareness of both development standards and verification criteria.
- **On-demand** — Type `/qa` in Windsurf to run the full QA verification workflow. Type `/developer` to reload all agent files mid-session.

> [!TIP]
> **How it connects to the rebuild:** The rebuild process (`run.sh`) auto-populates `config.md` from the PRD and developer agent config (Step 8d). Endpoint lists, env var mappings, and mock strategies are filled in before the first quality check. Human operators then customize the acceptance criteria — adding app-specific checks, adjusting thresholds, and defining verification rules beyond the universal standards. After the developer agent claims compliance (Step 12), activate the QA agent via `/qa` to independently verify.

## SRE Agent

The `sre-agent/` directory contains a complete, deployable SRE agent that provides automated incident response for your rebuilt services.

**What it does:**
1. **Receives alerts from monitoring platforms** — webhooks from GCP Cloud Monitoring, New Relic, Datadog, or similar trigger the agent. The alert intake pipeline deduplicates by incident ID, serializes per service, enforces a global concurrency limit (default: 3), and orders queued alerts by priority.
2. **Diagnoses issues** — calls `/ops/status`, `/ops/health` (includes dependency health with latency), `/ops/metrics`, and `/ops/errors` on the affected service. Follows the dependency chain to find the root cause.
3. **Classifies the problem** — infrastructure, application, dependency, data, or configuration.
4. **Remediates safely** — executes playbook-defined actions (cache flush, cache refresh, circuit breaker reset, log level adjustment). All actions are idempotent and non-destructive.
5. **Escalates when unsure** — if no playbook matches, remediation fails, or the issue involves data integrity, security, or infrastructure changes, the agent escalates to a human via PagerDuty with a full diagnostic summary.
6. **Tracks token usage** — every API call's token consumption is tracked per incident and globally. Configurable per-incident and hourly token budgets prevent runaway costs — the agent auto-escalates to a human when a budget is exceeded.
7. **Documents everything** — writes an incident report for every alert it responds to, including token usage.

**Components:**
- **`skill.md`** — the agent's instructions, diagnostic workflow, escalation rules, and hard safety constraints. **This file is the agent's brain.** On every alert, `agent.py` reads it from disk and sends the full text to the LLM as the `system` message — the first message in the conversation. The alert becomes the first `user` message. Everything the agent knows, every decision it makes, and every constraint it follows comes from this file. The runtime code is generic infrastructure; `skill.md` is what makes it an SRE agent.
- **`config.md`** — per-project configuration: service registry, SLO thresholds, PagerDuty escalation config, escalation contacts, cloud platform IAM roles, and runtime environment variables.
- **`playbooks/`** — remediation playbooks for common incident types (high error rate, high latency, dependency failure, saturation, certificate expiry).
- **`incidents/`** — agent-written incident reports with diagnosis, actions taken, and resolution status.
- **`runtime/`** — the deployable Python/FastAPI service. Receives monitoring platform webhooks, runs the agentic loop, executes tool calls, and escalates to PagerDuty when needed. Includes alert intake pipeline, token budget controls, OpenTelemetry instrumentation, Dockerfile, and Terraform templates for Cloud Run. See `sre-agent/runtime/README.md` for setup and deployment.

> [!TIP]
> **How it connects to the rebuild:** The rebuild process (`run.sh`) auto-configures the agent's tech stack from the chosen rebuild candidate (Step 7). Your rebuilt services expose `/ops/*` endpoints as defined in `STANDARDS.md`. The agent uses those endpoints to monitor and respond to incidents. Fill in `config.md` with your service URLs, PagerDuty escalation config, and escalation contacts, deploy the runtime, and the agent is operational.

## IDE Compatibility

The rebuilder template supports multiple IDEs through layered bootstrap mechanisms. Each mechanism points to the same canonical agent files (`developer-agent/skill.md`, `developer-agent/config.md`, `qa-agent/skill.md`, `qa-agent/config.md`).

| IDE | Bootstrap File | Auto-loaded | Notes |
|---|---|---|---|
| **Windsurf** | `.windsurfrules` | Yes — every session | Also discovers `AGENTS.md` and `.windsurf/skills/` |
| **VS Code + GitHub Copilot** | `.github/copilot-instructions.md` | Yes — every Copilot Chat | Reads agent files on demand |
| **Other tools** | `AGENTS.md` | Depends on tool support | Cross-tool standard; adopted by Claude Code and others |

### Windsurf-Specific Features

Windsurf users get additional capabilities through the `.windsurf/` directory:

- **Skills** (`.windsurf/skills/`) — Progressive disclosure: only the skill name and description are in the system prompt. Full content loads on demand. The `@legacy-rebuild` skill wraps the 90KB ideation process so it never occupies context unless invoked.
- **Workflows** (`.windsurf/workflows/`) — Manual slash commands: `/run-replicator`, `/qa`, `/developer`, `/populate-templates`.
- **Rules** — `.windsurfrules` at the repo root is always-on. `AGENTS.md` at the root is treated as an always-on rule.

### Windsurf Enterprise

For organizations on Windsurf Enterprise, system-level Skills and Rules can be deployed to all workspaces via IT-managed paths:

| OS | Skills Path | Rules Path |
|---|---|---|
| macOS | `/Library/Application Support/Windsurf/skills/` | `/Library/Application Support/Windsurf/rules/` |
| Linux/WSL | `/etc/windsurf/skills/` | `/etc/windsurf/rules/` |
| Windows | `C:\ProgramData\Windsurf\skills\` | `C:\ProgramData\Windsurf\rules\` |

This allows org-wide development standards to be enforced as read-only rules that individual developers cannot override. Project-specific config (`config.md`) remains at the workspace level.

### Cursor

Cursor IDE support (`.cursorrules`) is not currently included in this template. Cursor users can manually read the agent files or use `AGENTS.md` if their tool supports it. Adding `.cursorrules` is a future consideration — contributions welcome.

