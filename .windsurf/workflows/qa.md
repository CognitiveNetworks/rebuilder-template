---
description: Activate the QA agent to independently verify the developer agent's work
---

# QA Agent Verification Workflow

This workflow activates the QA agent to independently verify that the developer agent's output meets quality standards. The QA agent does **not** replace the developer agent — it is a second opinion that checks whether the developer agent followed the standards in `developer-agent/skill.md`.

## Steps

1. Read the QA agent standards and project-specific config:
   - Read `qa-agent/skill.md` in full — these are the verification procedures
   - Read `qa-agent/config.md` in full — these are the project-specific acceptance criteria
   - Read `developer-agent/skill.md` in full — these are the standards being verified
   - Read `developer-agent/config.md` in full — these are the project-specific settings

2. After reading all four files, confirm by stating: **"QA Agent activated for [project-name]. Verifying developer agent compliance."**

3. Run all core quality gates independently (do not rely on any prior TEST_RESULTS.md):

// turbo
   ```
   pytest tests/ --cov=src/app --cov-fail-under=80 -v --tb=short
   ```

// turbo
   ```
   pylint src tests
   ```

// turbo
   ```
   black --check src/ tests/
   ```

// turbo
   ```
   mypy src/app/
   ```

4. Run extended quality gates:

// turbo
   ```
   radon cc src/ -a -nc
   ```

// turbo
   ```
   radon mi src/
   ```

// turbo
   ```
   vulture src/ --min-confidence 80
   ```

// turbo
   ```
   pip-audit
   ```

// turbo
   ```
   interrogate src/ -v
   ```

// turbo
   ```
   pylint --disable=all --enable=duplicate-code src/
   ```

// turbo
   ```
   complexipy src -mx 15 -d low
   ```

5. Verify `/ops/*` endpoint contract per `qa-agent/skill.md` — check that every required diagnostic and remediation endpoint exists and returns the required fields. Use the API Endpoints to Verify table in `qa-agent/config.md`.

6. Verify template conformance:
   - `entrypoint.sh` matches template pattern
   - `environment-check.sh` accounts for all original env vars (use the mapping in `qa-agent/config.md`)
   - `Dockerfile` matches template (no extra platform flags, correct base image)
   - Helm chart templates match template repo
   - Required files present: `env.list`, `catalog-info.yaml`, `monitored-paths.txt`, `.actrc`
   - `.windsurfrules` and `.github/copilot-instructions.md` exist at built repo root
   - `developer-agent/skill.md` and `developer-agent/config.md` exist in built repo with placeholders filled

7. Compare results against the developer agent's `tests/TEST_RESULTS.md` (if it exists). Flag any discrepancies — coverage numbers that don't match, gates that were claimed as passing but now fail, etc.

8. Generate a QA verification report using the template at `qa-agent/TEST_RESULTS_TEMPLATE.md`. Write it to `tests/TEST_RESULTS.md` (replacing the developer agent's version with the QA agent's independently verified version).

9. Summarize findings:
   - **Passed** — gates that pass and match the developer agent's claims
   - **Discrepancies** — gates where the QA agent's result differs from the developer agent's claim
   - **Critical gaps** — missing endpoints, missing files, broken compliance items
   - **Recommendations** — items for human review
