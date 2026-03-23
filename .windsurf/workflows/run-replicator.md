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
- (optional) `adjacent/` — cloned adjacent repos

## Steps

1. **Identify the project directory.** The user will say something like "run replicator on vizio-automate" or "run replicator on orderflow". Map this to the path `rebuild-inputs/<project>/`. Verify `scope.md` and `input.md` exist.

// turbo
2. **Create output directories** if they don't already exist:
   ```
   mkdir -p <project-dir>/output
   mkdir -p <project-dir>/sre-agent
   mkdir -p <project-dir>/developer-agent
   mkdir -p <project-dir>/qa-agent
   mkdir -p <project-dir>/docs/adr
   mkdir -p <project-dir>/docs/postmortems
   ```

3. **Copy template files** into the project directory (skip if already present):
   - `sre-agent/skill.md` → `<project-dir>/sre-agent/skill.md`
   - `sre-agent/config.md` → `<project-dir>/sre-agent/config.md`
   - `developer-agent/skill.md` → `<project-dir>/developer-agent/skill.md`
   - `developer-agent/config.md` → `<project-dir>/developer-agent/config.md`
   - `developer-agent/.windsurfrules` → `<project-dir>/developer-agent/.windsurfrules`
   - `developer-agent/.github/copilot-instructions.md` → `<project-dir>/developer-agent/.github/copilot-instructions.md`
   - `qa-agent/skill.md` → `<project-dir>/qa-agent/skill.md`
   - `qa-agent/config.md` → `<project-dir>/qa-agent/config.md`
   - `qa-agent/TEST_RESULTS_TEMPLATE.md` → `<project-dir>/qa-agent/TEST_RESULTS_TEMPLATE.md`
   - `docs/cutover-report.md` → `<project-dir>/docs/cutover-report.md`
   - `docs/disaster-recovery.md` → `<project-dir>/docs/disaster-recovery.md`

4. **Invoke the `@legacy-rebuild` skill.** Read `.windsurf/skills/legacy-rebuild/SKILL.md` for the process overview, then read and execute `rebuild/IDEATION_PROCESS.md`. Read `<project-dir>/input.md` and `<project-dir>/scope.md`. Execute Steps 1-11 sequentially, writing outputs to `<project-dir>/output/`. Tell the user that they should review before continuing on steps 12-18.

5. **For Steps 7 and 8 (template population)**, you MUST follow the `/populate-templates` workflow rules. Read `.windsurf/workflows/populate-templates.md` before populating any template file. The strict rules in that workflow override any inclination to condense, rephrase, or restructure template content.

6. **After all steps complete**, summarize what was generated and list any `[TODO]` placeholders that remain for the user to fill in post-deployment.
