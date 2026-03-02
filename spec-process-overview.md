# Spec-Driven Development — Visual Overview

> Quick-reference companion to [spec-driven-development.md](../spec-driven-development.md).
> Start here for the picture; go there for the full explanation.

---

## Three Phases

Every Replicator rebuild follows the same three phases.
The output of each phase feeds the next.

```mermaid
flowchart LR
    A["<b>Phase 1 — Analyze</b><br/>Legacy code → PRD,<br/>ADRs, agent configs"]
    B["<b>Phase 2 — Build</b><br/>PRD → new codebase,<br/>tests, infrastructure"]
    C["<b>Phase 3 — Operate</b><br/>Alerts → diagnose,<br/>remediate, escalate"]

    A -->|"populated agent configs<br/>+ PRD"| B
    B -->|"deployed service<br/>with /ops/* endpoints"| C

    style A fill:#e8f4f8,stroke:#2c7bb6
    style B fill:#e8f0e4,stroke:#4daf4a
    style C fill:#fef3e0,stroke:#ff7f00
```

---

## The Contract — Inputs, Process, Outputs

The process constrains the LLM to **fill in values**, not decide what the structure is.
Same inputs + same process = same outputs (structure, quality, function).

```mermaid
flowchart TB
    subgraph INPUTS ["Inputs — what you provide"]
        direction LR
        S["scope.md<br/><i>what it is, what it should be</i>"]
        I["input.md<br/><i>tech stack, APIs, auth</i>"]
        R["repo/<br/><i>legacy source code</i>"]
        A["adjacent/<br/><i>related repos (optional)</i>"]
    end

    subgraph PROCESS ["Process — what the agent executes"]
        direction LR
        IP["IDEATION_PROCESS.md<br/><i>18 prescribed steps</i>"]
        SK["skill.md<br/><i>coding standards + checklists</i>"]
        ST["STANDARDS.md<br/><i>architecture standards</i>"]
    end

    subgraph OUTPUTS ["Outputs — what gets delivered"]
        direction LR
        O1["18 named artifacts<br/><i>fixed structure, fixed location</i>"]
        O2["Built codebase<br/><i>standards-compliant, tested</i>"]
        O3["Agent configs<br/><i>populated, IDE-loadable</i>"]
        O4["Quality receipt<br/><i>TEST_RESULTS.md</i>"]
    end

    INPUTS --> PROCESS --> OUTPUTS

    style INPUTS fill:#e8f4f8,stroke:#2c7bb6
    style PROCESS fill:#fff3cd,stroke:#d4a017
    style OUTPUTS fill:#e8f0e4,stroke:#4daf4a
```

---

## Five Reproducibility Mechanisms

These work together to ensure two independent agents, given the same inputs, arrive at the same destination.

```mermaid
flowchart TB
    P["<b>1. Prescriptive Process</b><br/>Every step defines<br/>exact file, structure, fields"]
    I["<b>2. Input Specificity</b><br/>Detailed scope.md eliminates<br/>agent decision-making"]
    C["<b>3. Compliance Checklists</b><br/>30+ items force convergence<br/>on the end state"]
    B["<b>4. Binding Standards</b><br/>Agent Role framing converts<br/>guidelines → orders"]
    F["<b>5. Feedback Loop</b><br/>Every manual correction<br/>becomes a process rule"]

    P --> SAME["Same structure,<br/>same quality,<br/>same function"]
    I --> SAME
    C --> SAME
    B --> SAME
    F --> SAME

    style SAME fill:#e8f0e4,stroke:#4daf4a,stroke-width:2px
```

---

## Two Agents, Same Pattern

Both agents use the same two-file pattern: **skill.md** (how to act) + **config.md** (what to act on).

