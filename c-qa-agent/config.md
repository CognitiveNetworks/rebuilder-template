# C QA Agent — Project Configuration

> This file contains project-specific QA values. Populated during ideation
> Step 8d or manually for new projects.

---

## Project

| Field | Value |
|-------|-------|
| **Name** | *[TODO: project name]* |
| **Repository** | *[TODO: repo URL]* |
| **Language** | C (C11 / C17) |
| **Build System** | CMake ≥ 3.20 |
| **Original Legacy Repo** | *[TODO: legacy repo URL]* |

---

## Test Commands

| Tool | Command | Gate |
|------|---------|------|
| **clang-format** | `clang-format --dry-run -Werror src/**/*.c src/**/*.h` | Format |
| **cppcheck** | `cppcheck --enable=all --error-exitcode=1 src/` | Static analysis |
| **clang-tidy** | `clang-tidy src/**/*.c -- -Iinclude/` | Lint |
| **cmake build** | `cmake --build build/` | Build |
| **ctest** | `cd build && ctest --output-on-failure` | Unit test |
| **lcov** | `lcov --capture --directory build/ --output-file coverage.info` | Coverage |
| **lizard** | `lizard src/ -C 15 -w` | Complexity |
| **helm lint** | `helm lint ./charts` | Helm |
| **helm template** | `./tests/test-helm-template.sh` | Helm |
| **helm unittest** | `helm unittest ./charts` | Helm |

---

## Quality Gate Thresholds

| Gate | Threshold | Blocking Stage |
|------|-----------|----------------|
| clang-format | Zero violations | Merge |
| cppcheck | Zero errors | Merge |
| clang-tidy | Zero warnings | Merge |
| Build | Compiles clean | Merge |
| ctest | All pass | Merge |
| Coverage | ≥80% | Merge |
| lizard | CCN ≤ 15 | Release |
| Container build | Succeeds | Release |
| Container smoke | `/status` → `OK` | Release |
| Helm lint | No errors | Release |

---

## Test Environments

| Environment | Dependencies | Purpose |
|-------------|-------------|---------|
| **Local** | Mocked | Developer iteration |
| **CI** | Mocked | PR validation |
| **Dev** | Real (deployed) | Integration verification |
| **Staging** | Real (deployed) | Pre-production validation |

---

## Required Test Environment Variables

| Variable | Test Default | Purpose |
|----------|-------------|---------|
| `ENV` | `dev` | Environment name |
| `LOG_LEVEL` | `DEBUG` | Logging verbosity |
| `TEST_CONTAINER` | `true` | Skip external deps in smoke test |
| `SERVICE_NAME` | `local-testing` | OTEL service identifier |

---

## Acceptance Criteria — App-Specific

### API Endpoints to Verify

| Method | Path | Expected Status |
|--------|------|----------------|
| GET | `/status` | 200 — `OK` |
| GET | `/health` | 200 — composite health |
| *[TODO]* | *[TODO]* | *[TODO]* |

### Environment Variable Mapping

| Original (Legacy) | Rebuilt | Notes |
|-------------------|---------|-------|
| *[TODO]* | *[TODO]* | *[TODO]* |
