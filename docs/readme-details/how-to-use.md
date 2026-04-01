# How to Use the Rebuilder Template

Full phase-by-phase guide. For a quick overview, see the [README](../../README.md).

---

## Quick Start

### Windsurf

Open this repo in Windsurf and tell Cascade what you want to rebuild:

> **"Rebuild evergreen-tvevents"**

Cascade invokes the `@legacy-rebuild` skill, sets up the project directory, and runs the 18-step analysis. You review the outputs and guide the build.

### VS Code + Copilot

Open this repo in VS Code. Copilot auto-loads `.github/copilot-instructions.md`. Tell Copilot:

> **"Read rebuild/IDEATION_PROCESS.md and rebuild evergreen-tvevents"**

VS Code does not have Windsurf's `/run-replicator` workflow or `@legacy-rebuild` skill, so you reference the process file directly. The agent follows the same 18-step process.

---

## Running All Steps Without Pausing

By default the process pauses after Phase 1 (Steps 1–11) so you can review the analysis before the build starts. To run all 18 steps in one pass:

> **Windsurf:** *"Rebuild my-service — run all steps including the build, do not pause between phases"*
>
> **VS Code + Copilot:** *"Read rebuild/IDEATION_PROCESS.md and rebuild my-service. Run all 18 steps including the build phase — do not stop after analysis."*

> [!NOTE]
> The analysis-then-review workflow exists for a reason: the PRD and target architecture come from AI analysis of your legacy code, and you may want to adjust them before code is written. Use the full rebuild shortcut when you trust the defaults or want a fast first pass you'll iterate on.

---

## Phase 1: Analyze

Tell the agent which legacy repo to rebuild. It clones the repo, creates the project directory, copies templates, and executes Steps 1–11.

### Windsurf

| What you want | What to say |
|---|---|
| Rebuild a single service | *"Rebuild my-service"* |
| Rebuild with related repos | *"Rebuild my-service with adjacent repos auth-api and worker-app"* |
| Use the workflow directly | `/run-replicator` on my-service |

### VS Code + Copilot

| What you want | What to say |
|---|---|
| Rebuild a single service | *"Read rebuild/IDEATION_PROCESS.md and rebuild my-service. The repo is at github.com/your-org/my-service."* |
| Rebuild with related repos | *"Read rebuild/IDEATION_PROCESS.md and rebuild my-service with adjacent repos auth-api and worker-app."* |

All outputs land in `rebuild-inputs/<project>/`.

> [!IMPORTANT]
> Review the outputs — especially `scope.md` Target State and `output/prd.md`. The Current Application section comes from the code; the Target State comes from your decisions. Adjust before proceeding to the build phase.

---

## Phase 2: Build

After reviewing the Phase 1 outputs, create a new repo and ask the agent to build it:

> *"Create a new repo for the rebuilt service and build it from the PRD."*

This works in both Windsurf and VS Code. The agent copies the populated agent configs, PRD, ADRs, and docs into the new repo. In the new repo, the developer and QA agents auto-load via `.windsurfrules` (Windsurf) or `.github/copilot-instructions.md` (VS Code).

After the code is written:
- **Windsurf:** Run `/qa` to independently verify quality gates.
- **VS Code:** Ask Copilot: *"Read {lang}-qa-agent/skill.md and run the full QA verification."*

---

## Phase 3: Operate

Deploy the SRE agent from `sre-agent/runtime/`. Fill in `sre-agent/config.md` with service registry URLs and PagerDuty escalation config. The agent receives monitoring webhooks, diagnoses issues via `/ops/*` endpoints, and escalates when it can't resolve.

See `sre-agent/runtime/README.md` for deployment instructions.

---

## Quick Reference

| Action | Windsurf | VS Code + Copilot |
|---|---|---|
| Rebuild a service | *"Rebuild my-service"* | *"Read rebuild/IDEATION_PROCESS.md and rebuild my-service"* |
| Rebuild (all steps, no pause) | *"Rebuild my-service — run all steps including the build, do not pause between phases"* | *"Read rebuild/IDEATION_PROCESS.md and rebuild my-service. Run all 18 steps including the build phase — do not stop after analysis."* |
| Run QA verification | `/qa` | *"Read {lang}-qa-agent/skill.md and run QA verification"* |
| Reload agent standards | `/developer` | *"Re-read {lang}-developer-agent/skill.md and {lang}-qa-agent/skill.md"* |
| Profile a slow endpoint | *"Read performance-agent/skill.md and profile the POST /events endpoint — it's slow at P99"* | *"Read performance-agent/skill.md and profile the POST /events endpoint — it's slow at P99"* |
| Investigate a memory leak | *"Read performance-agent/skill.md — memory usage keeps climbing in the worker process"* | *"Read performance-agent/skill.md — memory usage keeps climbing in the worker process"* |
| Check SRE alerting config | *"Read sre-agent/skill.md — what's the alerting config for this service?"* | *"Read sre-agent/skill.md — what's the alerting config for this service?"* |
| Explore the rebuild process | *"@legacy-rebuild what steps are in the process?"* | *"Read rebuild/IDEATION_PROCESS.md and summarize the steps"* |
