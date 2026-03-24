# TEST_RESULTS.md — [SERVICE_NAME] Quality Gate Report

**Generated:** [DATE]
**Build Phase:** Step 12 — QA Agent Standards Compliance Audit

---

## Tool Versions

| Tool         | Version   |
|--------------|-----------|
| Python       | 3.12.x    |
| pytest       | 8.x.x    |
| ruff         | 0.x.x    |
| mypy         | x.x.x    |
| radon        | x.x.x    |
| vulture      | x.x      |
| pip-audit    | x.x.x    |
| interrogate  | x.x.x    |
| pylint       | x.x.x    |

## Codebase Metrics

| Metric           | Count |
|------------------|-------|
| Source files      | X     |
| Source lines      | X     |
| Test files        | X     |
| Test lines        | X     |
| Source:Test ratio | X:1   |

---

## Core Gates

### 1. pytest — [PASS ✅ / FAIL ❌]

```
[paste pytest output summary]
```

Coverage: **XX%** (threshold: 80%)

| Module            | Stmts | Miss | Cover |
|-------------------|-------|------|-------|
| `__init__.py`     | X     | X    | X%    |
| `routes.py`       | X     | X    | X%    |
| [add rows]        |       |      |       |
| **TOTAL**         | X     | X    | **X%** |

**Coverage gaps explained:**
- [module] (X%): [explanation of why coverage is below average — e.g., requires live infrastructure]

No module with testable logic is below 50%.

### 2. Linter (ruff check) — [PASS ✅ / FAIL ❌]

```
$ ruff check src/ tests/
[paste output]
```

### 3. Formatter (black) — [PASS ✅ / FAIL ❌]

```
$ black --check src/ tests/
[paste output]
```

### 4. Type Checker (mypy) — [PASS ✅ / FAIL ❌]

```
$ mypy src/app/
[paste output]
```

---

## Extended Gates

### 5. Cyclomatic Complexity (radon cc) — [PASS ✅ / FAIL ❌]

```
[paste radon cc summary]
```

No function rated C or higher. Highest-rated functions (B):
- [function_name] — B(X): [brief explanation]

### 6. Maintainability Index (radon mi) — [PASS ✅ / FAIL ❌]

| File              | Rating | Score  |
|-------------------|--------|--------|
| [file.py]         | A      | XX.XX  |

All files rated A. No refactoring required.

### 7. Dead Code (vulture) — [PASS ✅ / FAIL ❌]

```
$ vulture src/ --min-confidence 80
[paste output or "(no output — 0 findings)"]
```

### 8. Dependency Vulnerabilities (pip-audit) — [PASS ✅ / FAIL ❌ / ADVISORY ⚠️]

```
[paste pip-audit output]
```

**Assessment:** [Explain findings — are they runtime or dev-only? Action needed?]

### 9. Docstring Coverage (interrogate) — [PASS ✅ / FAIL ❌]

```
$ interrogate src/ -v
[paste output]
```

### 10. Duplicate Code (pylint) — [PASS ✅ / FAIL ❌]

```
$ pylint --disable=all --enable=duplicate-code src/
[paste output]
```

### 11. Cognitive Complexity (ruff C901) — [PASS ✅ / FAIL ❌]

```
$ ruff check src/ --select C901
[paste output]
```

---

## Helm Gates

### 12. Helm Lint — [PASS ✅ / FAIL ❌]

```
$ helm lint charts/
[paste output]
```

### 13. Helm Template Render — [PASS ✅ / FAIL ❌]

```
$ tests/test-helm-template.sh -all
[paste summary — renders for dev, qa, prod]
```

---

## Quality Gate Summary

| Gate                    | Threshold         | Result                | Status |
|-------------------------|-------------------|-----------------------|--------|
| pytest                  | 0 failures        | X passed, 0 failed    | [✅/❌] |
| Test coverage           | ≥ 80%             | XX%                   | [✅/❌] |
| ruff check (lint)       | 0 errors          | X errors              | [✅/❌] |
| black                   | All formatted     | X/X formatted         | [✅/❌] |
| mypy (types)            | 0 errors          | X errors              | [✅/❌] |
| Cyclomatic complexity   | Average A or B    | X (X.XX)              | [✅/❌] |
| Maintainability index   | All files A or B  | [All A / mixed]       | [✅/❌] |
| Dead code (vulture)     | 0 findings        | X findings            | [✅/❌] |
| Dependency vulns        | 0 runtime CVEs    | X runtime, X dev-only | [✅/❌] |
| Docstring coverage      | ≥ 80%             | XX%                   | [✅/❌] |
| Duplicate code          | < 3%              | X%                    | [✅/❌] |
| Cognitive complexity    | 0 issues (C901)   | X issues              | [✅/❌] |
| Helm lint               | 0 errors          | X errors              | [✅/❌] |
| Helm template render    | dev/qa/prod       | [renders / fails]     | [✅/❌] |

**Overall: X/14 gates PASS**

---

## Bugs Found and Fixed During Validation

| Bug | File | Description | Fix |
|-----|------|-------------|-----|
| [rule id] | [file.py] | [description] | [fix applied] |

## Not Yet Tested

The following require running infrastructure that cannot be validated offline:

- **[Dependency]** — [what cannot be tested and why]
- **Docker container runtime** — `docker build` and `docker compose up` not executed in CI-less environment. Dockerfile validated by inspection.
- **OTEL collector** — Trace/metric/log export to OTEL collector requires running collector. Instrumentation wired in code; export paths not exercised.

## Template Conformance Checklist

- [ ] `entrypoint.sh` matches template pattern
- [ ] `environment-check.sh` extends template correctly
- [ ] `Dockerfile` matches template (no extra flags)
- [ ] Helm chart templates identical to template repo
- [ ] Required files present: `env.list`, `catalog-info.yaml`, `monitored-paths.txt`, `.actrc`
- [ ] `__init__.py` OTEL setup matches template
- [ ] All original env vars accounted for in rebuilt `environment-check.sh`
- [ ] All original env vars mapped in `charts/values.yaml`
