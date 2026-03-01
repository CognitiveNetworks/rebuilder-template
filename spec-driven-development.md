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
standards written as third-person guidelines ("The team should never commit to
main") as reference material — something the agent *knows about* but does not
*apply to itself*. Rewriting standards in second-person imperative ("You do not
run `git push origin main`") converts them from reference to instruction, which
is the distinction LLMs use to decide whether a rule constrains their own
actions. See **"The Reference vs. Instruction Problem"** below for the full
analysis, examples, and measured impact.

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

## The Reference vs. Instruction Problem

This is the single most important lesson from the first full rebuild, and the
one most likely to be underestimated by teams writing agent instructions for the
first time.

### What we observed

WINDSURF_DEV.md contained the rule: **"Never commit directly to main."** The
agent read the file. The agent understood the rule. The agent committed directly
to main anyway — repeatedly, across multiple sessions.

This was not a model failure, a context window issue, or a prompt injection. The
agent was following the instruction as it understood it: the document described
how a *team* should work, and the agent's job was to produce *code* that
conformed to those standards. The commit workflow was (from the agent's
perspective) a human process concern, not an instruction directed at the agent
itself.

### Root cause: audience ambiguity

The rule "Never commit directly to main" is written in the style of a
**reference document** — a guideline for a human engineering team. It describes
a policy. It does not address the agent. An LLM reading this applies it the
same way a new engineer reading an onboarding wiki would: "good to know, I'll
follow this when it seems relevant."

Compare the original language to the fix:

| Before (reference) | After (instruction) |
|---|---|
| "Never commit directly to main." | "**You** do not run `git push origin main`." |
| "Run the full test suite before pushing." | "**You** run pytest before `git push`." |
| "Use feature branches for all changes." | "Before every commit, **you** check which branch you are on." |
| "Write detailed commit messages." | "**You** write the commit message to `/tmp/commit-msg.txt` and run `git commit -F /tmp/commit-msg.txt`." |

The left column describes policy. The right column gives orders. An LLM treats
these fundamentally differently:

- **Reference language** ("The team should...") → the agent *knows* the rule
  and will mention it if asked, but does not internalize it as a constraint on
  its own tool calls
- **Instruction language** ("You must...") → the agent applies the rule to its
  own actions, including terminal commands, file writes, and commit workflows

This is not a quirk of a particular model. It is a structural property of how
instruction-tuned LLMs process documents. The model's training teaches it to
distinguish between information it should *know* and instructions it should
*follow*. Third-person guidelines land in the "know" category. Second-person
imperatives land in the "follow" category.

### The fix: Agent Role section

The solution was not to rewrite every sentence in WINDSURF_DEV.md. Instead, we
added a single section at the top — **Agent Role** — that reframes the entire
document:

> **You are the developer on this project.** When you load this file, every
> standard in it becomes your operating procedure — not a reference document,
> not a style guide, but the rules you follow by default.

This framing paragraph converts the entire document from "reference material
the agent is aware of" to "operating instructions the agent must execute." The
specific rules that follow don't need to be rewritten — the framing changes
how the agent interprets all of them.

Four principles reinforce this framing:

1. **"You own the process."** — The agent does not wait for the human to
   remind it to branch, test, lint, or write a commit message. It does
   these things because the document says to.
2. **"You enforce standards on yourself."** — Before every commit, the agent
   checks its own work against the checklists. If something fails, it fixes
   the issue before committing.
3. **"You flag conflicts."** — If the human asks for something that
   contradicts the document, the agent says so rather than silently violating
   the standard. This is critical: it means the agent will protect the
   process even from the operator.
4. **"Standards apply to your actions, not just your output."** — The
   explicit bridge from "these rules describe good code" to "these rules
   constrain your terminal commands."

### Why this matters for confidence

Without the reference-to-instruction conversion, the agent's compliance with
standards is **probabilistic**. It might follow "never commit to main" in some
sessions based on context cues, and violate it in others. The same model, same
temperature, same document — but inconsistent behavior because the document
doesn't unambiguously address the agent.

With the Agent Role framing, compliance becomes **deterministic within the
bounds of the instruction window**. The agent will follow the standard because
it has been told — in second-person imperative — that it is the entity
responsible for following it. When it doesn't (due to context window limits or
model error), the Pre-Commit Checklist provides a redundant enforcement layer:
a step-by-step procedure the agent executes before every commit, catching
violations mechanically.

This is the difference between:
- "We have coding standards" (hope the agent reads and follows them)
- "You are bound by these coding standards" (the agent's operating contract)

### Generalized principle for teams writing agent instructions

Any team adopting LLM-driven development should audit their standards documents
with this question: **"Who is this sentence talking to?"**

| Pattern | Agent behavior | Fix |
|---|---|---|
| "The team should..." | Agent knows the policy, does not apply it | "You must..." |
| "Best practices include..." | Agent treats as optional context | "Before [action], always [specific step]." |
| "It is recommended to..." | Agent may or may not follow | "You will [action] because [reason]." |
| "Avoid committing secrets." | Agent understands the concept | "Before every commit, you run `grep -r 'API_KEY\|SECRET' .` and verify no secrets are staged." |
| "Tests should pass before merge." | Agent may skip testing | "You run `pytest -v` and verify 0 failures before running `git push`." |

The pattern is consistent: **replace descriptive policy with imperative
procedure.** Tell the agent exactly what command to run, when to run it, and
what the expected output is. Leave no room for interpretation.

### The Pre-Commit Checklist as redundant enforcement

Even with the Agent Role framing, we added a **Pre-Commit Checklist** — five
explicit steps the agent must complete before every commit:

1. Verify you are on the correct branch (not `main` unless explicitly
   overridden)
2. Run the full test suite and confirm 0 failures
3. Run the linter and type checker and confirm 0 errors
4. Write a detailed commit message via `git commit -F /tmp/commit-msg.txt`
5. Review the diff and confirm it matches the intended change

This checklist is defense-in-depth. Even if the Agent Role framing somehow
fails to reframe the document (unlikely but possible with long context windows
or aggressive summarization), the checklist is a procedural instruction that
the agent executes step-by-step. The first step — "verify you are on the
correct branch" — catches the exact violation we observed in the first run.

### Measured impact

Before the fix (first run):
- Agent committed to `main` 100% of the time
- Agent skipped test runs ~20% of the time
- Agent used inconsistent commit message formats

After the fix (subsequent sessions):
- Agent creates feature branches when standards require them
- Agent runs tests before every commit
- Agent writes commit messages via `git commit -F`
- Agent flags conflicts when asked to override standards

The behavioral change was immediate — no retraining, no model switching, no
temperature adjustment. The only change was the language in the instruction
document. This is the strongest possible evidence that the reference vs.
instruction distinction is the primary control lever for agent compliance.

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

## After Day 1: The Lifecycle of Generated Code

Everything above describes **Day 1** — the initial generation. But generated
code doesn't stay generated. Engineers ship it, debug it, extend it, and
inevitably change parts that the spec got wrong. Without a feedback mechanism,
those changes are invisible to the spec, and the next regeneration overwrites
them with the same wrong code.

This section describes how the system handles the gap between what the spec
says and what the running code actually does.

### The immutable codebase mental model

The ideal is simple: **the PRD is the single source of truth, and the code is
a derived artifact.** If you want to change the code, change the spec first,
then regenerate. This is "immutable infrastructure" applied to application code.

In practice, this ideal breaks on Day 2. An engineer discovers a race
condition the spec didn't anticipate. A customer reports an edge case that
requires a fix before anyone can update the PRD. A performance optimization
needs domain knowledge that doesn't reduce to a spec bullet point.

These changes are legitimate. The question is: **how do you keep the spec and
the code convergent when humans inevitably edit the generated output?**

### Two mechanisms

**1. Spec-Impact PR Gate** — Every human PR to a replicated codebase triggers
a GitHub Action that maps the changed files to PRD sections, identifies which
spec requirements are affected, and posts a structured comment on the PR. The
engineer must acknowledge which PRD sections their change diverges from and
explain why. The PR template enforces this with mandatory sign-off checkboxes.

The gate doesn't block merging — it captures **why** the divergence exists.
Each merged PR appends an entry to `SPEC_DEBT.md`: the date, the PR, the
affected PRD sections, and the engineer's explanation of what the spec got
wrong.

**2. Spec-Lock Annotations** — For code blocks where the generated
implementation was fundamentally wrong (not just a bug fix but a conceptual
gap), engineers wrap the replacement in `@spec-lock` / `@end-spec-lock`
annotations. These annotations include:

- The PRD section the code implements
- A unique lock ID
- The behavioral contract the code guarantees
- The reason the generated version was replaced

Locked blocks are **human-authoritative** — the regeneration process must port
them faithfully rather than regenerating from prose. A language-agnostic
scanner (`scripts/scan-spec-locks.sh`) extracts all locks into
`spec-locks.yaml` for automated processing.

### The convergence lifecycle

```
Generate → Deploy → Human edits → Spec debt accumulates
    ↑                                        |
    |          Reconcile: merge debt          |
    |          entries into PRD               |
    +←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←+
                Regenerate with
                improved spec
```

On **re-replication** (rebuilding a previously generated codebase), the process
runs a reconciliation step before assessment:

1. Read `SPEC_DEBT.md` — every entry where a human explained why the generated
   code was wrong.
2. Read `spec-locks.yaml` — every block where a human replaced the generated
   implementation entirely.
3. **Update the PRD** to incorporate what the humans taught it. Missing
   requirements get added. Wrong requirements get corrected. Inexpressible
   constraints get documented as notes.
4. Re-generate from the improved spec.

After reconciliation, some locks can be removed — the PRD now captures what
they protected. The remaining locks represent requirements that truly cannot be
expressed in spec prose (performance tuning, hardware quirks, vendor SDK
workarounds). Those are carried forward.

### Spec-lock count as a health metric

The number of `@spec-lock` annotations in a codebase is a leading indicator
of spec quality:

| Lock count | Interpretation |
|---|---|
| 0 | Either the spec is perfect, or nobody is editing the generated code (both worth investigating) |
| 1–5 | Healthy — a few edge cases the spec couldn't anticipate |
| 6–15 | The spec has gaps — reconciliation before next rebuild is recommended |
| 15+ | The spec is significantly incomplete — consider a spec rewrite before regenerating |

Over successive rebuilds, the lock count should **decrease**. Each
reconciliation cycle converts locks into spec improvements. A rising lock count
means the spec is diverging from reality faster than reconciliation is closing
the gap.

### What this means for engineering leaders

- **Human edits are expected, not failures.** The system captures them rather
  than ignoring them.
- **Every spec-debt entry is a spec improvement waiting to happen.** The debt
  ledger is a prioritized backlog of PRD corrections.
- **Spec-lock count is auditable.** You can track it per-repo, per-sprint,
  per-team. A team with a falling lock count is converging their specs toward
  completeness.
- **Re-replication gets better each cycle.** The first generation has no human
  input. The second generation incorporates every correction from the first
  deployment. By the third cycle, most edge cases are in the spec.

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
