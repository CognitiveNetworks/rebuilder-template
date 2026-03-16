# Project Instructions — Auto-loaded by GitHub Copilot in VS Code
#
# This file ensures the developer agent and QA agent prompts are read
# before any coding work begins. VS Code with GitHub Copilot reads
# `.github/copilot-instructions.md` automatically and includes it in every
# Copilot Chat interaction.
#
# Equivalent of `.windsurfrules` for Windsurf users.

## Required Context

Before writing any code, making any changes, or answering any questions about
this project, you MUST read these four files in full:

### Developer Agent (development standards)

1. `developer-agent/skill.md` — development standards, coding practices,
   testing expectations, CI/CD pipeline structure, service bootstrap checklist,
   and observability requirements.
2. `developer-agent/config.md` — project-specific configuration: commands,
   environments, services, secrets references, and SRE agent integration.

### QA Agent (quality verification)

3. `qa-agent/skill.md` — QA standards, quality gates, test strategy,
   acceptance criteria, and verification procedures. The QA agent verifies
   the developer agent's output — it does not replace it.
4. `qa-agent/config.md` — project-specific QA configuration: test commands,
   thresholds, env var mapping, mock strategy, and acceptance criteria.

Do not proceed with any task until all four files have been read. The developer
agent files define the standards every change must conform to. The QA agent
files define how compliance is verified.

## Session Greeting

At the start of every new conversation, after reading all four files, confirm by
stating: **"Loaded [project-name] developer and QA standards from skill.md and
config.md."** (Replace `[project-name]` with the actual project name from the
header of developer-agent/skill.md.) If you cannot find or read any file, say so
explicitly instead of proceeding silently.

## Quick Reference

- Run tests: see developer-agent/config.md Development Commands table
- Run locally: see developer-agent/config.md Development Commands table
- Service bootstrap checklist: developer-agent/skill.md → Service Bootstrap section
- Observability contract: developer-agent/skill.md → Observability section
- CI/CD pipeline: developer-agent/skill.md → CI/CD section + config.md CI/CD section
- Quality gates: qa-agent/skill.md → Quality Gates section
