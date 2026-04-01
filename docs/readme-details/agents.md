# Agents Reference

Detailed reference for each agent type included in the rebuilder template.

---

## Developer Agents

The `{lang}-developer-agent/` directories contain the daily development instructions for AI-assisted coding sessions. Each language has its own agent with language-specific coding standards, tools, and CI/CD pipelines — but all share the same structural patterns and quality expectations.

| Language | Directory | Coding Standard |
|---|---|---|
| Python | `python-developer-agent/` | PEP 8, Black, pylint, mypy, pytest |
| C | `c-developer-agent/` | Inscape C standard (kernel.org base + 4-space indent, Allman braces) |
| Go | `go-developer-agent/` | Idiomatic Go (gofmt, golangci-lint, go test -race) |

**What each covers:**
- **Coding practices** — error handling, security, input validation, dependency management, removal of outdated code (DP2.5, Stackdriver), no SRE Agent for library repos
- **Testing** — unit, API, integration, contract, E2E expectations
- **CI/CD pipeline** — lint → test → build → scan → deploy-to-dev → integration tests → promote-to-staging → E2E → promote-to-prod
- **Environment strategy** — dev/staging/prod with promotion flow, environment parity, rollback via image SHA
- **Service bootstrap** — checklist of what every new service ships with from its first PR (Dockerfile, CI pipeline, Terraform, `/ops/*` endpoints, OpenAPI spec, tests)
- **Terraform workflow** — plan on PR, apply on merge, remote state, environment-specific variables
- **Observability** — Golden Signals, RED method, SLOs, `/ops/*` endpoints as definition of done

**Components:**
- **`skill.md`** — project-specific coding rules (HOW TO WRITE CODE). Loaded automatically via IDE instruction files (`.windsurfrules`, `.github/copilot-instructions.md`) alongside `template/skill.md` (HOW TO BUILD) and QA agent files (HOW TO CHECK).
- **`config.md`** — per-project configuration: dev commands, CI/CD pipeline, environments, services, secrets references, monitoring links.

> [!TIP]
> The rebuild process (`run.sh`) auto-populates `skill.md` and `config.md` from the PRD and chosen rebuild candidate (Step 8). Project name, architecture, development commands, CI/CD pipeline, Terraform settings, and observability config are filled in before the first line of code is written. Copy both files into the target repo, and the AI agent will follow the standards defined by the rebuild process.

---

## QA Agents

The `{lang}-qa-agent/` directories contain quality verification procedures for rebuilt services. Each language has its own QA agent with language-specific quality gates. The QA agent independently verifies that the developer agent's output meets quality standards — it does **not** replace the developer agent, it checks it.

| Language | Directory | Quality Gates |
|---|---|---|
| Python | `python-qa-agent/` | pytest, pylint, black, mypy, vulture, pip-audit, interrogate, complexipy |
| C | `c-qa-agent/` | clang-format, cppcheck, clang-tidy, Unity tests, gcov/lcov, lizard |
| Go | `go-qa-agent/` | gofmt, go vet, golangci-lint, go test -race, gosec, govulncheck |

**What each does:**
1. **Re-runs every quality gate independently** — using the language-appropriate tools. Compares results against the developer agent's `TEST_RESULTS.md` and flags discrepancies.
2. **Verifies `/ops/*` endpoint compliance** — checks that every required diagnostic and remediation endpoint exists and returns the correct fields per the SRE contract.
3. **Checks template conformance** — Dockerfile, entrypoint.sh, Helm chart, environment-check.sh, IDE instruction files must match template patterns.
4. **Produces an independent quality report** — generates `TEST_RESULTS.md` from its own gate runs, not from the developer agent's claims.
5. **Flags gaps for human review** — categorizes findings as Critical / Important / Minor. Does not silently fix business logic.

**Components:**
- **`skill.md`** — QA verification procedures: 5-level test strategy, 11 quality gates, `/ops/*` contract verification, acceptance criteria framework, comparison workflow, and bug reporting protocol. This file is universal — the same standards apply to every rebuilt service.
- **`config.md`** — per-project QA configuration: test commands, quality gate thresholds, env var mapping, mock strategy, endpoint list, event types, and acceptance criteria. **Human operators customize this file** to add app-specific checks and adjust thresholds.
- **`TEST_RESULTS_TEMPLATE.md`** — template for the quality gate report. Includes sections for tool versions, codebase metrics, core and extended gate results, bugs found, untestable items, and template conformance.
- **`examples/`** — example test patterns including `conftest.py` (fixtures), `test_routes.py` (API tests), `test_ops_endpoints.py` (`/ops/*` contract tests), and E2E shell scripts for live instance verification.

**How it's activated:**
- **Always-on** — IDE instruction files load `template/skill.md`, developer agent files, and QA agent files on every session.
- **On-demand** — Type `/qa` in Windsurf to run the full QA verification workflow. Type `/developer` to reload all agent files mid-session.

