---
description: "Run the full replicator process. Usage: /run-replicator <github-url> — e.g. /run-replicator https://github.com/CognitiveNetworks/automate"
---

# Run Replicator

This workflow runs the full legacy rebuild process. The **destination repo**
is the working area where all outputs are written. **rebuilder-template is
read-only** — it provides the process definition and agent templates but is
never modified.

## Invocation

The user provides a **GitHub URL** for the legacy repo, plus optional context:

```
/run-replicator https://github.com/CognitiveNetworks/automate
Use the adjacent repo https://github.com/CognitiveNetworks/cntools.
This will be containerized to run locally but also will need to run in GCP.
Do not include cooker.
```

**Required:** The first GitHub URL is the **legacy repo** to rebuild.

**Optional inline context** (parsed from the user's message):

| Pattern | What to do with it |
|---|---|
| `adjacent repo <url>` or `with <url>` | Clone to `<dest>/rebuild-inputs/adjacent/<name>/` during bootstrap |
| Deployment/runtime constraints (e.g., "run in GCP", "containerized") | Pre-populate into `scope.md` Target State and `input.md` context |
| Exclusions (e.g., "do not include cooker") | Record in `input.md` under exclusions/constraints; respect during analysis |

The agent should extract all of these from the user's message and apply them
during bootstrap. Any context provided here saves the user from manually editing
`scope.md` and `input.md` later.

**If the user did not provide a URL**, ask them:
> "Please provide the GitHub URL for the legacy repo you want to rebuild.
> Example: `/run-replicator https://github.com/CognitiveNetworks/automate`"
>
> Do not proceed until a valid GitHub URL is provided.

Everything else is derived automatically:

| Derived from URL | Convention | Example |
|---|---|---|
| Repo name | Last path segment (minus `.git`) | `automate` |
| Destination repo path | `../rebuilder-<name>` (sibling of rebuilder-template) | `../rebuilder-automate` |
| Destination GitHub repo | Same org, `rebuilder-<name>` | `CognitiveNetworks/rebuilder-automate` |

The **target language** and **template repo URL** are read from `scope.md` after bootstrap.

## Workspace Isolation (Mandatory)

The replicator process reads **only** these directories:
- `<dest>/rebuild-inputs/repo/` — the legacy codebase
- `<dest>/template/` — the template repo (build standard)
- `<dest>/rebuild-inputs/adjacent/` — adjacent production dependencies (if listed in scope.md)
- rebuilder-template — process definitions and agent templates (read-only)

**Never read from, reference, or import code from any other `rebuilder-*` repository in the workspace.** Other rebuilder repos (e.g., `rebuilder-ingesttimeline`, a prior `rebuilder-evergreen-tvevents` build) may be in any state — partially built, stale, or broken. Referencing them contaminates the current build. The destination directory is wiped clean precisely so the build starts from zero.

## Steps

### Step 0: Bootstrap the Destination Repo

Extract the repo name from the URL (e.g., `automate` from `https://github.com/CognitiveNetworks/automate`). Derive the destination path: `../rebuilder-<name>`.

**If the destination repo does NOT exist:**

// turbo
0a. Create the destination repo and initialize git:
   ```
   mkdir -p <dest>/rebuild-inputs
   cd <dest> && git init
   ```

// turbo
0b. Clone the legacy repo:
   ```
   git clone <legacy-url> <dest>/rebuild-inputs/repo
   ```

// turbo
0b-adj. **Clone adjacent repos** (if mentioned in the user's message):
   ```
   mkdir -p <dest>/rebuild-inputs/adjacent
   git clone <adjacent-url> <dest>/rebuild-inputs/adjacent/<name>
   ```

0c. Copy the input templates from rebuilder-template:
   ```
   cp scope.md <dest>/rebuild-inputs/scope.md
   cp rebuild/input.md <dest>/rebuild-inputs/input.md
   ```

0c-pre. **Pre-populate from inline context.** If the user's invocation message
   included deployment constraints, exclusions, or other context, write them
   into the appropriate sections of `scope.md` and `input.md` now:
   - **Adjacent repos** → `scope.md` → Adjacent Repositories section
   - **Deployment/runtime** (e.g., "containerized", "run in GCP") → `scope.md` → Target State
   - **Exclusions** (e.g., "do not include cooker") → `input.md` → Exclusions/constraints
   This pre-population saves the user time but does **not** skip the review step.

0d. **STOP and ask the user to review `scope.md` and `input.md`.**
   Tell them:
   - Open `<dest>/rebuild-inputs/scope.md` — review pre-populated fields and
     fill out any remaining blanks (Current State, Target Language, Template
     Repository).
   - Open `<dest>/rebuild-inputs/input.md` — review pre-populated context and
     fill out pain points.
   - The **Target Language** field determines which template repo to clone
     and which agent templates to use (python, c, or go).
   - Say "continue" when both files are ready.

   **Do not proceed until the user confirms.** The scope and input files
   drive every decision in the rebuild process.

0e. After the user confirms, read `scope.md` → Template Repository field.
   Clone the template repo:
   ```
   git clone <template-repo-url> <dest>/template
   ```
   Verify `<dest>/template/skill.md` exists.

**If the destination repo ALREADY exists:**

Verify `rebuild-inputs/scope.md`, `rebuild-inputs/input.md`, and
`rebuild-inputs/repo/` exist. If `template/` is missing, read `scope.md` →
Template Repository and clone it. Proceed to Step 1.

---

### Step 1: Clean the Destination Directory

Wipe all prior build artifacts so no stale code contaminates the new build.
Preserve `.git/`, `rebuild-inputs/` (user inputs + legacy repo), and `template/`:
```
find <dest> -mindepth 1 -maxdepth 1 ! -name '.git' ! -name 'rebuild-inputs' ! -name 'template' -exec rm -rf {} +
```
**Confirm with the user before deleting.** Show the destination path and ask
for explicit approval. This is a destructive operation.

// turbo
### Step 2: Create Output Directories

```
mkdir -p <dest>/output
mkdir -p <dest>/sre-agent
mkdir -p <dest>/{lang}-developer-agent
mkdir -p <dest>/{lang}-qa-agent
mkdir -p <dest>/docs/adr
mkdir -p <dest>/docs/postmortems
```

> **Language detection:** Read `<dest>/rebuild-inputs/scope.md` → Target Language field to determine `{lang}` (python, c, or go).

### Step 3: Copy Agent Template Files

Copy from rebuilder-template into the destination repo (skip if already present):
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

### Step 4: Run the Ideation Process

Invoke the `@legacy-rebuild` skill. Read `.windsurf/skills/legacy-rebuild/SKILL.md`
(from rebuilder-template) for the process overview, then read and execute
`rebuild/IDEATION_PROCESS.md`. Read `<dest>/rebuild-inputs/input.md` and
`<dest>/rebuild-inputs/scope.md`. Execute Steps 1-11 sequentially, writing
outputs to `<dest>/output/`. Tell the user that they should review before
continuing on steps 12-18.

**Before the Build phase (Steps 12–18):** Read `<dest>/template/skill.md` in
full. Every checkbox in that file is mandatory for the built service. Complete
them all during the Build phase. Do not invent your own tooling, configs, or
patterns — match what the template repo specifies.

### Step 5: Populate Templates

For Steps 7 and 8 (template population), you MUST follow the
`/populate-templates` workflow rules. Read
`.windsurf/workflows/populate-templates.md` (from rebuilder-template) before
populating any template file. The strict rules in that workflow override any
inclination to condense, rephrase, or restructure template content.

### Step 6: Summary

After all steps complete, summarize what was generated and list any `[TODO]`
placeholders that remain for the user to fill in post-deployment.
