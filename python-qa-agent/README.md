# QA Agent

Quality verification for rebuilt Evergreen Python services. The QA agent independently verifies that the developer agent's output meets quality standards — it does **not** replace the developer agent, it checks it.

## What This Is

A verification layer that re-runs every quality gate, checks `/ops/*` endpoint compliance, validates template conformance, and produces an independent quality report. The developer agent writes code to standards; the QA agent proves the standards were met.

Human operators customize the QA agent's acceptance criteria per project — adding app-specific checks, adjusting thresholds, and defining endpoint verification rules that go beyond the universal developer agent standards.

## How It's Activated

The QA agent is loaded two ways:

### Always-On (IDE auto-load)

The same IDE instruction files that load the developer agent also load the QA agent:

| IDE | File | Location in built repo | How it works |
|---|---|---|---|
| **Windsurf** | `.windsurfrules` | repo root | Read at the start of every Cascade session |
| **VS Code + GitHub Copilot** | `.github/copilot-instructions.md` | `.github/` at repo root | Included in every Copilot Chat interaction |
| **Other tools** | `AGENTS.md` | repo root | Cross-tool standard; depends on tool support |

All IDE instruction files load four files: `python-developer-agent/skill.md`, `python-developer-agent/config.md`, `python-qa-agent/skill.md`, and `python-qa-agent/config.md`. This gives the AI assistant awareness of both what to build (developer) and how compliance is verified (QA).

### On-Demand (Windsurf workflow)

Type `/qa` in Windsurf to run the full QA verification workflow. This:

1. Re-reads all four agent files
2. Runs all quality gates independently (pytest, coverage, pylint, black, mypy, pip-audit, interrogate, jscpd, complexipy)
3. Verifies every `/ops/*` endpoint returns required fields
4. Checks template conformance (Dockerfile, entrypoint.sh, Helm chart, env vars)
5. Compares results against the developer agent's `TEST_RESULTS.md`
6. Generates an independent verification report

Use `/qa` after the developer agent claims a feature is complete, during Step 12 of the ideation process, or any time you want an independent quality check.

## Files

| File | Purpose |
|---|---|
| `skill.md` | QA standards — test strategy, quality gates, `/ops/*` contract verification, acceptance criteria framework, comparison workflow |
| `config.md` | Per-project QA config — test commands, thresholds, env var mapping, mock strategy, acceptance criteria (customized by humans) |
| `TEST_RESULTS_TEMPLATE.md` | Template for the quality gate report generated during verification |
| `examples/conftest.py` | Example test fixtures — OTEL disable, env vars, sys.modules mocks, domain-realistic payloads |
| `examples/test_routes.py` | Example API endpoint tests — status, health, drain mode, main endpoint, error handling |
| `examples/test_ops_endpoints.py` | Example `/ops/*` SRE contract tests — all 14 endpoints including drain lifecycle |
| `examples/e2e/test_health.sh` | E2E script — live health endpoint verification |
| `examples/e2e/test_ops_contract.sh` | E2E script — live `/ops/*` contract validation with drain mode lifecycle |
| `examples/e2e/test_smoke.sh` | E2E script — basic request/response smoke test |
| `README.md` | This file |

## What It Verifies

### Quality Gates (11 gates)

| # | Gate | Tool | What It Checks |
|---|------|------|----------------|
| 1 | Unit + API tests | pytest | All tests pass, 0 failures |
| 2 | Test coverage | pytest-cov | ≥ 80% line coverage of `app/` |
| 3 | Lint | pylint | 0 errors |
| 4 | Format | black | All files formatted |
| 5 | Type check | mypy | 0 errors (strict mode) |
| 6 | Dependency vulnerabilities | pip-audit | 0 critical/high CVEs |
| 8 | Docstring coverage | interrogate | Measured baseline, public APIs documented |
| 9 | Duplicate code | pylint + jscpd | < 3% duplication |
| 10 | Cognitive complexity | complexipy | 0 issues at threshold 15 |

### Template Conformance

- `/ops/*` endpoints return required fields per SRE contract
- `environment-check.sh` accounts for all original env vars
- Dockerfile matches template pattern (pinned base image, non-root USER)
- Helm chart renders for all environments
- IDE instruction files exist at built repo root
- Developer agent files populated (no `[TODO]` placeholders remaining)

## How to Customize

The QA agent is designed to be tuned per project. After the replicator populates `config.md` (Step 8d), human operators should:

1. **Add app-specific endpoints** to the "API Endpoints to Verify" table — every endpoint your service exposes should be listed with expected status codes.
2. **Add event types** to the "Event Types to Verify" table — every input format your service accepts, with validation rules.
3. **Adjust thresholds** — if your project requires higher coverage or stricter complexity limits, update the Quality Gate Thresholds table.
4. **Add custom checks** — if your service has domain-specific verification needs (e.g., HMAC validation, specific header requirements), add them to the acceptance criteria.
5. **Map env vars** — document every environment variable rename from the legacy service so the QA agent can verify `environment-check.sh` completeness.

## How It Relates to Other Documents

| Document | Scope | Relationship to QA Agent |
|---|---|---|
| `python-developer-agent/skill.md` | Development standards | **What the QA agent verifies.** The developer agent defines the rules; the QA agent checks they were followed. |
| `python-developer-agent/config.md` | Project-specific dev config | Read by the QA agent for project context (commands, services, environments). |
| `python-qa-agent/skill.md` | QA verification procedures | **How verification is performed.** Quality gates, test strategy, acceptance criteria framework. |
| `python-qa-agent/config.md` | Project-specific QA config | **What is verified.** Endpoint list, env var mapping, thresholds, mock strategy — customized per project. |
| `sre-agent/skill.md` | Incident response | The SRE agent defines the `/ops/*` contract that the QA agent verifies. |
| `STANDARDS.md` | Migration planning | Referenced during comparison workflow (original vs. rebuilt). |

## Setup

If you ran `rebuild/run.sh`, Step 8d of the ideation process has already populated `config.md` with project-specific values and copied `python-qa-agent/` into the built repo.

1. Review the auto-populated content in `config.md` for accuracy.
2. Add app-specific endpoints and event types to the acceptance criteria tables.
3. Adjust quality gate thresholds if needed.
4. Run `/qa` in Windsurf to verify — the workflow reads all files and runs all gates.

If you did **not** run the rebuild process, set up manually:

1. Copy `python-qa-agent/` into your project repo.
2. Fill out `config.md` with your project-specific details — test commands, env var mapping, endpoints, mock strategy.
3. Copy example tests from `examples/` to your `tests/` directory and customize for your service.
4. Run `/qa` in Windsurf or manually run each quality gate command from the table in `skill.md`.
