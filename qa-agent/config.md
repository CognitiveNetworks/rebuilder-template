# QA Agent Configuration

**Instructions:** Fill out this file when setting up the QA agent for a specific project. This provides project-specific context that the agent needs for quality assurance work. Replace all `[TODO]` placeholders with actual values.

## Project

- **Project Name:** [TODO: e.g., evergreen-tvevents]
- **Repository:** [TODO: e.g., CognitiveNetworks/evergreen-tvevents]
- **Primary Language:** Python 3.12
- **Framework:** FastAPI ≥ 0.115.0
- **Original Legacy Repo:** [TODO: e.g., CognitiveNetworks/tvevents-k8s]

## Test Commands

| Command | Purpose |
|---|---|
| `pip install -e ".[dev]"` | Install all dependencies including test tools |
| `pytest tests/ -x` | Run tests, stop on first failure |
| `pytest tests/ --cov=src/app --cov-fail-under=80` | Run tests with coverage enforcement |
| `pytest tests/test_routes.py tests/test_ops_endpoints.py` | Run API + /ops/* contract tests only |
| `pylint src tests` | Lint check |
| `black --check src/ tests/` | Format check |
| `mypy src/app/` | Type check |
| `radon cc src/ -a -nc` | Cyclomatic complexity |
| `radon mi src/` | Maintainability index |
| `vulture src/ --min-confidence 80` | Dead code detection |
| `pip-audit` | Dependency vulnerability scan |
| `interrogate src/ -v` | Docstring coverage |
| `pylint --disable=all --enable=duplicate-code src/` | Duplicate code check |
| `complexipy src -mx 15 -d low` | Cognitive complexity |
| `helm lint charts/` | Helm chart lint |
| `tests/test-helm-template.sh -all` | Helm template rendering |

## Quality Gate Thresholds

| Gate | Threshold | Blocks |
|---|---|---|
| Test failures | 0 | Merge |
| Line coverage | ≥ 80% | Merge |
| Lint errors | 0 | Merge |
| Format violations | 0 | Merge |
| Type errors | 0 | Merge |
| Cyclomatic complexity | Average A or B, no function ≥ C | Release |
| Maintainability index | All files A or B | Release |
| Dead code | 0 findings | Release |
| Runtime CVEs | 0 | Release |
| Docstring coverage | ≥ 80% | Release |
| Duplicate code | < 3% | Release |
| Cognitive complexity (C901) | 0 issues | Release |
| Helm lint | 0 errors | Release |

## Extended Tool Versions

> Pin these to match CI. Update when CI changes.

| Tool | Version |
|---|---|
| Python | 3.12.x |
| pytest | 8.3.x |
| pylint | ≥ 3.2.5 |
| mypy | latest |
| radon | ≥ 6.0.0 |
| vulture | ≥ 2.10 |
| pip-audit | ≥ 2.9.0 |
| interrogate | ≥ 1.7.0 |
| pylint | ≥ 3.0.0 |
| helm | ≥ 3.14.0 |

## Test Environments

| Environment | Purpose | Dependencies |
|---|---|---|
| Local (pytest) | Unit + API tests | All external deps mocked via `conftest.py` |
| CI (GitHub Actions) | Full quality gate suite | All external deps mocked |
| Dev (deployed) | Integration / smoke tests | Real RDS, Kafka, OTEL collector |
| Staging (deployed) | E2E tests | Real infrastructure, prod-like config |

## External Dependency Mocking

> Map each external dependency to its mock strategy in tests.

| Dependency | Mock Target | Strategy |
|---|---|---|
| RDS / PostgreSQL | `rds_module` | `sys.modules` mock in `conftest.py` |
| Kafka / MSK | `kafka_module` | `sys.modules` mock in `conftest.py` |
| cnlib (token_hash) | `cnlib.cnlib.token_hash` | `sys.modules` mock in `conftest.py` |
| cnlib (log) | `cnlib.cnlib.log` / `cnlib.log` | `sys.modules` mock in `conftest.py` |
| OTEL SDK | N/A | Disabled via `OTEL_SDK_DISABLED=true` env var |

## Required Environment Variables for Tests

> These must be set in `conftest.py` via `os.environ.setdefault()` before any app imports.

| Variable | Test Default | Notes |
|---|---|---|
| `OTEL_SDK_DISABLED` | `true` | Disables all OTEL in tests |
| `ENV` | `dev` | |
| `LOG_LEVEL` | `DEBUG` | |
| `SERVICE_NAME` | `[TODO: service name]` | |
| `TEST_CONTAINER` | `true` | Triggers OTEL disable in env-check |

> Add app-specific variables below:

| Variable | Test Default | Notes |
|---|---|---|
| [TODO] | [TODO] | [TODO: describe] |

## Acceptance Criteria — App-Specific

> List the app-specific acceptance criteria here. These supplement the generic criteria in `skill.md`.

### API Endpoints to Verify

| Method | Path | Expected Status | Notes |
|---|---|---|---|
| GET | `/status` | 200, body: `OK` | Health check |
| GET | `/health` | 200 or 503 | Deep health with dependency checks |
| GET | `/ops/status` | 200 | Composite health verdict |
| GET | `/ops/health` | 200 | Dependency-level health |
| GET | `/ops/metrics` | 200 | Golden Signals + RED |
| GET | `/ops/config` | 200 | Non-sensitive runtime config |
| GET | `/ops/errors` | 200 | Error summary |
| GET | `/ops/cache` | 200 | Cache statistics |
| POST | `/ops/loglevel` | 200 or 400 | Change log level |
| POST | `/ops/log-level` | 200 or 400 | Change log level (canonical path) |
| POST | `/ops/cache/flush` | 200 or 500 | Flush and refresh cache |
| POST | `/ops/cache/refresh` | 200 | Refresh cache from source |
| POST | `/ops/circuits` | 200 | Circuit breaker state |
| [TODO] | [TODO] | [TODO] | [TODO: app-specific endpoints] |

### Event Types to Verify

> List all event types the service handles. For each, verify validation and output generation.

| Event Type | Class | Validation | Output |
|---|---|---|---|
| [TODO] | [TODO] | [TODO: describe validation rules] | [TODO: describe output shape] |

### Environment Variable Mapping (Original → Rebuilt)

> Document all variable renames from the legacy service.

| Original | Rebuilt | Notes |
|---|---|---|
| [TODO] | [TODO] | [TODO: e.g., RDS_HOST → DB_HOST] |

## Comparison Checklist

> Check off each item when comparing a rebuilt service against its original.

- [ ] `environment-check.sh` — all original vars accounted for (renamed or removed with justification)
- [ ] `entrypoint.sh` — matches template pattern, includes `--log-level` and `--reload`
- [ ] `Dockerfile` — matches template (no extra platform flags, same user pattern)
- [ ] `__init__.py` — OTEL setup matches template (LoggerProvider, MeterProvider, TracerProvider)
- [ ] `routes.py` — all original endpoints present, /ops/* endpoints added
- [ ] `charts/values.yaml` — all original env vars present (mapped to new names)
- [ ] Helm templates — identical to template repo
- [ ] Required files — `env.list`, `catalog-info.yaml`, `monitored-paths.txt`, `.actrc`
- [ ] Security — T1_SALT / HMAC validation present if original had it
- [ ] Obfuscation — same fields, same conditions as original
- [ ] Caching — same pattern (3-tier if original had file cache)
- [ ] Output — same JSON structure, same flattening, same field names
