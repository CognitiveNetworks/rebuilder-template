---
description: Run the full replicator process on a legacy repo. Triggered by "run replicator on <repo>" or similar.
---

# Run Replicator

This workflow runs the full legacy rebuild process. The **destination repo**
is the working area where all outputs are written. **rebuilder-template is
read-only** — it provides the process definition and agent templates but is
never modified.

## Prerequisites

The destination repo must exist with the following structure:

```
<dest>/                                ← the destination repo (working area)
├── rebuild-inputs/
│   ├── scope.md                       ← filled out with current and target state
│   ├── input.md                       ← filled out with pain points and context
│   ├── repo/                          ← cloned legacy repository
│   └── adjacent/                      ← (optional) cloned adjacent repos
└── template/                          ← cloned template repo (build standard)
```

- `rebuild-inputs/scope.md` — filled out with current and target state
- `rebuild-inputs/input.md` — filled out with pain points and context
- `rebuild-inputs/repo/` — the cloned legacy repository
- `template/` — the cloned template repo (e.g., `rebuilder-evergreen-template-repo-python`). This is the build standard — not an adjacent repo. Its `skill.md` is the authoritative checklist for how the rebuilt service must be structured.
- (optional) `rebuild-inputs/adjacent/` — cloned adjacent repos (production code dependencies)

### Workspace Isolation (Mandatory)

The replicator process reads **only** these directories:
- `<dest>/rebuild-inputs/repo/` — the legacy codebase
- `<dest>/template/` — the template repo (build standard)
- `<dest>/rebuild-inputs/adjacent/` — adjacent production dependencies (if listed in scope.md)
- rebuilder-template — process definitions and agent templates (read-only)

**Never read from, reference, or import code from any other `rebuilder-*` repository in the workspace.** Other rebuilder repos (e.g., `rebuilder-ingesttimeline`, a prior `rebuilder-evergreen-tvevents` build) may be in any state — partially built, stale, or broken. Referencing them contaminates the current build. The destination directory is wiped clean precisely so the build starts from zero.

## Steps

1. **Identify the destination repo.** The user will say something like "run replicator on evergreen-tvevents" or "run replicator on orderflow". Map this to the destination repo path (e.g., `../rebuilder-evergreen-tvevents`). Verify `rebuild-inputs/scope.md` and `rebuild-inputs/input.md` exist in that repo.

// turbo
1b. **Clone the template repo** if `<dest>/template/` does not already exist. The template repo URL is specified in `rebuild-inputs/input.md`. Clone it to `<dest>/template/`:
   ```
   git clone <template-repo-url> <dest>/template
   ```
   After cloning, verify `<dest>/template/skill.md` exists. This file is the authoritative checklist for the Build phase.

1c. **Clean the destination directory.** Wipe all prior build artifacts so no stale code contaminates the new build. Preserve `.git/`, `rebuild-inputs/` (user inputs + legacy repo), and `template/`:
   ```
   find <dest> -mindepth 1 -maxdepth 1 ! -name '.git' ! -name 'rebuild-inputs' ! -name 'template' -exec rm -rf {} +
   ```
   **Confirm with the user before deleting.** Show the destination path and ask for explicit approval. This is a destructive operation.

// turbo
2. **Create output directories** in the destination repo:
   ```
   mkdir -p <dest>/output
   mkdir -p <dest>/sre-agent
   mkdir -p <dest>/{lang}-developer-agent
   mkdir -p <dest>/{lang}-qa-agent
   mkdir -p <dest>/docs/adr
   mkdir -p <dest>/docs/postmortems
   ```

   > **Language detection:** Read `<dest>/rebuild-inputs/scope.md` → Target Language field to determine `{lang}` (python, c, or go).

3. **Copy agent template files** from rebuilder-template into the destination repo (skip if already present):
   - `sre-agent/skill.md` → `<dest>/sre-agent/skill.md`
   - `sre-agent/config.md` → `<dest>/sre-agent/config.md`
   - `{lang}-developer-agent/skill.md` → `<dest>/{lang}-developer-agent/skill.md`
   - `{lang}-developer-agent/config.md` → `<dest>/{lang}-developer-agent/config.md`
   - `{lang}-developer-agent/.windsurfrules` → `<dest>/{lang}-developer-agent/.windsurfrules`
   - `{lang}-developer-agent/.github/copilot-instructions.md` → `<dest>/{lang}-developer-agent/.github/copilot-instructions.md`
   - `{lang}-qa-agent/skill.md` → `<dest>/{lang}-qa-agent/skill.md`
   - `{lang}-qa-agent/config.md` → `<dest>/{lang}-qa-agent/config.md`
   - `{lang}-qa-agent/TEST_RESULTS_TEMPLATE.md` → `<dest>/{lang}-qa-agent/TEST_RESULTS_TEMPLATE.md`
   - `docs/cutover-report.md` → `<dest>/docs/cutover-report.md`
   - `docs/disaster-recovery.md` → `<dest>/docs/disaster-recovery.md`

4. **Invoke the `@legacy-rebuild` skill.** Read `.windsurf/skills/legacy-rebuild/SKILL.md` (from rebuilder-template) for the process overview, then read and execute `rebuild/IDEATION_PROCESS.md`. Read `<dest>/rebuild-inputs/input.md` and `<dest>/rebuild-inputs/scope.md`. Execute Steps 1-11 sequentially, writing outputs to `<dest>/output/`. Tell the user that they should review before continuing on steps 12-18.

   **Before the Build phase (Steps 12–18):** Read `<dest>/template/skill.md` in full. Every checkbox in that file is mandatory for the built service. Complete them all during the Build phase. Do not invent your own tooling, configs, or patterns — match what the template repo specifies.

5. **For Steps 7 and 8 (template population)**, you MUST follow the `/populate-templates` workflow rules. Read `.windsurf/workflows/populate-templates.md` (from rebuilder-template) before populating any template file. The strict rules in that workflow override any inclination to condense, rephrase, or restructure template content.

6. **After all steps complete**, summarize what was generated and list any `[TODO]` placeholders that remain for the user to fill in post-deployment.
