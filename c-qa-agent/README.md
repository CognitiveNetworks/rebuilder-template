# C QA Agent

Quality verification procedures for rebuilt Evergreen C services. The QA agent independently verifies that the developer agent's output meets quality standards — it does **not** replace the developer agent, it checks it.

## Files

| File | Purpose |
|---|---|
| `skill.md` | QA verification standards — quality gates, test strategy, acceptance criteria |
| `config.md` | Per-project QA config — thresholds, env vars, acceptance criteria |
| `README.md` | This file |

## How It Relates

| Document | Scope |
|---|---|
| `c-developer-agent/skill.md` | Development standards — **what the QA agent verifies** |
| `c-developer-agent/config.md` | Project-specific dev config — read by QA for context |
| `c-qa-agent/skill.md` | QA verification procedures — **how compliance is checked** |
| `c-qa-agent/config.md` | Project-specific QA config — thresholds, test commands |
