# C Developer Agent

Daily development instructions for AI-assisted C coding sessions. `skill.md` is loaded automatically via IDE-specific instruction files at the project root.

## What This Is

A focused set of instructions that AI coding assistants follow during C development — coding practices (Inscape C standard based on Linux kernel style), testing, git workflow, CI/CD pipeline structure, environment promotion, service bootstrap requirements, and observability standards.

## How Auto-Loading Works

| IDE | File | Location in built repo | How it works |
|---|---|---|---|
| **Windsurf** | `.windsurfrules` | repo root | Read at the start of every Cascade session |
| **VS Code + GitHub Copilot** | `.github/copilot-instructions.md` | `.github/` at repo root | Included in every Copilot Chat interaction |
| **Other tools** | `AGENTS.md` | repo root | Cross-tool standard; depends on tool support |

All files contain the same instruction: read `c-developer-agent/skill.md`, `c-developer-agent/config.md`, `c-qa-agent/skill.md`, and `c-qa-agent/config.md` before performing any task.

## Files

| File | Purpose |
|---|---|
| `.windsurfrules` | Project rules for Windsurf — placed at repo root |
| `.github/copilot-instructions.md` | Project rules for VS Code + GitHub Copilot |
| `skill.md` | C development standards — Inscape C standard |
| `config.md` | Per-project config — commands, environments, services |
| `README.md` | This file |

## What It Covers

- **Coding practices** — Inscape C standard (kernel.org base with overrides), error handling, memory management
- **Testing** — Unity/CMocka unit tests, gcov/lcov coverage
- **Git workflow** — branching, commit messages, PR expectations
- **CI/CD pipeline** — clang-format → cppcheck → build → test → container smoke test
- **Observability** — stdout/stderr logging, OTEL, `/ops/*` endpoints
