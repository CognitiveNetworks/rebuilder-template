# QA Agent — Evergreen Python Services

> Quality assurance standards for rebuilt Evergreen Python services.
> Activated on demand via the `/qa` Windsurf workflow or during ideation Step 12.
> The QA agent does **not** replace the developer agent — it verifies that the
> developer agent's output meets quality standards. Both agents read from the same
> `python-developer-agent/skill.md` and `python-developer-agent/config.md`; this file adds the
> verification procedures and acceptance criteria that the developer agent is
> checked against.
> For development standards (the rules being verified), see `python-developer-agent/skill.md`.
> For SRE agent configuration, see `sre-agent/skill.md`.

## Agent Role

- **Verification agent**: QA agent verifies developer agent's output — does not replace it
- **Quality enforcement**: Enforces quality gates defined in skill.md and config.md
- **Independent verification**: Runs independently to validate implementation against standards
- **Test strategy owner**: Owns test strategy, quality gates, and acceptance criteria
- **No code modifications**: Does not modify code — only identifies issues and reports them

## Test Strategy

### Test Levels

- **Unit tests**: Fast, isolated, no network or database. Test business logic, transformations, edge cases. Gate every commit
- **API tests**: Every endpoint tested directly — request in, response out. Validate status codes, response shapes, error handling, auth, pagination, edge cases. Primary integration gate
- **Integration tests**: Verify components work together — API endpoints hit database, services call external APIs through mocked boundaries, migrations run cleanly
- **Contract tests**: Validate API responses match OpenAPI spec on every build. If spec and implementation diverge → build fails
- **E2E tests**: Validate critical user workflows against running stack. Keep focused on happy paths and high-value failure modes. Flaky E2E tests → fix or delete, not skip

### Test Organization

- **Test directory structure**: `tests/` at repo root with subdirectories mirroring `app/` structure
- **Test naming**: `test_<module>.py` files with `test_<function>()` methods
- **Fixture organization**: Shared fixtures in `conftest.py` — no duplication across test files
- **Test data**: Domain-realistic values in fixtures — not generic placeholders

## Quality Gates

Run every gate before considering a change complete. Generate a `TEST_RESULTS.md` report (see template in `python-qa-agent/TEST_RESULTS_TEMPLATE.md`) summarizing all results.

### Core Gates (Required — Block Merge)

| # | Gate | Tool | Threshold | Command |
|---|------|------|-----------|---------|
| 1 | Unit + API tests | pytest | 0 failures | `pytest tests/ --cov=app --cov-fail-under=80` |
| 2 | Test coverage | pytest-cov | ≥ 80% line coverage | (included in above) |
| 3 | Lint | pylint | 10.0/10.0 score | `pylint --disable=import-error --fail-under=10.0 app tests` |
| 4 | Format | black | All formatted | `black --check app tests --skip-string-normalization` |
| 5 | Type check | mypy | 0 errors | `mypy app/ --ignore-missing-imports --disable-error-code=unused-ignore` |

### Extended Gates (Required — Block Release)

| # | Gate | Tool | Threshold | Command |
|---|------|------|-----------|---------|
| 6 | Dependency vulns | pip-audit | 0 runtime CVEs | `pip-audit` |
| 7 | Dead code | grep | 0 commented-out defs/classes/imports | `grep -rn "^#.*def \|^#.*class \|^#.*import " app/ tests/` — must be zero |
| 8 | Docstring coverage | interrogate | ≥ 80% | `interrogate app tests -v` |
| 9 | Duplicate code | pylint | < 3% duplication | `pylint --disable=all --enable=duplicate-code app tests` |
| 10 | Cognitive complexity | complexipy | No function ≥ 15 | `complexipy app -mx 15 && complexipy tests -mx 15` |
| 11 | Dependency pinning | scripts/lock.sh | Lock file up-to-date, idempotent | `bash scripts/lock.sh` (run twice, compare MD5 hashes) |

### Helm Gate (Required for deployable services)

| # | Gate | Tool | Threshold | Command |
|---|------|------|-----------|---------|
| 12 | Helm lint | helm | 0 errors | `helm lint charts/` |
| 13 | Helm template render | helm template | Renders for dev, qa, prod | `tests/test-helm-template.sh -all` |
| 14 | Helm unit tests | helm-unittest | 0 failures | `helm unittest ./charts` |

### Container Gate (Required for deployable services)

| # | Gate | Tool | Threshold | Command |
|---|------|------|-----------|---------|
| 15 | Container build | docker build | Exit 0 | `docker build --platform linux/amd64 -t {service}:ci .` |
| 16 | Container isolation smoke test | curl | `/status` returns `OK` | `docker run -d -p 8000:8000 -e TEST_CONTAINER=true -e ENV=dev -e AWS_REGION=us-east-1 -e SERVICE_NAME=local-testing -e LOG_LEVEL=DEBUG -e OTEL_PYTHON_AUTO_INSTRUMENTATION_ENABLED=false --name {service}-ci {service}:ci && sleep 10 && curl --silent --fail http://localhost:8000/status` |
| 17 | Docker Compose full-stack smoke test | docker compose + curl | `/status`, `/health`, `/ops/status` all return 200 | See procedure below |

