# C QA Agent — Quality Verification Standards

> You verify the C developer agent's output. The developer agent writes code,
> tests, configs, and documentation per `c-developer-agent/skill.md`. You
> independently verify that every standard was met. You do not trust that it
> was done — you check.
>
> For development standards (the rules being verified), see `c-developer-agent/skill.md`.
> For cross-cutting modernization practices, see `STANDARDS.md`.

---

## Agent Role

You are the C QA verification agent. You independently verify that the
developer agent's output meets quality standards. You do **not** replace the
developer agent — you are a check on it.

---

## Test Strategy

### Level 1 — Unit Tests

- ≥80% line coverage measured by `gcov`/`lcov`
- Mock all external dependencies
- One test file per source module in `tests/`
- Framework: Unity or CMocka

### Level 2 — Integration Tests

- Component interactions end-to-end
- Test against built container with `docker run`
- Verify `/status` and `/health` endpoints

### Level 3 — Contract Tests

- API responses match expected schemas
- `/ops/*` endpoint contract verification

---

## Quality Gates

All gates must pass before merge. Failures block the PR.

### Core Gates (Block Merge)

| Gate | Tool | Command | Pass Criteria |
|------|------|---------|---------------|
| **Format** | clang-format | `clang-format --dry-run -Werror src/**/*.c src/**/*.h` | Zero formatting violations |
| **Static Analysis** | cppcheck | `cppcheck --enable=all --error-exitcode=1 src/` | Zero errors |
| **Lint** | clang-tidy | `clang-tidy src/**/*.c -- -Iinclude/` | Zero warnings |
| **Build** | CMake | `cmake --build build/` | Compiles without errors or warnings |
| **Test** | ctest | `cd build && ctest --output-on-failure` | All tests pass |
| **Coverage** | gcov/lcov | `lcov --capture ...` | ≥80% line coverage |

### Extended Gates (Block Release)

| Gate | Tool | Command | Pass Criteria |
|------|------|---------|---------------|
| **Complexity** | lizard | `lizard src/ -C 15 -w` | No function exceeds CCN 15 |
| **Container Build** | Docker | `docker build -t <service>:latest .` | Builds without errors |
| **Container Smoke** | curl | `curl http://localhost:8000/status` | Returns `OK` |
| **Helm Lint** | Helm | `helm lint ./charts` | No errors |
| **Helm Template** | Helm | `./tests/test-helm-template.sh` | Renders for all envs |
| **Helm Unittest** | Helm | `helm unittest ./charts` | All tests pass |

---

## `/ops/*` Endpoint Verification

### Diagnostic Endpoints

| Endpoint | Method | Expected |
|----------|--------|----------|
| `/ops/status` | GET | `{"status": "ok"}` |
| `/ops/health` | GET | Composite dependency health |
| `/ops/metrics` | GET | Golden Signals snapshot |
| `/ops/config` | GET | Non-secret runtime config |
| `/ops/errors` | GET | Recent error summary |

### Remediation Endpoints

| Endpoint | Method | Expected |
|----------|--------|----------|
| `/ops/loglevel` | PUT | Change log level at runtime |
| `/ops/cache/flush` | POST | Flush application cache |

---

## Acceptance Criteria Framework

### Functional Parity

- Every user-facing feature from the legacy service is replicated or
  intentionally dropped with justification.

### Infrastructure Parity

- Container builds and runs
- Helm chart deploys to all environments
- Environment variables validated at startup

### Coding Standards Verification

- Every item in `c-developer-agent/skill.md` is verified as implemented
- Inscape C standard enforced: 4-space indent, Allman braces, include guards,
  lowercase functions, UPPER_CASE defines, initialized variables, one
  statement per line, one variable per line

### Template Conformance

- Every section of the template `skill.md` is verified for compliance
