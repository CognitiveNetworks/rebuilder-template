---
description: Activate the QA agent to independently verify the developer agent's work
---

# QA Agent Verification Workflow

This workflow activates the QA agent to independently verify that the developer agent's output meets quality standards. The QA agent does **not** replace the developer agent — it is a second opinion that checks whether the developer agent followed the standards in `{lang}-developer-agent/skill.md`.

> **Language detection:** Read `scope.md` → Target Language field to determine `{lang}` (python, c, or go). All agent directory references below use `{lang}-developer-agent/` and `{lang}-qa-agent/`.

## Steps

1. Read the QA agent standards and project-specific config:
   - Read `{lang}-qa-agent/skill.md` in full — these are the verification procedures
   - Read `{lang}-qa-agent/config.md` in full — these are the project-specific acceptance criteria
   - Read `{lang}-developer-agent/skill.md` in full — these are the standards being verified
   - Read `{lang}-developer-agent/config.md` in full — these are the project-specific settings

2. After reading all four files, confirm by stating: **"QA Agent activated for [project-name]. Verifying developer agent compliance."**

3. Run all core quality gates independently (do not rely on any prior TEST_RESULTS.md):

// turbo
   ```
   pytest tests/ --cov=app --cov-fail-under=80 -v --tb=short
   ```

// turbo
   ```
   pylint --disable=import-error --fail-under=10.0 app tests
   ```

// turbo
   ```
   black --check app tests --skip-string-normalization
   ```

// turbo
   ```
   mypy app/ --ignore-missing-imports --disable-error-code=unused-ignore
   ```

4. Run extended quality gates:

// turbo
   ```
   vulture app/ --min-confidence 80
   ```

// turbo
   ```
   pip-audit
   ```

// turbo
   ```
   interrogate app/ -v
   ```

// turbo
   ```
   pylint --disable=all --enable=duplicate-code app/
   ```

// turbo
   ```
   complexipy app -mx 15
   ```

5. Run container gates (for deployable services only):

   a. Build the container image:
   ```
   docker build -t {service}:ci .
   ```

   b. Isolation smoke test (TEST_CONTAINER=true):
   ```
   docker run -d -p 8000:8000 -e TEST_CONTAINER=true -e ENV=dev -e AWS_REGION=us-east-1 -e SERVICE_NAME=local-testing -e LOG_LEVEL=DEBUG -e OTEL_PYTHON_AUTO_INSTRUMENTATION_ENABLED=false --name {service}-ci {service}:ci
   sleep 10
   curl --silent --fail http://localhost:8000/status
   docker stop {service}-ci && docker rm {service}-ci
   ```

   c. Docker Compose full-stack smoke test (if `docker-compose.yml` exists):
   ```
   docker compose up --build -d
   # Wait for app health (up to 90s)
   timeout 90 bash -c 'until docker compose ps app | grep -q "(healthy)"; do sleep 5; done'
   docker compose ps
   curl --silent --fail http://localhost:8000/status
   curl --silent --fail http://localhost:8000/health
   curl --silent --fail http://localhost:8000/ops/status
   curl --silent --fail http://localhost:8000/ops/health
   curl --silent --fail http://localhost:8000/ops/config
   curl --silent --fail http://localhost:8000/ops/metrics
   docker compose down -v
   ```

   If Docker is unavailable, mark container gates as `NOT RUN — Docker unavailable` (advisory).

   d. CI pipeline verification via `act` (requires Docker):

   Run each CI job locally using `act` to verify the GitHub Actions workflow executes
   correctly — not just the individual tools, but the full pipeline definition. This
   catches wrong paths in workflow YAML, missing env vars in CI context, and job
   configuration errors that individual tool runs cannot detect.

   `.actrc` must exist with `--container-architecture linux/amd64`.

// turbo
   ```
   act -j black --env-file env.list
   ```

// turbo
   ```
   act -j pytest --env-file env.list
   ```

// turbo
   ```
   act -j pylint --env-file env.list
   ```

// turbo
   ```
   act -j complexipy --env-file env.list
   ```

// turbo
   ```
   act -j mypy --env-file env.list
   ```

// turbo
   ```
   act -j helm_lint
   ```

   Each `act -j <job>` must exit 0. If a job fails via `act` but the equivalent
   standalone command passed (e.g., `pylint` passed in step 3 but `act -j pylint`
   fails), the CI workflow definition has a bug — fix the workflow YAML, not the tool.

   If `act` is not installed, install it (`brew install act` on macOS). Both `act` and Docker
   are required — CI pipeline gates are merge-blocking, not advisory.

6. Verify `/ops/*` endpoint contract per `{lang}-qa-agent/skill.md` — check that every required diagnostic and remediation endpoint exists and returns the required fields. Use the API Endpoints to Verify table in `{lang}-qa-agent/config.md`.

7. Verify template conformance:
   - `entrypoint.sh` matches template pattern
   - `environment-check.sh` accounts for all original env vars (use the mapping in `{lang}-qa-agent/config.md`)
   - `Dockerfile` matches template (no extra platform flags, correct base image)
   - Helm chart templates match template repo
   - Required files present: `env.list`, `catalog-info.yaml`, `monitored-paths.txt`, `.actrc`
   - `.windsurfrules` and `.github/copilot-instructions.md` exist at built repo root
   - `{lang}-developer-agent/skill.md` and `{lang}-developer-agent/config.md` exist in built repo with placeholders filled
   - `template/skill.md` exists in built repo — open it, walk every checkbox, and confirm each is satisfied by the built code. Mark any N/A items with a justification. This is the authoritative build standard checklist.

8. Compare results against the developer agent's `tests/TEST_RESULTS.md` (if it exists). Flag any discrepancies — coverage numbers that don't match, gates that were claimed as passing but now fail, etc.

9. Generate a QA verification report using the template at `{lang}-qa-agent/TEST_RESULTS_TEMPLATE.md`. Write it to `tests/TEST_RESULTS.md` (replacing the developer agent's version with the QA agent's independently verified version).

10. Summarize findings:
   - **Passed** — gates that pass and match the developer agent's claims
   - **Discrepancies** — gates where the QA agent's result differs from the developer agent's claim
   - **Critical gaps** — missing endpoints, missing files, broken compliance items
   - **Recommendations** — items for human review
