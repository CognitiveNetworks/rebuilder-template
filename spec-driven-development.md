# Spec-Driven Development: Reproducibility Contract

> How the Replicator process produces predictable, auditable rebuilds — and
> why an LLM-driven pipeline doesn't generate unicorns every time.

## The Problem This Solves

An LLM given the prompt "rebuild this Python service" will produce a different
result every time. Different file structures, different naming conventions,
different test patterns, different levels of observability. The output depends
on the model's training data, temperature settings, and whatever the model
"feels like" doing that day. This is unacceptable for engineering organizations
that need consistency, auditability, and predictable quality.

Replicator eliminates this variance by converting "rebuild this service" into a
structured contract between **inputs** (what you provide), **process** (what
the agent executes), and **outputs** (what gets delivered). The LLM is
constrained to operate within this contract — it fills in the blanks, it
doesn't decide what the blanks are.

## The Contract

```
┌─────────────────────────────────────────────────────────┐
│                        INPUTS                            │
│                                                          │
│  scope.md          What the app is, what it should be    │
│  input.md          Tech stack, APIs, dependencies, auth  │
│  repo/             The actual legacy source code         │
│  adjacent/         Related repos (optional)              │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                       PROCESS                            │
│                                                          │
│  IDEATION_PROCESS.md   18 prescribed steps               │
│  WINDSURF_DEV.md       Coding standards + checklists     │
│  WINDSURF.md           Architecture standards            │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                       OUTPUTS                            │
│                                                          │
│  18 named artifacts    Fixed structure, fixed location    │
│  Built codebase        Standards-compliant, tested        │
│  Agent configs         Populated, IDE-loadable            │
│  Quality receipt       TEST_RESULTS.md with gate results  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**The key insight:** the process document defines the *structure* of every
output artifact — section headings, table columns, required fields. The LLM
fills in *values* derived from the inputs. This is closer to form-filling than
creative writing.

## What Is Fixed vs. What Varies

### Fixed (identical across runs)

These elements are prescribed by the process and standards documents. A fresh
agent starting from the same inputs will produce structurally identical results:

| Element | Prescribed by | Example |
|---|---|---|
| Output file names and locations | IDEATION_PROCESS.md | `output/prd.md`, `docs/adr/001-*.md` |
| Document structures | IDEATION_PROCESS.md step templates | PRD has Background, Goals, Non-Goals, etc. |
| API contract (`/ops/*` endpoints) | WINDSURF.md + WINDSURF_DEV.md Step 12 | 11 diagnostic/remediation endpoints per service |
| Quality gates (14 gates) | WINDSURF_DEV.md Step 12 | pytest, ruff, mypy, radon, vulture, pip-audit, etc. |
| Service bootstrap checklist | WINDSURF_DEV.md | Dockerfile, CI/CD, Terraform, health endpoint, OTEL |
| Code audit checklist (14 items) | WINDSURF_DEV.md | Timing-safe comparisons, pool close, backoff, etc. |
| Pre-commit checklist (5 steps) | WINDSURF_DEV.md | Branch check, tests, lint, message, diff review |
| Test data requirements | WINDSURF_DEV.md + Step 13a | Domain-realistic identifiers, no `abc123` |
| Commit message format | WINDSURF_DEV.md | Summary + structured body via `git commit -F` |
| IDE instruction files | Step 8 (7c) | `.windsurfrules`, `.github/copilot-instructions.md` |
| Agent role framing | WINDSURF_DEV.md Agent Role section | Agent is the developer, standards are binding |

### Determined by inputs (predictable given the same scope.md)

These elements vary between projects but are deterministic given the same
inputs. Two agents reading the same scope.md will converge on the same
decisions because the scope document explicitly states them:

| Element | Driven by | Example (tv-collection-services) |
|---|---|---|
| Service count and names | scope.md target architecture table | 8 services: mcp-router, tv-control, etc. |
| Tech stack | scope.md proposed tech stack | Python 3.12, FastAPI, DAPR, Terraform |
| Backward-compatible endpoints | scope.md "What Must Be Preserved" | `GET /control`, `POST /`, etc. |
| What to drop | scope.md "What Can Be Dropped" | DAI, ZeroMQ, Consul, New Relic agent |
| Cloud migration plan | scope.md target infrastructure | AWS → cloud-agnostic via DAPR |
| ADR topics | PRD → "ADRs Required" | Cloud provider, database, framework, orchestration |
| Feature parity entries | scope.md API surface + legacy assessment | Every endpoint cataloged with status |

### Varies (different path, same destination)

These elements may differ between runs but do not affect the functional
outcome. An engineer reviewing two independent runs would see equivalent
quality, not equivalent prose:

| Element | Why it varies | Impact |
|---|---|---|
| Narrative prose in docs | LLM word choice is non-deterministic | None — structure and facts are fixed |
| Implementation micro-decisions | Cache pattern, iterator style, variable names | Functionally equivalent |
| Test scenario narratives | Docstring wording, exact assertion messages | Quality is equivalent |
| ADR prose | Argument phrasing in Alternatives Considered | Conclusions are the same |
| Order of operations within a step | Agent may read files in different order | Results converge |

## How Reproducibility Is Achieved

### 1. Prescriptive process, not suggestive guidance

IDEATION_PROCESS.md does not say "consider writing a legacy assessment." It
says:

> Write results to `output/legacy_assessment.md` using this structure:
>
> ```
> # Legacy Assessment
> ## Application Overview
> ## Architecture Health
> - Rating: [Good / Acceptable / Poor / Critical]
> ...
> ```

Every step specifies: what file to create, what sections it must have, what
fields each section requires, and where the values come from. The agent has no
discretion about *whether* to produce the artifact or *how to structure* it —
only about *what values* to fill in based on the source code and scope document.

### 2. Input specificity drives output specificity

The single biggest lever on output quality is the specificity of `scope.md`.
Compare:

**Vague input → high variance:**
> "Modernize this Python service to use FastAPI."

An agent reading this has dozens of degrees of freedom: how many services? What
endpoints? What database? What auth model? Each run makes different choices.

**Specific input → low variance:**
> "Consolidate 8 services into a monorepo with independently deployable
> microservices. FastAPI, Python 3.12, DAPR sidecars, Terraform. Preserve
> `/control`, `/tvc`, `/cast_oobe_notification` endpoint URLs — firmware cannot
> be updated. Replace SQS with DAPR pub/sub. Replace Consul with DAPR service
> invocation. Drop DAI endpoints. Rebrand from Cognitive Networks to Inscape."

Two agents reading this will converge on the same architecture, same service
boundaries, same endpoint design. The scope document eliminates the decisions
that create variance.

**Implication for operators:** If you want reproducible output, write a
detailed scope.md. The more decisions you make in the scope document, the fewer
decisions the agent makes at runtime.

### 3. Compliance checklists act as convergence gates

Even when the implementation path varies, the compliance audit (Step 12) forces
convergence on the end state. The audit checks 30+ specific items:

- Does every endpoint have a Pydantic response model?
- Does `/health` return 503 when unhealthy?
- Does the Dockerfile use a pinned base image and non-root user?
- Do all 14 quality gates pass?

Two agents might implement a health endpoint differently — one as a function,
one as a class — but both must pass the same compliance check. The checklist is
the convergence mechanism: **different paths, same destination.**

### 4. Standards documents are binding, not advisory

The Agent Role section in WINDSURF_DEV.md establishes:

> **You are the developer on this project.** When you load this file, every
> standard in it becomes your operating procedure — not a reference document,
> not a style guide, but the rules you follow by default.

This framing was added specifically because early runs showed that agents treat
standards as "nice to have" unless explicitly told the standards are mandatory.
The distinction matters: an advisory document creates variance (the agent
decides whether to follow it); a binding document eliminates it.

### 5. The feedback loop closes gaps

Step 17 (Process Feedback Capture) requires that every manual correction the
operator gives during a run is analyzed and codified back into the process or
standards documents. This means:

- Run 1: Operator says "use realistic test data, not `abc123`"
- Gap identified: no standard for test data realism
- Fix applied: Step 13a added to IDEATION_PROCESS.md, realistic test data
  bullet added to WINDSURF_DEV.md Testing section
- Run 2: Agent produces realistic test data without being told

Each run makes the next run more reproducible. The process is a living document
that converges toward zero manual intervention over successive rebuilds.

## The Agent Architecture

Two agents operate during the lifecycle of a rebuilt service, each with a
distinct role, instruction set, and activation mechanism.

### Developer Agent

**When it runs:** During the rebuild (Phase 2) and ongoing development.

**How it loads:** The IDE reads an instruction file at repo root
(`.windsurfrules` for Windsurf, `.github/copilot-instructions.md` for VS Code
+ Copilot) which tells the agent to read `developer-agent/WINDSURF_DEV.md` and
`developer-agent/config.md` before any work.

**What it knows:**
- `WINDSURF_DEV.md` — coding practices, testing standards, CI/CD pipeline,
  environment strategy, service bootstrap checklist, code audit checklist,
  pre-commit checklist, observability requirements, and the Agent Role section
  that makes all of this binding
- `config.md` — project-specific configuration: dev commands, CI/CD pipeline
  details, environment URLs, service registry, secrets references

**What it does:**
- Writes code that conforms to the standards
- Runs tests and quality gates before every commit
- Checks itself against the code audit checklist
- Flags conflicts when a human request contradicts the standards
- Produces structurally consistent output across sessions and across projects

**What constrains it:**
- The Pre-Commit Checklist (5 steps: branch, tests, lint, commit message, diff
  review) must be completed before every commit
- The Code Audit Checklist (14 items across security, connections,
  correctness, dependencies) must be checked before declaring code complete
- The Service Bootstrap Checklist defines the minimum viable first PR
- Quality gates (14 automated checks) must all pass

**Key property:** The developer agent is stateless between sessions. It reloads
WINDSURF_DEV.md at the start of every session. This means improvements to the
standards document immediately affect the next session — no retraining, no
redeployment. The document *is* the agent's behavior.

### SRE Agent

**When it runs:** After deployment (Phase 3), triggered by monitoring alerts.

**How it loads:** `agent.py` reads `WINDSURF_SRE.md` from disk and sends it as
the system prompt to the LLM on every alert. The file is the agent's entire
operating procedure.

**What it knows:**
- `WINDSURF_SRE.md` — diagnostic workflow, escalation rules, safety
  constraints, playbook references, tool definitions
- `config.md` — service registry (URLs), SLO thresholds, PagerDuty
  configuration, escalation contacts, cloud platform access

**What it does:**
1. Receives an alert from the monitoring platform (webhook)
2. Calls `/ops/*` diagnostic endpoints on the affected service
3. Classifies the problem (infrastructure, application, dependency, data,
   configuration)
4. Executes playbook-defined remediation (cache flush, circuit reset, drain,
   log level, bounded scaling)
5. Escalates to a human via PagerDuty when it cannot confidently resolve

**What constrains it:**
- Hard safety constraints: no data deletion, no schema changes, no credential
  rotation, no unbounded scaling
- Token budget per incident and per hour — auto-escalates when exceeded
- Every action is idempotent and non-destructive
- Every alert produces a written incident report

**Key property:** Like the developer agent, the SRE agent is prompt-driven. Its
behavior is defined entirely by `WINDSURF_SRE.md`. Changing the instruction
file changes the agent's behavior on the next alert. Playbooks in `playbooks/`
extend its remediation capabilities without code changes.

### How the Agents Relate

```
                    IDEATION_PROCESS.md
                    (18-step analysis)
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
     developer-agent/            sre-agent/
     WINDSURF_DEV.md            WINDSURF_SRE.md
     config.md                  config.md
              │                       │
              ▼                       ▼
     Phase 2: Build              Phase 3: Operate
     (IDE sessions)              (alert webhooks)
              │                       │
              ▼                       ▼
     Built service ──────────► /ops/* endpoints
     with /ops/* endpoints     consumed by SRE agent
```

The developer agent creates the service. The SRE agent operates it. Both are
configured by the same rebuild process. The developer agent's standards ensure
the service exposes the `/ops/*` endpoints that the SRE agent requires. This is
not accidental — it is a designed contract.

## Reproducibility Evidence

### Measured: tv-collection-services

The tv-collection-services rebuild was the first full-scale run of this
process. After the build was complete, we ran the thought experiment:
"If a fresh agent started from only the template and the same inputs, would
it arrive at the same place?"

**Assessment: ~97% reproducible.**

| Category | Reproducibility | Why |
|---|---|---|
| Service architecture (8 services, names, responsibilities) | Identical | Explicitly specified in scope.md |
| Tech stack (FastAPI, DAPR, Terraform, Python 3.12) | Identical | Explicitly specified in scope.md |
| Backward-compatible endpoints | Identical | "Firmware cannot be updated" constraint |
| `/ops/*` diagnostic + remediation endpoints | Identical | Mandated by WINDSURF_DEV.md Step 12 |
| Quality gates (14 automated checks, all passing) | Identical | Prescribed with exact tool commands |
| Document structure (PRD, ADRs, feature parity) | Identical | Templates define every section |
| Domain-realistic test data | Identical | Mandated by WINDSURF_DEV.md + Step 13a |
| Code audit findings (31 issues) | Identical | 14-item checklist catches them proactively |
| Docker runtime (21 containers healthy) | Equivalent | Same compose structure, different debug path |
| Narrative prose in documentation | Varies | Word choice is non-deterministic |
| Exact implementation patterns | Varies | Functionally equivalent alternatives |

The ~3% variance consists of aesthetic prose differences and implementation
micro-decisions — different variable names, different iterator patterns,
different phrasings in ADR arguments. The functional output (what the code
does, what tests verify, what endpoints exist, what quality gates pass) is
deterministic.

### What closed the gap

The first run was assessed at ~90% reproducible. Three rounds of process
improvements addressed specific gap categories:

| Gap observed | Root cause | Fix applied | Location |
|---|---|---|---|
| Generic test data (`abc123`, `test-token`) | No standard for test realism | Realistic test data mandate | WINDSURF_DEV.md + Step 13a |
| 31 code quality issues found during review | No proactive checklist | 14-item Code Audit Checklist | WINDSURF_DEV.md |
| Inconsistent commit messages | No message format standard | Commit Messages subsection, `git commit -F` | WINDSURF_DEV.md |
| Agent committed to main despite "never commit to main" | Standards treated as advisory | Agent Role section + Pre-Commit Checklist | WINDSURF_DEV.md |

Each fix converted a human correction into a document rule, eliminating that
class of variance from future runs.

## For a Director of Engineering

### What you can rely on

1. **Structural consistency.** Every rebuild produces the same set of
   artifacts in the same locations with the same internal structure. You can
   compare two rebuild outputs side-by-side because they use the same
   templates.

2. **Quality guarantees.** 14 automated quality gates must pass before the
   build is considered complete. These are not aspirational — they are
   enforced by the process and verified by `tests/TEST_RESULTS.md`. The
   quality receipt is a machine-verified proof, not an engineer's assertion.

3. **Compliance auditability.** The compliance audit (Step 12) checks 30+
   specific items — Dockerfile pinning, non-root user, health endpoint
   behavior, Pydantic response models, OTEL instrumentation, IDE instruction
   files. Each item is a binary pass/fail.

4. **Process improvement is systematic.** Every manual correction from an
   operator becomes a process change (Step 17). The process gets tighter with
   each run. Gaps don't persist — they get codified into the standards.

5. **Agent behavior is document-driven.** Both agents (developer and SRE)
   load their instructions from markdown files at the start of every session.
   Changing the document changes the behavior. No retraining, no
   redeployment, no model fine-tuning. You control the agent by editing a
   text file.

### What varies and why it's acceptable

1. **Prose is non-deterministic.** The exact wording in ADRs, component
   overviews, and PRD narratives will differ between runs. The structure,
   findings, and conclusions will not. This is the same variance you get
   between two human engineers writing the same design doc — the analysis is
   the same, the sentences are different.

2. **Implementation has degrees of freedom.** Two runs might implement a
   config parser as a function vs. a class, or use a list comprehension vs.
   a generator. The compliance checklist and quality gates ensure both
   implementations meet the same standard. This is functionally equivalent
   variance — the kind that code review would accept either way.

3. **Novel runtime bugs take different debug paths.** A Docker runtime issue
   that wasn't previously cataloged (Step 13b) will be debugged differently
   by different agent runs. The end state is the same (all containers
   healthy), but the journey differs. The process catalogs known failure
   patterns to reduce even this variance over time.

### What you should verify

1. **scope.md quality.** The single biggest driver of output quality is the
   specificity of the scope document. Review it carefully — especially the
   Target State section. Vague scope → variable output. Specific scope →
   deterministic output.

2. **TEST_RESULTS.md exists and shows all gates passing.** This is the
   quality receipt. If it doesn't exist or shows failures, the build is not
   complete regardless of what else was produced.

3. **process-feedback.md is empty or contains only minor items.** If this
   file has substantive entries, the process had gaps that required human
   intervention. Those gaps should be closed before the next rebuild.

### The mental model

Think of it as a **structured form with LLM-powered fill-in**, not a
**creative writing exercise with LLM-powered imagination**:

| Analogy | What varies | What doesn't |
|---|---|---|
| Tax preparation software | The numbers on the form | The form itself, the filing rules, the validation checks |
| Building code inspection | The house design | The checklist, the safety minimums, the pass/fail criteria |
| Replicator rebuild | The prose, the implementation micro-decisions | The artifacts, the structure, the quality gates, the compliance checks |

The LLM's generative capability is channeled into *analysis and
implementation* — reading legacy code, understanding domain logic, writing
compliant code. Its tendency toward creative variance is constrained by
*prescriptive structure* — fixed templates, binding checklists, automated
quality gates.

The result is output that is **predictable in structure, deterministic in
quality, and equivalent in function** — even when the exact words and code
differ between runs.