```mermaid
flowchart TB
    subgraph DEV ["Developer Agent — Phase 2"]
        D_TRIGGER["Developer opens IDE"]
        D_SHIM["IDE reads shim file<br/>.windsurfrules or<br/>.github/copilot-instructions.md"]
        D_LOAD["Loads skill.md + config.md"]
        D_ACT["Writes code per standards<br/>Runs tests before commit<br/>Enforces checklists on itself"]
        D_TRIGGER --> D_SHIM --> D_LOAD --> D_ACT
    end

    subgraph SRE ["SRE Agent — Phase 3"]
        S_TRIGGER["Monitoring alert fires"]
        S_LOAD2["agent.py reads skill.md<br/>as system prompt"]
        S_DIAG["Calls /ops/* endpoints<br/>Classifies problem<br/>Runs playbook"]
        S_ACT["Remediates or escalates<br/>via PagerDuty"]
        S_TRIGGER --> S_LOAD2 --> S_DIAG --> S_ACT
    end

    DEV -.->|"service exposes<br/>/ops/* endpoints"| SRE

    style DEV fill:#e8f4f8,stroke:#2c7bb6
    style SRE fill:#fef3e0,stroke:#ff7f00
```

**Both agents are stateless.** Every session starts from the skill file on disk.
Change the document → change the behavior. No retraining, no redeployment.

---

## After Day 1 — The Convergence Loop

Generated code doesn't stay generated. Engineers fix bugs, handle edge cases, and tune performance.
Two mechanisms keep the spec and code convergent over time:

| Mechanism | What it does |
|---|---|
| **Spec-Impact PR Gate** | Every human PR maps changes to PRD sections. Engineer explains the divergence. Entry logged to `SPEC_DEBT.md`. |
| **Spec-Lock Annotations** | Code blocks the spec can't express (`@spec-lock`) are preserved across regeneration. |

```mermaid
flowchart LR
    GEN["Generate<br/>from spec"]
    DEPLOY["Deploy"]
    EDIT["Human edits<br/>fix bugs, tune perf"]
    DEBT["Spec debt<br/>accumulates<br/><i>SPEC_DEBT.md +<br/>spec-locks.yaml</i>"]
    RECONCILE["Reconcile<br/>merge debt into PRD"]
    REGEN["Regenerate<br/>with improved spec"]

    GEN --> DEPLOY --> EDIT --> DEBT --> RECONCILE --> REGEN
    REGEN -->|"next cycle"| DEPLOY

    style GEN fill:#e8f4f8,stroke:#2c7bb6
    style RECONCILE fill:#fff3cd,stroke:#d4a017
    style REGEN fill:#e8f0e4,stroke:#4daf4a
```

Each cycle, the spec absorbs what humans taught it. Lock count should **decrease** over time:

| Locks | Meaning |
|---|---|
| 0 | Spec is complete (or nobody is editing — investigate) |
| 1–5 | Healthy — a few edge cases |
| 6–15 | Spec has gaps — reconcile before next rebuild |
| 15+ | Spec needs a rewrite |

---

## The Key Insight — Reference vs. Instruction

The single biggest lesson from the first rebuild: **how you write standards determines whether the agent follows them.**

```mermaid
flowchart LR
    subgraph REF ["Reference Language ✗"]
        R1["'Never commit to main'"]
        R2["Agent <i>knows</i> the rule"]
        R3["Agent does not<br/>apply it to itself"]
        R1 --> R2 --> R3
    end

    subgraph INST ["Instruction Language ✓"]
        I1["'<b>You</b> do not run<br/>git push origin main'"]
        I2["Agent <i>follows</i> the rule"]
        I3["Compliance becomes<br/>deterministic"]
        I1 --> I2 --> I3
    end

    style REF fill:#fde8e8,stroke:#c0392b
    style INST fill:#e8f0e4,stroke:#4daf4a
```

| Pattern (weak) | Fix (strong) |
|---|---|
| "The team should…" | "**You** must…" |
| "Best practices include…" | "Before [action], **you** always [step]." |
| "Avoid committing secrets." | "Before every commit, **you** run `grep -r 'API_KEY' .`" |

---

## The Mental Model

> Think **structured form with LLM-powered fill-in**, not creative writing with LLM-powered imagination.

| Analogy | What varies | What doesn't |
|---|---|---|
| Tax software | The numbers | The form, the rules, the validation |
| Building inspection | The house design | The checklist, the safety minimums |
| **Replicator rebuild** | **Prose, micro-decisions** | **Artifacts, structure, quality gates** |
