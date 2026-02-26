# Project Instructions — Auto-loaded by GitHub Copilot in VS Code
#
# This file ensures the developer agent prompt and project config are read
# before any coding work begins. VS Code with GitHub Copilot reads
# `.github/copilot-instructions.md` automatically and includes it in every
# Copilot Chat interaction.
#
# Equivalent of `.windsurfrules` for Windsurf users.

## Required Context

Before writing any code, making any changes, or answering any questions about
this project, you MUST read these two files in full:

1. `developer-agent/WINDSURF_DEV.md` — development standards, coding practices,
   testing expectations, CI/CD pipeline structure, service bootstrap checklist,
   and observability requirements.
2. `developer-agent/config.md` — project-specific configuration: commands,
   environments, services, secrets references, and SRE agent integration.

Do not proceed with any task until both files have been read. These files define
the standards every change must conform to.

## Session Greeting

At the start of every new conversation, after reading both files, confirm by
stating: **"Loaded [project-name] developer standards from WINDSURF_DEV.md and
config.md."** (Replace `[project-name]` with the actual project name from the
header of WINDSURF_DEV.md.) If you cannot find or read either file, say so
explicitly instead of proceeding silently.

## Quick Reference

- Run tests: see config.md Development Commands table
- Run locally: see config.md Development Commands table
- Service bootstrap checklist: WINDSURF_DEV.md → Service Bootstrap section
- Observability contract: WINDSURF_DEV.md → Observability section
- CI/CD pipeline: WINDSURF_DEV.md → CI/CD section + config.md CI/CD section
