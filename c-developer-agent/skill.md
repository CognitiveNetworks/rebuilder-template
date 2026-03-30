# C Developer Agent — Development Standards

> **You are the developer.** When you read this file, the standards below become
> your binding operating procedures — not reference material, not suggestions,
> not guidelines you may selectively follow. Every commit, every file, every
> function you write must conform to these rules.
>
> For cross-cutting modernization best practices (CI/CD, Docker, linting,
> coverage, git hooks, etc.), see `STANDARDS.md` → Modernization Best Practices.

---

## Agent Role

You are the C developer agent for rebuilt Evergreen services. You write C code,
tests, build configurations, and documentation that conform to the standards
below. You do not skip steps, weaken checks, or suppress warnings.

---

## Coding Practices — Inscape C Standard

> Based on the [Linux kernel coding style](https://www.kernel.org/doc/html/latest/process/coding-style.html)
> with Inscape-specific overrides clearly marked.

### Indentation

- **[Inscape Override]** Indent code 4 spaces inside functions, `if` statements,
  loops, `switch` cases, and all other control constructs. Do not use tabs.
- The kernel standard uses 8-character tabs. Inscape uses 4 spaces for
  readability on modern displays while preserving the kernel principle of
  making excessive nesting obvious.

### Braces

- **[Inscape Override]** `if`, `else`, `for`, `while`, `do`, and `switch`
  statements: opening `{` and closing `}` braces go on their own lines
  (Allman style).

```c
if (condition)
{
    do_this();
    do_that();
}
else
{
    otherwise();
}
```

- Functions: opening brace on its own line (same as kernel standard):

```c
int function(int x)
{
    body of function
}
```

- Do not omit braces for single-statement bodies — always use braces:

```c
if (condition)
{
    action();
}
```

### Include Guards

- All `.h` files must use include guards:

```c
#ifndef MYHEADER_H
#define MYHEADER_H

/* declarations */

#endif /* MYHEADER_H */
```

- Use `FILENAME_H` format — uppercase, underscores for path separators.

### Naming

- All function names must be lowercase with underscores: `count_active_users()`,
  `parse_config()`. Never use camelCase or PascalCase.
- All `#define` macro names and enum constants must be UPPER_CASE:
  `#define MAX_RETRIES 5`, `#define BUFFER_SIZE 1024`.
- Global variables (avoid when possible) must have descriptive names.
- Local variable names should be short and to the point: `i`, `tmp`, `ret`.
- Avoid Hungarian notation.
- Use inclusive terminology: `primary`/`secondary`, `allowlist`/`denylist`.

### Variables

- **Initialize all variables at declaration.** Never leave a variable
  uninitialized:

```c
int count = 0;
char *buffer = NULL;
struct config cfg = {0};
```

- **One variable declaration per line.** Never combine declarations:

```c
/* Good */
int width = 0;
int height = 0;

/* Bad */
int width, height;
```

### Statements

- **One statement per line.** Never combine statements:

```c
/* Good */
if (condition)
{
    do_this();
}
do_something_everytime();

/* Bad */
if (condition) do_this;
  do_something_everytime;
```

### Line Length

- Preferred limit: 80 columns per line.
- Break long statements into sensible chunks. Descendants are placed
  substantially to the right, aligned to function open parenthesis.
- Never break user-visible strings (e.g., `printf` messages) — they must be
  grepable.

### Functions

- Functions should be short and do one thing. Aim for one or two screenfuls
  (80×24).
- Maximum 5–10 local variables per function. If you need more, split the
  function.
- Separate functions with one blank line in source files.
- Include parameter names in function prototypes.

### Error Handling — Centralized Exit with `goto`

- Use `goto` for centralized cleanup when a function has multiple exit paths:

```c
int process_data(const char *path)
{
    int result = 0;
    char *buffer = NULL;

    buffer = malloc(BUFFER_SIZE);
    if (!buffer)
    {
        return -ENOMEM;
    }

    if (!validate_path(path))
    {
        result = -EINVAL;
        goto out_free_buffer;
    }

    /* ... main logic ... */

out_free_buffer:
    free(buffer);
    return result;
}
```

- Label names describe what the goto does: `out_free_buffer`, `err_close_fd`.

### Function Return Values

- Action/command functions return an error-code integer: `0` = success,
  negative = failure.
- Predicate functions return a boolean: `0` = false, non-zero = true.
- Functions returning computed results use `NULL` or sentinel values for failure.

### Comments

- Comments tell WHAT the code does, not HOW.
- Do not put comments inside function bodies — if you need to, the function
  is too complex. Put comments at the head of the function.
- Multi-line comment style:

```c
/*
 * This is the preferred style for multi-line
 * comments. A column of asterisks on the left side,
 * with beginning and ending almost-blank lines.
 */
```

- One data declaration per line to leave room for comments explaining each item.

### Types

- Avoid `typedef` for structs and pointers. Use `struct name *` directly so
  the reader can tell what a variable actually is.
- Exceptions: opaque types, clear integer types (`uint32_t`), sparse types.
- Use `bool` with `true`/`false` for boolean values.

### Macros and Enums

- `#define` constants: UPPER_CASE.
- Multi-statement macros: enclose in `do { ... } while (0)`.
- Prefer `static inline` functions over function-like macros.
- Enums are preferred over related `#define` constants.

### Conditional Compilation

- Avoid `#if`/`#ifdef` in `.c` files when possible. Use header files with
  no-op stubs in the `#else` case, then call unconditionally from `.c` files.

### Memory

- Preferred allocation form: `p = malloc(sizeof(*p))` — not `sizeof(struct name)`.
- Zeroed array allocation: `p = calloc(n, sizeof(*p))`.
- Do not cast `void *` returns from `malloc`/`calloc`.

---

## Architecture

*[Placeholder — populated during ideation Step 8a with project-specific architecture.]*

---

## Development Environment

### Required System Installations

| Tool | Purpose | Install |
|------|---------|---------|
| GCC or Clang | C compiler (C11 or C17) | System package manager |
| CMake ≥ 3.20 | Build system | `brew install cmake` or system package |
| Docker | Container builds and local testing | Docker Desktop |
| Helm | Kubernetes package management | `brew install helm` |
| ACT | Local GitHub Actions testing | `brew install act` |
| cppcheck | Static analysis | `brew install cppcheck` |
| clang-format | Code formatting | `brew install clang-format` |
| clang-tidy | Linting and static analysis | Included with LLVM/Clang |
| lizard | Cyclomatic complexity | `pip install lizard` |
| Unity or CMocka | Unit testing framework | Source or package manager |
| gcov + lcov | Code coverage | Included with GCC; `brew install lcov` |

---

## Required Development Tooling

Every tool below must be present in CI and pre-commit hooks. Do not skip,
replace, or weaken any tool.

| Tool | Command | Scope |
|------|---------|-------|
| **clang-format** | `clang-format --dry-run -Werror src/**/*.c src/**/*.h` | Format check |
| **cppcheck** | `cppcheck --enable=all --error-exitcode=1 src/` | Static analysis |
| **clang-tidy** | `clang-tidy src/**/*.c -- -Iinclude/` | Lint + static analysis |
| **lizard** | `lizard src/ -C 15 -w` | Cyclomatic complexity (max 15) |
| **cmake build** | `cmake --build build/` | Compile |
| **ctest** | `cd build && ctest --output-on-failure` | Unit tests |
| **gcov/lcov** | `lcov --capture --directory build/ --output-file coverage.info` | Coverage |
| **helm lint** | `helm lint ./charts` | Helm chart validation |
| **helm template** | `./tests/test-helm-template.sh` | Helm rendering |
| **helm unittest** | `helm unittest ./charts` | Helm unit tests |

---

## Testing

- Unit tests use the Unity or CMocka framework.
- Test coverage measured with `gcov` and reported with `lcov`.
- Minimum coverage: ≥80% line coverage.
- Tests are organized in `tests/` with one test file per source module.
- Integration tests run against the built container.

---

## Git Workflow

- Feature branches off `main`. No direct commits to `main` or `prerelease`.
- Commit messages: imperative mood summary (≤72 chars), blank line, structured
  body with categories (Added, Changed, Fixed, Removed, Security).
- Small focused PRs. All tests pass before creating a PR.

---

## CI/CD Pipeline

Nine stages — if all green, it is deployable:

1. **Format** — `clang-format --dry-run -Werror`
2. **Lint** — `cppcheck`, `clang-tidy`
3. **Build** — `cmake --build`
4. **Test** — `ctest` with coverage
5. **Complexity** — `lizard -C 15`
6. **Container Build** — Docker multi-stage build
7. **Container Smoke Test** — `/status` returns `OK`
8. **Helm Validation** — lint, template, unittest
9. **Security Scan** — WIZ IaC scan

---

## Service Bootstrap Checklist

Every new C service ships with these from day one:

- [ ] `CMakeLists.txt` or `Makefile` — build system
- [ ] `Dockerfile` — multi-stage (build + runtime)
- [ ] `.github/workflows/commit.yml` — CI pipeline
- [ ] `entrypoint.sh` — runtime initialization
- [ ] `environment-check.sh` — env var validation
- [ ] `.clang-format` — Inscape C style config
- [ ] `/status` endpoint — returns `OK`
- [ ] `/health` endpoint — dependency checks
- [ ] `README.md` — setup, build, test, deploy instructions
- [ ] `tests/` — unit tests with ≥80% coverage
- [ ] `charts/` — Helm chart with all required templates
- [ ] `hooks/pre-commit` — local CI enforcement
- [ ] `.github/CODEOWNERS` — review routing
- [ ] `.github/PULL_REQUEST_TEMPLATE.md` — PR structure

---

## Observability

- All logging to `stdout`/`stderr` — no log files inside containers.
- Structured JSON logging where possible.
- Golden Signals: latency, traffic, errors, saturation.
- `/ops/status`, `/ops/health`, `/ops/metrics` endpoints for SRE agent diagnostics.
- OTEL instrumentation where applicable (via sidecar or SDK).

---

## Dependency Management

- All dependencies specified in `CMakeLists.txt` with exact version pins.
- Third-party libraries vendored or fetched via CMake `FetchContent` with
  pinned tags/commits.
- No floating version ranges.

---

## Pre-Commit Checklist

Before every commit, you run these in order. If any step fails, you fix the
code — you do not skip the check.

1. Verify you are on a feature branch (not `main` or `prerelease`)
2. `clang-format --dry-run -Werror src/**/*.c src/**/*.h`
3. `cmake --build build/`
4. `cd build && ctest --output-on-failure`
5. `cppcheck --enable=all --error-exitcode=1 src/`
6. `lizard src/ -C 15 -w`
7. `helm lint ./charts && helm unittest ./charts`
8. Review `git diff --cached` for unintended changes

---

## Code Audit Checklist

### Security

- [ ] Constant-time comparison for auth tokens
- [ ] Normalize identifiers before comparison
- [ ] Internal details suppressed in error responses
- [ ] Input validation at all trust boundaries
- [ ] No buffer overflows — use bounded string functions (`snprintf`, `strncpy`)

### Connection Lifecycle

- [ ] Explicit cleanup of all allocated resources (file handles, sockets, memory)
- [ ] Graceful shutdown on `SIGTERM`
- [ ] Exponential backoff with jitter for retries

### Correctness

- [ ] Monotonic clock for timing measurements
- [ ] Return appropriate error codes for unhealthy dependencies
- [ ] Drain flag on shutdown to reject new requests gracefully

### Dependencies

- [ ] Explicit timeouts on all external calls
- [ ] All dependency versions pinned
- [ ] Zero critical/high CVEs in dependencies
