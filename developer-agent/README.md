# Developer Agent

Daily development instructions for AI-assisted coding sessions. `WINDSURF_DEV.md` is loaded automatically via IDE-specific instruction files at the project root.

## What This Is

A focused set of instructions that AI coding assistants follow during development — coding practices, testing, git workflow, CI/CD pipeline structure, environment promotion, service bootstrap requirements, Terraform workflow, and observability standards.

This is not the migration planning document (`WINDSURF.md`) and not the SRE agent (`sre-agent/WINDSURF_SRE.md`). The developer agent handles the daily work of building services that conform to the project's standards.

## How Auto-Loading Works

Each IDE has its own convention for reading project-level instructions automatically:

| IDE | File | Location in built repo | How it works |
|---|---|---|---|
| **Windsurf** | `.windsurfrules` | repo root | Read at the start of every Cascade session |
| **VS Code + GitHub Copilot** | `.github/copilot-instructions.md` | `.github/` at repo root | Included in every Copilot Chat interaction |
| **Cursor** | `.cursorrules` | repo root | Read at the start of every session (same content as `.windsurfrules`) |

All files contain the same instruction: read `developer-agent/WINDSURF_DEV.md` and `developer-agent/config.md` before performing any task.

**Without the correct file for your IDE at the project root, the developer agent prompt is NOT loaded automatically.** You would have to manually reference the files in every session.

This mirrors how the SRE agent works: `agent.py` reads `WINDSURF_SRE.md` from disk and sends it as the system prompt on every alert. The developer agent relies on IDE instruction files to achieve the same guarantee for human development sessions.

## When to Use

Every AI-assisted development session — the IDE instruction files ensure it happens automatically regardless of which editor the developer uses. It keeps context overhead low while ensuring every service is built to the same standards — same pipeline, same environment strategy, same observability contract, same bootstrap requirements.

## Files

| File | Purpose |
|---|---|
| `.windsurfrules` | Project rules for Windsurf — placed at repo root, auto-read on session start |
| `.github/copilot-instructions.md` | Project rules for VS Code + GitHub Copilot — placed in `.github/` at repo root, auto-included in Copilot Chat |
| `WINDSURF_DEV.md` | Development instructions — loaded by IDE instruction files |
| `config.md` | Per-project config — loaded by IDE instruction files |
| `README.md` | This file |

## What It Covers

- **Coding practices** — error handling, security, input validation, dependency management
- **Testing** — unit, API, integration, contract, E2E test expectations
- **Git workflow** — branching, commit messages, PR expectations
- **CI/CD pipeline** — defined stage structure from lint through production deploy, pipeline-as-code, container build and tagging strategy
- **Environment strategy** — dev/staging/prod with promotion flow, environment parity, rollback via image SHA
- **Service bootstrap** — checklist of what every new service ships with from day one (Dockerfile, CI, Terraform, `/ops/*` endpoints, OpenAPI spec, tests)
- **Dependency management** — internal libraries via private registries, API contracts via OpenAPI, third-party pinning and patching cadence
- **Observability** — Golden Signals, RED method, SLOs, composite health, `/ops/*` endpoints as definition of done
- **Terraform workflow** — plan on PR, apply on merge, remote state, environment promotion
- **Task scope rules** — GitHub issues for all work, no scope creep, prompting audit trail

## Observability: OTEL and `/ops/*`

The developer agent defines two observability standards that every service must implement:

1. **OpenTelemetry (OTEL)** — push-based continuous export of metrics, traces, and logs to your APM platform (Grafana, Datadog, New Relic, etc.). This is how you build dashboards, set up alerting rules, and analyze historical trends. OTEL is configured via standard environment variables and runs as a no-op when not configured.

2. **`/ops/*` endpoints** — pull-based programmatic API for on-demand diagnostics. The SRE agent queries these endpoints to diagnose issues and take remediation actions. Humans and scripts also use them for quick health checks.

These are complementary, not redundant:

- **OTEL** answers: "What has been happening over time?" — continuous, time-series, powers dashboards and alerts.
- **`/ops/*`** answers: "What is happening right now?" — on-demand, structured snapshots, powers the SRE agent's diagnostic loop.

Both report the same underlying signals (Golden Signals, RED metrics, dependency status). The service maintains a single source of truth for these signals internally — OTEL instruments and `/ops/*` responses are updated at the same instrumentation points.

The SRE agent runtime also instruments itself with OTEL because it is a service that follows the same standards. The SRE agent does **not** consume OTEL data from other services — it diagnoses them exclusively through their `/ops/*` endpoints.

## How It Relates to Other Documents

| Document | Scope | When to Load |
|---|---|---|
| `WINDSURF.md` | Migration planning — architecture decisions, technology selection, data migration, cutover, DR, ADRs, RBAC, feature parity | During migration planning phases |
| `developer-agent/WINDSURF_DEV.md` | Daily development — coding, testing, CI/CD, environments, service bootstrap, observability | Every development session (via IDE instruction files) |
| `sre-agent/WINDSURF_SRE.md` | Incident response — alert triage, diagnostics, remediation, escalation | Loaded by the SRE agent runtime (`agent.py`) |

## Setup

If you ran `rebuild/run.sh`, Steps 7a, 7b, and 7c of the rebuild process have already populated the project-specific sections of `WINDSURF_DEV.md`, `config.md`, and generated the IDE instruction files.

1. Review the auto-populated content in `WINDSURF_DEV.md` and `config.md` for accuracy.
2. Fill in any remaining `[TODO]` markers in `config.md` — secrets references, monitoring URLs, and environment URLs are not known until infrastructure is provisioned.
3. Copy the IDE instruction files to your rebuild project repo:
   - **Windsurf:** Copy `.windsurfrules` to the **repo root**
   - **VS Code + Copilot:** Copy `.github/copilot-instructions.md` into `.github/` at the **repo root**
   - **Cursor:** Copy `.windsurfrules` to the **repo root** and rename to `.cursorrules`
4. Copy `developer-agent/WINDSURF_DEV.md` and `developer-agent/config.md` into your rebuild project repo under `developer-agent/`.
5. Open the project in your IDE — the instruction file will tell the AI assistant to read both files before any work.

If you did **not** run the rebuild process, set up manually:

1. Copy the IDE instruction file for your editor from `developer-agent/`:
   - **Windsurf:** `.windsurfrules` → repo root
   - **VS Code + Copilot:** `.github/copilot-instructions.md` → `.github/` at repo root
   - **Cursor:** `.windsurfrules` → repo root, renamed to `.cursorrules`
2. Fill out `config.md` with your project-specific details — commands, environments, CI/CD config, services.
3. Fill in the placeholder sections in `WINDSURF_DEV.md` (project name, architecture, development environment, logging/tracing setup).
4. Copy both files into `developer-agent/` in your project repo.
5. Open the project in your IDE — the instruction file will tell the AI assistant to read both files before any work.
