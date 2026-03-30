---
description: Reload the developer agent standards mid-session or explicitly activate development mode
---

# Developer Agent Reload Workflow

This workflow explicitly reloads the developer and QA agent standards. Use it when:
- You've edited `{lang}-developer-agent/skill.md`, `{lang}-developer-agent/config.md`, `{lang}-qa-agent/skill.md`, or `{lang}-qa-agent/config.md` and want the agent to re-read them
- You want to confirm both agents are active and have current context
- You're switching focus back to development after a different task

Both agents are normally auto-loaded via `.windsurfrules` at session start. This workflow provides an explicit reload for mid-session use.

> **Language detection:** Read `scope.md` → Target Language field to determine `{lang}` (python, c, or go). All agent directory references below use `{lang}-developer-agent/` and `{lang}-qa-agent/`.

## Steps

1. Read all four agent files in full:
   - `{lang}-developer-agent/skill.md` — development standards
   - `{lang}-developer-agent/config.md` — project-specific settings
   - `{lang}-qa-agent/skill.md` — QA verification procedures
   - `{lang}-qa-agent/config.md` — project-specific acceptance criteria

2. After reading all four files, confirm by stating: **"Reloaded [project-name] developer and QA standards from skill.md and config.md."**

3. Summarize any recent changes to the agent files (if the user mentions they edited them), or confirm the current project configuration:
   - **Project name** from {lang}-developer-agent/skill.md header
   - **Framework** from {lang}-developer-agent/config.md
   - **Test command** from {lang}-developer-agent/config.md Development Commands table
   - **Quality gate thresholds** from {lang}-qa-agent/config.md

4. Resume normal development work with the reloaded standards active.
