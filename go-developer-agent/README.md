# Go Developer Agent

Daily development instructions for AI-assisted Go coding sessions. `skill.md` is loaded automatically via IDE-specific instruction files at the project root.

## What This Is

A focused set of instructions that AI coding assistants follow during Go development — idiomatic Go patterns, error handling, concurrency, testing, git workflow, CI/CD pipeline structure, and observability standards.

## How Auto-Loading Works

| IDE | File | Location in built repo | How it works |
|---|---|---|---|
| **Windsurf** | `.windsurfrules` | repo root | Read at the start of every Cascade session |
| **VS Code + GitHub Copilot** | `.github/copilot-instructions.md` | `.github/` at repo root | Included in every Copilot Chat interaction |
| **Other tools** | `AGENTS.md` | repo root | Cross-tool standard; depends on tool support |

All files contain the same instruction: read `go-developer-agent/skill.md`, `go-developer-agent/config.md`, `go-qa-agent/skill.md`, and `go-qa-agent/config.md` before performing any task.

## Files

| File | Purpose |
|---|---|
| `.windsurfrules` | Project rules for Windsurf — placed at repo root |
| `.github/copilot-instructions.md` | Project rules for VS Code + GitHub Copilot |
| `skill.md` | Go development standards — idiomatic Go patterns |
| `config.md` | Per-project config — commands, environments, services |
| `README.md` | This file |

## What It Covers

- **Coding practices** — idiomatic Go patterns, error handling, concurrency, interfaces
- **Testing** — table-driven tests, race detector, coverage
- **Git workflow** — branching, commit messages, PR expectations
- **CI/CD pipeline** — gofmt → golangci-lint → go vet → test → gosec → container smoke test
- **Observability** — structured logging, OTEL, `/ops/*` endpoints
