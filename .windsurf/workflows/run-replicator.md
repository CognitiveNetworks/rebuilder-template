---
description: Run the full replicator process on a legacy repo. Triggered by "run replicator on <repo>" or similar.
---

# Run Replicator

This workflow runs the full legacy rebuild process on a project directory.
It invokes the `@legacy-rebuild` skill which contains the process definition
and supporting file references.

## Prerequisites

The project directory must exist under `rebuild-inputs/` with:
- `scope.md` — filled out with current and target state
- `input.md` — filled out with pain points and context
- `repo/` — the cloned legacy repository
- `template/` — the cloned template repo (e.g., `rebuilder-evergreen-template-repo-python`). This is the build standard — not an adjacent repo. Its `skill.md` is the authoritative checklist for how the rebuilt service must be structured.
- (optional) `adjacent/` — cloned adjacent repos (production code dependencies)

## Steps

1. **Identify the project directory.** The user will say something like "run replicator on vizio-automate" or "run replicator on orderflow". Map this to the path `rebuild-inputs/<project>/`. Verify `scope.md` and `input.md` exist.

// turbo
1b. **Clone the template repo** if `<project-dir>/template/` does not already exist. The template repo URL is specified in `input.md`. Clone it to `<project-dir>/template/`:
   ```
   git clone <template-repo-url> <project-dir>/template
   ```
   After cloning, verify `<project-dir>/template/skill.md` exists. This file is the authoritative checklist for the Build phase.

// turbo
2. **Create output directories** if they don't already exist:
   ```
   mkdir -p <project-dir>/output
   mkdir -p <project-dir>/sre-agent
   mkdir -p <project-dir>/{lang}-developer-agent
   mkdir -p <project-dir>/{lang}-qa-agent
   mkdir -p <project-dir>/docs/adr
   mkdir -p <project-dir>/docs/postmortems
   ```

   > **Language detection:** Read `<project-dir>/scope.md` → Target Language field to determine `{lang}` (python, c, or go).

3. **Copy template files** into the project directory (skip if already present):
   - `sre-agent/skill.md` → `<project-dir>/sre-agent/skill.md`
   - `sre-agent/config.md` → `<project-dir>/sre-agent/config.md`
   - `{lang}-developer-agent/skill.md` → `<project-dir>/{lang}-developer-agent/skill.md`
   - `{lang}-developer-agent/config.md` → `<project-dir>/{lang}-developer-agent/config.md`
   - `{lang}-developer-agent/.windsurfrules` → `<project-dir>/{lang}-developer-agent/.windsurfrules`
   - `{lang}-developer-agent/.github/copilot-instructions.md` → `<project-dir>/{lang}-developer-agent/.github/copilot-instructions.md`
   - `{lang}-qa-agent/skill.md` → `<project-dir>/{lang}-qa-agent/skill.md`
   - `{lang}-qa-agent/config.md` → `<project-dir>/{lang}-qa-agent/config.md`
   - `{lang}-qa-agent/TEST_RESULTS_TEMPLATE.md` → `<project-dir>/{lang}-qa-agent/TEST_RESULTS_TEMPLATE.md`
   - `docs/cutover-report.md` → `<project-dir>/docs/cutover-report.md`
   - `docs/disaster-recovery.md` → `<project-dir>/docs/disaster-recovery.md`

4. **Invoke the `@legacy-rebuild` skill.** Read `.windsurf/skills/legacy-rebuild/SKILL.md` for the process overview, then read and execute `rebuild/IDEATION_PROCESS.md`. Read `<project-dir>/input.md` and `<project-dir>/scope.md`. Execute Steps 1-11 sequentially, writing outputs to `<project-dir>/output/`. Tell the user that they should review before continuing on steps 12-18.

   **Before the Build phase (Steps 12–18):** Read `<project-dir>/template/skill.md` in full. Every checkbox in that file is mandatory for the built service. Complete them all during the Build phase. Do not invent your own tooling, configs, or patterns — match what the template repo specifies.

5. **For Steps 7 and 8 (template population)**, you MUST follow the `/populate-templates` workflow rules. Read `.windsurf/workflows/populate-templates.md` before populating any template file. The strict rules in that workflow override any inclination to condense, rephrase, or restructure template content.

6. **After all steps complete**, summarize what was generated and list any `[TODO]` placeholders that remain for the user to fill in post-deployment.