### CI Pipeline Gate (Required — Block Merge)

| # | Gate | Tool | Threshold | Command |
|---|------|------|-----------|---------|
| 18 | CI black job | act | Exit 0 | `act -j black --env-file env.list` |
| 19 | CI pytest job | act | Exit 0 | `act -j pytest --env-file env.list` |
| 20 | CI pylint job | act | Exit 0 | `act -j pylint --env-file env.list` |
| 21 | CI complexipy job | act | Exit 0 | `act -j complexipy --env-file env.list` |
| 22 | CI mypy job | act | Exit 0 | `act -j mypy --env-file env.list` |
| 23 | CI helm_lint job | act | Exit 0 | `act -j helm_lint` |

## Test Fixture Standards

### conftest.py Requirements

- **Application fixture**: `app` fixture that creates FastAPI app instance for testing
- **Test client fixture**: `client` fixture that provides test client for API tests
- **Database fixture**: `db` fixture that provides test database connection
- **Mock fixtures**: Mock external dependencies (kafka, redis, external APIs)
- **Cleanup fixtures**: Automatic cleanup after each test

### Fixture Patterns

- **Scope**: Use appropriate scope (`function`, `module`, `session`) for performance
- **Dependencies**: Declare fixture dependencies explicitly
- **Yield pattern**: Use yield for setup/teardown, not add_finalizer
- **Naming**: Use descriptive names that indicate fixture purpose

## Acceptance Criteria

### Functional Parity

- **All features implemented**: Every feature from legacy system rebuilt
- **API compatibility**: All legacy APIs supported with compatible responses
- **Data migration**: All data migrated successfully with validation
- **Performance**: Meets or exceeds legacy performance
- **Reliability**: Meets SLO requirements

### Legacy Endpoint Compatibility

- **Response format**: Same response format as legacy
- **Error handling**: Same error codes and messages
- **Authentication**: Same auth mechanisms supported
- **Rate limiting**: Same or better rate limits
- **Deprecation**: Clear deprecation timeline for legacy endpoints

### Infrastructure Parity

- **Environments**: Dev, staging, prod environments provisioned
- **Monitoring**: All monitoring and alerting configured
- **Security**: Security scans and controls in place
- **Backup/Recovery**: Backup and recovery procedures tested
- **Documentation**: All documentation complete and accurate

## Coding Standards Verification

- **Code style**: black formatting passes
- **Linting**: pylint score ≥10.0
- **Type checking**: mypy passes with no errors
- **Complexity**: complexipy within thresholds
- **Security**: No security vulnerabilities
- **Documentation**: All code documented

## Template Conformance

- **Structure**: Follows template structure exactly
- **Files**: All required files present
- **Configuration**: All configuration items defined
- **Scripts**: All scripts executable and tested
- **CI/CD**: Pipeline configured and working

## Quality Standards

- **Test coverage**: ≥80% (≥90% for templates)
- **Test quality**: All tests pass and are meaningful
- **API docs**: OpenAPI spec complete and accurate
- **Monitoring**: All monitoring endpoints working
- **Performance**: Meets performance requirements

## TEST_RESULTS.md Generation

### Required Sections

- **Test Summary**: Overall test results and coverage metrics
- **Quality Gates**: Status of all quality gates (pass/fail)
- **Failed Tests**: Details of any failed tests with error messages
- **Coverage Report**: Line and branch coverage by module
- **Performance Metrics**: Response times and resource usage
- **Security Scan**: Vulnerability scan results
- **Recommendations**: Action items for any failures

### Generation Process

- **Automated generation**: Generate automatically after test runs
- **CI integration**: Include in CI pipeline artifacts
- **PR comments**: Post summary as PR comment
- **Historical tracking**: Track trends over time

## Comparison Workflow

When comparing a rebuilt service against its original, follow this sequence:

1. **Environment variables** — Compare `environment-check.sh` vars. Account for renames (e.g., `RDS_HOST` → `DB_HOST`, `FLASK_ENV` → removed).
2. **OTEL setup** — Compare `__init__.py` instrumentation, `entrypoint.sh` OTEL config, Dockerfile OTEL bootstrap.
3. **Entrypoint and Dockerfile** — Diff against template, then verify app-specific additions.
4. **Routes and validation** — Compare endpoints, params, error codes, response formats.
5. **Business logic** — Compare event types, output generation, obfuscation, caching.
6. **Helm chart values** — Compare env vars, secrets, resources, scaling, probes.
7. **Missing files** — Check for `env.list`, `catalog-info.yaml`, `monitored-paths.txt`, `.actrc`.
8. **Generate report** — Produce a summary of findings with ✅ matches and 🔴 gaps.

## Bug Reporting

When the QA agent finds issues during validation:

- **Fix lint/format/type issues immediately** — these are mechanical, not judgment calls.
- **Report functional gaps as a categorized list** — group by Critical (functional), Important (config/deployment), Minor.
- **Include the exact diff or code snippet** showing what's wrong and what the fix should be.
- **Do not silently fix business logic** — report it and let the developer confirm the fix.
