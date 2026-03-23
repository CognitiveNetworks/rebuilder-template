---
name: legacy-rebuild
description: Executes the full legacy rebuild process — analyzes a legacy codebase, generates a PRD, populates agent configs, produces ADRs, feature parity matrix, and data migration mapping. Invoke when someone says "rebuild", "replicator", "ideation process", or wants to analyze a legacy application for modernization.
---

# Legacy Rebuild Skill

This skill executes the full legacy rebuild ideation process. It analyzes a
legacy codebase and produces all artifacts needed to rebuild it as a modern
Evergreen Python service.

## When to Use

- User says "rebuild", "run replicator", or "analyze legacy"
- User wants to modernize a legacy application
- User references the ideation process or rebuild process

## Process

The full process is defined in `rebuild/IDEATION_PROCESS.md` (18 steps across
two phases). This skill provides the entry point — read that file for the
complete step-by-step procedure.

### Phase 1: Analyze (Steps 1–11) — Automated

Produces analysis artifacts, PRD, agent configs, ADRs, and mapping documents.
Executed by `rebuild/run.sh` in a single automated pass.

### Phase 2: Build (Steps 12–18) — Interactive

Validates the code, generates remaining documentation, and captures process
feedback. Executed during interactive development sessions with the developer
agent after the service code is written.

## Required Inputs

Before starting, verify these exist in the project working directory:

- `scope.md` — filled out with current and target state
- `input.md` — filled out with pain points and context
- `repo/` — the cloned legacy repository
- (optional) `adjacent/` — cloned adjacent repos

## Supporting Files

| File | Purpose |
|---|---|
| `rebuild/IDEATION_PROCESS.md` | Full 18-step process definition |
| `rebuild/input.md` | Input template |
| `rebuild/run.sh` | Automated execution script |
| `scope.md` | Scope template |
| `developer-agent/skill.md` | Developer agent standards (template) |
| `developer-agent/config.md` | Developer agent config (template) |
| `qa-agent/skill.md` | QA agent standards (template) |
| `qa-agent/config.md` | QA agent config (template) |
| `sre-agent/skill.md` | SRE agent standards (template) |
| `sre-agent/config.md` | SRE agent config (template) |

## Template Population Rules

When populating agent templates (Steps 7–8), follow the strict rules in
`.windsurf/workflows/populate-templates.md`. Key rules:

1. Preserve every section — do not delete, merge, or summarize
2. Only replace placeholders — do not rewrite prose
3. Keep formatting identical — heading levels, table columns, list styles
4. If a value is unknown, leave the placeholder and add a TODO comment

## Quick Start

```bash
# 1. Create project directory
mkdir -p rebuild-inputs/my-project

# 2. Clone legacy repo
git clone <url> rebuild-inputs/my-project/repo

# 3. Copy templates
cp scope.md rebuild-inputs/my-project/scope.md
cp rebuild/input.md rebuild-inputs/my-project/input.md

# 4. Fill out scope.md and input.md

# 5. Run
./rebuild/run.sh rebuild-inputs/my-project
```

Or use the `/run-replicator` workflow for interactive execution.
