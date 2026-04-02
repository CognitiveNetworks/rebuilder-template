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

The **destination repo** is the working area. Before starting, verify these exist there:

- `rebuild-inputs/scope.md` — filled out with current and target state (includes Template Repository field)
- `rebuild-inputs/input.md` — filled out with pain points and context (includes Template Repository field)
- `rebuild-inputs/repo/` — the cloned legacy repository
- `template/` — the **required** template repo (`rebuilder-evergreen-template-repo-python`) that defines Dockerfile, entrypoint.sh, environment-check.sh, Helm charts, CI workflows, pip-compile, OTEL auto-instrumentation, quality gate tooling, and coding practices. **This is not optional.** The template repo is the build standard — not an adjacent repo. Its `skill.md` is the authoritative checklist for the Build phase.
- (optional) `rebuild-inputs/adjacent/` — cloned adjacent repos (production code dependencies)

## Template Repository (Non-Negotiable)

[`rebuilder-evergreen-template-repo-python`](https://github.com/CognitiveNetworks/rebuilder-evergreen-template-repo-python)
is the canonical reference for how every rebuilt service must be structured.
It defines:

- **Dockerfile** — base image, user pattern, layer ordering
- **entrypoint.sh** — uvicorn startup, log level, reload flags
- **environment-check.sh** — required env var validation
- **Helm chart templates** — deployment, service, configmap, ingress
- **CI workflow** — GitHub Actions pipeline stages and quality gates
- **pip-compile** — dependency pinning strategy
- **OTEL auto-instrumentation** — OpenTelemetry setup pattern
- **Quality gate tooling** — pylint, black, mypy, pytest, coverage, complexipy, etc.

**Do not deviate from these patterns.** The developer agent's `config.md`
references this repo. The QA agent validates every checkbox in
`template/skill.md` during verification. `template/skill.md` is copied into
the built repo and stays there permanently. If the template repo is not cloned
into `template/`, the agent cannot verify conformance — the rebuild must not
proceed without it.

## Workspace Isolation

The replicator reads **only** from these directories during a rebuild:
- `<dest>/rebuild-inputs/repo/` — the legacy codebase
- `<dest>/template/` — the template repo (build standard)
- `<dest>/rebuild-inputs/adjacent/` — adjacent production dependencies (if listed in scope.md)
- rebuilder-template — process definitions and agent templates (read-only)

**Never read from, reference, or import code from any other `rebuilder-*` repository in the workspace.** Other rebuilder repos may be partially built, stale, or from a different project. The destination repo is wiped clean before every run (preserving `.git/`, `rebuild-inputs/`, and `template/`). Do not read from other repos expecting reusable state — each build starts from zero.

## Supporting Files

| File | Purpose |
|---|---|
| `rebuild/IDEATION_PROCESS.md` | Full 18-step process definition |
| `rebuild/input.md` | Input template |
| `rebuild/run.sh` | Automated execution script |
| `scope.md` | Scope template |
| `template/` | **Required** — build standard repo; `template/skill.md` is the authoritative checklist |
| `{lang}-developer-agent/skill.md` | Developer agent standards (template) |
| `{lang}-developer-agent/config.md` | Developer agent config (template) |
| `{lang}-qa-agent/skill.md` | QA agent standards (template) |
| `{lang}-qa-agent/config.md` | QA agent config (template) |
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

### Option 1: `/run-replicator` workflow (recommended)

In Windsurf, type:
```
/run-replicator https://github.com/CognitiveNetworks/automate
```

The workflow automatically:
1. Derives destination repo path (`../rebuilder-automate`)
2. Creates the repo and clones the legacy code
3. Copies `scope.md` and `input.md` templates
4. Asks you to fill them out (pauses until you confirm)
5. Clones the template repo
6. Runs the full ideation process

### Option 2: Manual setup + `run.sh`

```bash
# 1. Create destination repo
mkdir -p /path/to/rebuilder-my-project/rebuild-inputs
cd /path/to/rebuilder-my-project && git init

# 2. Clone legacy repo into rebuild-inputs/
git clone <url> rebuild-inputs/repo

# 3. Clone the template repo (required — not optional)
git clone git@github.com:CognitiveNetworks/rebuilder-evergreen-template-repo-python.git template

# 4. Copy input templates from rebuilder-template
cp /path/to/rebuilder-template/scope.md rebuild-inputs/scope.md
cp /path/to/rebuilder-template/rebuild/input.md rebuild-inputs/input.md

# 5. Fill out scope.md and input.md

# 6. Run (from rebuilder-template)
/path/to/rebuilder-template/rebuild/run.sh /path/to/rebuilder-my-project
```
