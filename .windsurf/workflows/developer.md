---
description: Reload the developer agent standards mid-session or explicitly activate development mode
---

# Developer Agent Reload Workflow

This workflow explicitly reloads the developer and QA agent standards. Use it when:
- You've edited `developer-agent/skill.md`, `developer-agent/config.md`, `qa-agent/skill.md`, or `qa-agent/config.md` and want the agent to re-read them
- You want to confirm both agents are active and have current context
- You're switching focus back to development after a different task

Both agents are normally auto-loaded via `.windsurfrules` at session start. This workflow provides an explicit reload for mid-session use.

## Steps

1. Read all four agent files in full:
   - `developer-agent/skill.md` — development standards
   - `developer-agent/config.md` — project-specific settings
   - `qa-agent/skill.md` — QA verification procedures
   - `qa-agent/config.md` — project-specific acceptance criteria

2. After reading all four files, confirm by stating: **"Reloaded [project-name] developer and QA standards from skill.md and config.md."**

3. Summarize any recent changes to the agent files (if the user mentions they edited them), or confirm the current project configuration:
   - **Project name** from developer-agent/skill.md header
   - **Framework** from developer-agent/config.md
   - **Test command** from developer-agent/config.md Development Commands table
   - **Quality gate thresholds** from qa-agent/config.md

4. Resume normal development work with the reloaded standards active.
