---
description: Reload the developer agent standards mid-session or explicitly activate development mode
---

# Developer Agent Reload Workflow

This workflow explicitly reloads the developer agent standards. Use it when:
- You've edited `developer-agent/skill.md` or `config.md` and want the agent to re-read them
- You want to confirm the developer agent is active and has current context
- You're switching focus back to development after a QA verification session (`/qa`)

The developer agent is normally auto-loaded via `.windsurfrules` at session start. This workflow provides an explicit reload for mid-session use.

## Steps

1. Read the developer agent standards and project-specific config:
   - Read `developer-agent/skill.md` in full — these are the development standards
   - Read `developer-agent/config.md` in full — these are the project-specific settings

2. Read the QA agent standards (for awareness of quality verification criteria):
   - Read `qa-agent/skill.md` in full — these are the QA verification procedures
   - Read `qa-agent/config.md` in full — these are the project-specific acceptance criteria

3. After reading all four files, confirm by stating: **"Reloaded [project-name] developer and QA standards from skill.md and config.md."**

4. Summarize any recent changes to the agent files (if the user mentions they edited them), or confirm the current project configuration:
   - **Project name** from developer-agent/skill.md header
   - **Framework** from developer-agent/config.md
   - **Test command** from developer-agent/config.md Development Commands table
   - **Quality gate thresholds** from qa-agent/config.md

5. Resume normal development work with the reloaded standards active.
