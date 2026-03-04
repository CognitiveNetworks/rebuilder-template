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
flowchart LR
    subgraph INPUTS ["Inputs"]
        S["scope.md · input.md<br/>repo/ · adjacent/"]
    end
    subgraph PROCESS ["Process"]
        IP["IDEATION_PROCESS.md<br/>skill.md · STANDARDS.md"]
    end
    subgraph OUTPUTS ["Outputs"]
        O["18 artifacts · codebase<br/>agent configs · TEST_RESULTS.md"]
    end

    INPUTS -->|"analyzed by"| PROCESS -->|"produces"| OUTPUTS

    style INPUTS fill:#e8f4f8,stroke:#2c7bb6
    style PROCESS fill:#fff3cd,stroke:#d4a017
    style OUTPUTS fill:#e8f0e4,stroke:#4daf4a
```

| Inputs | Process | Outputs |
|---|---|---|
| **scope.md** — what it is, what it should be | **IDEATION_PROCESS.md** — 18 prescribed steps | **18 named artifacts** — fixed structure, fixed location |
| **input.md** — tech stack, APIs, auth | **skill.md** — coding standards + checklists | **Built codebase** — standards-compliant, tested |
| **repo/** — legacy source code | **STANDARDS.md** — architecture standards | **Agent configs** — populated, IDE-loadable |
| **adjacent/** — related repos (optional) | | **TEST_RESULTS.md** — quality receipt |

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

## The Key Insight — Reference vs. Instruction

The single biggest lesson from the first rebuild: **how you write standards determines whether the agent follows them.**

```mermaid
flowchart LR
    REF["Reference ✗<br/><i>'Never commit to main'</i>"]
    KNOW["Agent <b>knows</b> the rule<br/>but doesn't apply it"]
    INST["Instruction ✓<br/><i>'<b>You</b> do not run<br/>git push origin main'</i>"]
    FOLLOW["Agent <b>follows</b> the rule<br/>compliance is deterministic"]

    REF --> KNOW
    INST --> FOLLOW

    style REF fill:#fde8e8,stroke:#c0392b
    style KNOW fill:#fde8e8,stroke:#c0392b
    style INST fill:#e8f0e4,stroke:#4daf4a
    style FOLLOW fill:#e8f0e4,stroke:#4daf4a
```

| Pattern (weak) | Fix (strong) |
|---|---|
| "The team should…" | "**You** must…" |
| "Best practices include…" | "Before [action], **you** always [step]." |
| "Avoid committing secrets." | "Before every commit, **you** run `grep -r 'API_KEY' .`" |
| "Tests should pass before merge." | "**You** run `pytest -v` and verify 0 failures before `git push`." |

---

## The Mental Model

> Think **structured form with LLM-powered fill-in**, not creative writing with LLM-powered imagination.

| Analogy | What varies | What doesn't |
|---|---|---|
| Tax software | The numbers | The form, the rules, the validation |
| Building inspection | The house design | The checklist, the safety minimums |
| **Replicator rebuild** | **Prose, micro-decisions** | **Artifacts, structure, quality gates** |