> [!TIP]
> The rebuild process (`run.sh`) auto-populates `config.md` from the PRD and developer agent config (Step 8d). Endpoint lists, env var mappings, and mock strategies are filled in before the first quality check. Human operators then customize the acceptance criteria — adding app-specific checks, adjusting thresholds, and defining verification rules beyond the universal standards. After the developer agent claims compliance (Step 12), activate the QA agent via `/qa` to independently verify.

---

## SRE Agent

The `sre-agent/` directory contains a complete, deployable SRE agent that provides automated incident response for rebuilt services.

**What it does:**
1. **Receives alerts from monitoring platforms** — webhooks from GCP Cloud Monitoring, New Relic, Datadog, or similar trigger the agent. The alert intake pipeline deduplicates by incident ID, serializes per service, enforces a global concurrency limit (default: 3), and orders queued alerts by priority.
2. **Diagnoses issues** — calls `/ops/status`, `/ops/health` (includes dependency health with latency), `/ops/metrics`, and `/ops/errors` on the affected service. Follows the dependency chain to find the root cause.
3. **Classifies the problem** — infrastructure, application, dependency, data, or configuration.
4. **Remediates safely** — executes playbook-defined actions (cache flush, cache refresh, circuit breaker reset, log level adjustment). All actions are idempotent and non-destructive.
5. **Escalates when unsure** — if no playbook matches, remediation fails, or the issue involves data integrity, security, or infrastructure changes, the agent escalates to a human via PagerDuty with a full diagnostic summary.
6. **Tracks token usage** — every API call's token consumption is tracked per incident and globally. Configurable per-incident and hourly token budgets prevent runaway costs — the agent auto-escalates to a human when a budget is exceeded.
7. **Documents everything** — writes an incident report for every alert it responds to, including token usage.

**Components:**
- **`skill.md`** — the agent's instructions, diagnostic workflow, escalation rules, and hard safety constraints. **This file is the agent's brain.** On every alert, `agent.py` reads it from disk and sends the full text to the LLM as the `system` message — the first message in the conversation.
- **`config.md`** — per-project configuration: service registry, SLO thresholds, PagerDuty escalation config, escalation contacts, cloud platform IAM roles, and runtime environment variables.
- **`playbooks/`** — remediation playbooks for common incident types (high error rate, high latency, dependency failure, saturation, certificate expiry).
- **`incidents/`** — agent-written incident reports with diagnosis, actions taken, and resolution status.
- **`runtime/`** — the deployable Python/FastAPI service. Receives monitoring platform webhooks, runs the agentic loop, executes tool calls, and escalates to PagerDuty when needed. Includes alert intake pipeline, token budget controls, OpenTelemetry instrumentation, Dockerfile, and Terraform templates for Cloud Run.

See `sre-agent/runtime/README.md` for setup and deployment.

> [!TIP]
> The rebuild process (`run.sh`) auto-configures the agent's tech stack from the chosen rebuild candidate (Step 7). Your rebuilt services expose `/ops/*` endpoints as defined in `STANDARDS.md`. The agent uses those endpoints to monitor and respond to incidents. Fill in `config.md` with your service URLs, PagerDuty escalation config, and escalation contacts, deploy the runtime, and the agent is operational.

---

## Performance Agent

The `performance-agent/` directory provides specialized Python profiling and optimization capabilities. It is loaded **on demand** — not always-on like the developer and QA agents.

**What it covers:**
- **Profiling tools** — cProfile, line_profiler, memory_profiler, py-spy, tracemalloc
- **Optimization patterns** — list comprehensions, generators, string concatenation, dictionary lookups, NumPy vectorization, caching, multiprocessing, async I/O
- **Database optimization** — batch operations, query planning, indexing, connection pooling
- **Memory management** — leak detection, `__slots__`, weak references, iterators vs lists
- **Benchmarking** — timeit, pytest-benchmark, custom decorators

**Components:**
- **`skill.md`** — profiling tools, optimization patterns, and best practices.
- **`config.md`** — per-project performance configuration: latency targets, hot paths, profiling commands, infrastructure context.
- **`references/advanced-patterns.md`** — extended examples: NumPy vectorization, caching with `lru_cache`, `__slots__`, multiprocessing, async I/O, database batching, and pytest-benchmark.

**How to activate:**
- **Windsurf:** *"Read performance-agent/skill.md and profile the event ingestion endpoint"*
- **VS Code + Copilot:** *"Read performance-agent/skill.md and performance-agent/config.md. The POST /events endpoint is slow at P99 — help me profile it."*

Based on [wshobson/agents — python-performance-optimization](https://github.com/wshobson/agents/tree/main/plugins/python-development/skills/python-performance-optimization), adapted to the rebuilder agent convention.
