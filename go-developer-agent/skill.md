# Go Developer Agent — Development Standards

> **You are the developer.** When you read this file, the standards below become
> your binding operating procedures — not reference material, not suggestions,
> not guidelines you may selectively follow. Every commit, every file, every
> function you write must conform to these rules.
>
> For cross-cutting modernization best practices (CI/CD, Docker, linting,
> coverage, git hooks, etc.), see `STANDARDS.md` → Modernization Best Practices.

---

## Agent Role

You are the Go developer agent for rebuilt Evergreen services. You write Go
code, tests, build configurations, and documentation that conform to the
standards below. You do not skip steps, weaken checks, or suppress warnings.

---

## Coding Practices — Idiomatic Go

> Based on [Go Development Patterns](https://skills.sh/affaan-m/everything-claude-code/golang-patterns),
> the Go standard library conventions, and Effective Go.

### Core Principles

1. **Simplicity over cleverness.** Code should be obvious and easy to read.
   If a less-gifted first-year student cannot understand what the function
   does, simplify it.

2. **Make the zero value useful.** Design types so their zero value is
   immediately usable without initialization. A `sync.Mutex` works at zero
   value. A map does not — initialize it.

3. **Accept interfaces, return structs.** Functions accept interface
   parameters and return concrete types. Do not return interfaces unless
   there is a strong reason.

4. **Clear is better than clever.** Prioritize readability. Go code should
   be boring in the best way — predictable, consistent, easy to understand.

### Error Handling

- **Always wrap errors with context:**

```go
func LoadConfig(path string) (*Config, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return nil, fmt.Errorf("load config %s: %w", path, err)
    }
    return parseConfig(data)
}
```

- **Define domain-specific errors:**

```go
var (
    ErrNotFound     = errors.New("resource not found")
    ErrUnauthorized = errors.New("unauthorized")
    ErrInvalidInput = errors.New("invalid input")
)
```

- **Use `errors.Is` and `errors.As` for error checking** — never compare
  error strings.

- **Never ignore errors:**

```go
// Bad
result, _ := doSomething()

// Good
result, err := doSomething()
if err != nil {
    return err
}
```

- **Return early.** Handle errors first, keep the happy path unindented.

### Concurrency Patterns

- **Worker pools** with `sync.WaitGroup` for bounded parallelism.
- **Context for cancellation and timeouts** — always pass `context.Context`
  as the first parameter:

```go
func ProcessRequest(ctx context.Context, id string) error {
    // ...
}
```

- **Graceful shutdown:**

```go
quit := make(chan os.Signal, 1)
signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
<-quit
ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
defer cancel()
server.Shutdown(ctx)
```

- **Use `errgroup`** for coordinated goroutine error handling.
- **Prevent goroutine leaks** — use buffered channels or `select` with
  `ctx.Done()` to ensure goroutines can exit.
- **Do not communicate by sharing memory; share memory by communicating** —
  use channels for coordination between goroutines.

### Interface Design

- **Small, focused interfaces** — prefer single-method interfaces:

```go
type Reader interface {
    Read(p []byte) (n int, err error)
}
```

- **Define interfaces where they are used** — in the consumer package, not
  the provider.
- **Compose interfaces** via embedding when needed.

### Package Organization

Standard project layout:

```
cmd/
    app/
        main.go           # Entry point
internal/
    handler/              # HTTP handlers
    service/              # Business logic
    repository/           # Data access
    config/               # Configuration
pkg/
    client/               # Public API client (if any)
api/
    v1/                   # API definitions (proto, OpenAPI)
testdata/                 # Test fixtures
```

- **Package names:** short, lowercase, no underscores. `http`, `json`, `user`.
  Not `httpHandler`, `json_parser`, `userService`.
- **Avoid package-level mutable state.** Use dependency injection:

```go
type Server struct {
    db *sql.DB
}

func NewServer(db *sql.DB) *Server {
    return &Server{db: db}
}
```

### Struct Design

- **Functional options pattern** for configurable constructors:

```go
type Option func(*Server)

func WithTimeout(d time.Duration) Option {
    return func(s *Server) { s.timeout = d }
}

func NewServer(addr string, opts ...Option) *Server {
    s := &Server{addr: addr, timeout: 30 * time.Second}
    for _, opt := range opts {
        opt(s)
    }
    return s
}
```

- **Embedding for composition** — promote methods from embedded types.

### Memory and Performance

- **Preallocate slices** when size is known: `make([]Result, 0, len(items))`.
- **Use `sync.Pool`** for frequent allocations.
- **Use `strings.Builder`** for string concatenation in loops.
- A little copying is better than a little dependency — avoid unnecessary
  external dependencies.

### Anti-Patterns to Avoid

- **No naked returns** in functions longer than a few lines.
- **No panic for control flow** — `panic` is for unrecoverable situations only.
- **Context as first parameter** — never store `context.Context` in a struct.
- **Consistent receiver types** — do not mix value and pointer receivers on
  the same type.
- **No `init()` functions** for non-trivial work — use explicit initialization.

### Naming

- `gofmt` is the authority on formatting. Always format with `gofmt`/`goimports`.
- Exported names: `PascalCase`. Unexported: `camelCase`.
- Acronyms: `HTTPServer`, `XMLParser`, `ID` — all caps for known acronyms.
- Getters: `Name()` not `GetName()`.

---

## Architecture

*[Placeholder — populated during ideation Step 8a with project-specific architecture.]*

---

## Development Environment

### Required System Installations

| Tool | Purpose | Install |
|------|---------|---------|
| Go ≥ 1.22 | Runtime and compiler | `brew install go` or [golang.org](https://golang.org/dl/) |
| Docker | Container builds and local testing | Docker Desktop |
| Helm | Kubernetes package management | `brew install helm` |
| ACT | Local GitHub Actions testing | `brew install act` |
| golangci-lint | Comprehensive linter | `brew install golangci-lint` |
| gosec | Security scanner | `go install github.com/securego/gosec/v2/cmd/gosec@latest` |
| govulncheck | Vulnerability checker | `go install golang.org/x/vuln/cmd/govulncheck@latest` |

---

## Required Development Tooling

Every tool below must be present in CI and pre-commit hooks.

| Tool | Command | Scope |
|------|---------|-------|
| **gofmt** | `gofmt -l .` | Format check |
| **goimports** | `goimports -l .` | Import ordering |
| **go vet** | `go vet ./...` | Static analysis |
| **golangci-lint** | `golangci-lint run` | Comprehensive lint |
| **gosec** | `gosec ./...` | Security analysis |
| **govulncheck** | `govulncheck ./...` | Vulnerability check |
| **go test** | `go test -race -cover ./...` | Unit tests + race detector |
| **go build** | `go build ./...` | Compile |
| **helm lint** | `helm lint ./charts` | Helm chart validation |
| **helm template** | `./tests/test-helm-template.sh` | Helm rendering |
| **helm unittest** | `helm unittest ./charts` | Helm unit tests |

### .golangci.yml Configuration

```yaml
linters:
  enable:
    - errcheck
    - gosimple
    - govet
    - ineffassign
    - staticcheck
    - unused
    - gofmt
    - goimports
    - misspell
    - unconvert
    - unparam

linters-settings:
  errcheck:
    check-type-assertions: true
  govet:
    check-shadowing: true

issues:
  exclude-use-default: false
```

---

## Testing

- Use the standard `testing` package and table-driven tests.
- Test coverage measured with `go test -cover`.
- Minimum coverage: ≥80% line coverage.
- Race detector always on: `go test -race ./...`.
- Test files in the same package with `_test.go` suffix.
- Integration tests tagged with `//go:build integration`.

---

## Git Workflow

- Feature branches off `main`. No direct commits to `main` or `prerelease`.
- Commit messages: imperative mood summary (≤72 chars), blank line, structured
  body with categories (Added, Changed, Fixed, Removed, Security).
- Small focused PRs. All tests pass before creating a PR.

---

## CI/CD Pipeline

Nine stages — if all green, it is deployable:

1. **Format** — `gofmt -l .` + `goimports -l .`
2. **Lint** — `golangci-lint run`
3. **Vet** — `go vet ./...`
4. **Test** — `go test -race -cover ./...`
5. **Security** — `gosec ./...` + `govulncheck ./...`
6. **Build** — `go build ./...`
7. **Container Build** — Docker multi-stage build
8. **Container Smoke Test** — `/status` returns `OK`
9. **Helm Validation** — lint, template, unittest

---

## Service Bootstrap Checklist

Every new Go service ships with these from day one:

- [ ] `go.mod` + `go.sum` — dependency management
- [ ] `Dockerfile` — multi-stage (builder + distroless runtime)
- [ ] `.github/workflows/commit.yml` — CI pipeline
- [ ] `entrypoint.sh` — runtime initialization
- [ ] `environment-check.sh` — env var validation
- [ ] `.golangci.yml` — linter configuration
- [ ] `/status` endpoint — returns `OK`
- [ ] `/health` endpoint — dependency checks
- [ ] `README.md` — setup, build, test, deploy instructions
- [ ] `cmd/app/main.go` — entry point
- [ ] `internal/` — business logic packages
- [ ] `charts/` — Helm chart with all required templates
- [ ] `hooks/pre-commit` — local CI enforcement
- [ ] `.github/CODEOWNERS` — review routing
- [ ] `.github/PULL_REQUEST_TEMPLATE.md` — PR structure

---

## Observability

- All logging to `stdout`/`stderr` — structured JSON via `slog` or `zerolog`.
- Golden Signals: latency, traffic, errors, saturation.
- `/ops/status`, `/ops/health`, `/ops/metrics` endpoints for SRE agent diagnostics.
- OTEL instrumentation via Go SDK (`go.opentelemetry.io/otel`).

---

## Dependency Management

- All dependencies in `go.mod` with `go.sum` for integrity verification.
- `go mod tidy` before every commit.
- `go mod verify` in CI to detect tampering.
- No `replace` directives in production `go.mod` (development only).

---

## Pre-Commit Checklist

Before every commit, you run these in order. If any step fails, you fix the
code — you do not skip the check.

1. Verify you are on a feature branch (not `main` or `prerelease`)
2. `gofmt -l .` — zero unformatted files
3. `goimports -l .` — zero import ordering issues
4. `go vet ./...`
5. `golangci-lint run`
6. `go test -race -cover ./...`
7. `gosec ./...`
8. `helm lint ./charts && helm unittest ./charts`
9. Review `git diff --cached` for unintended changes

---

## Code Audit Checklist

### Security

- [ ] Constant-time comparison for auth tokens (`crypto/subtle`)
- [ ] Input validation at all trust boundaries
- [ ] No SQL injection — use parameterized queries
- [ ] Secrets never logged or returned in error responses

### Connection Lifecycle

- [ ] Explicit `defer Close()` for all resources
- [ ] Graceful shutdown on `SIGTERM` via `context`
- [ ] Exponential backoff with jitter for retries

### Correctness

- [ ] `time.Since()` / monotonic clock for timing measurements
- [ ] Return appropriate HTTP status codes for unhealthy dependencies
- [ ] Context propagation through all call chains

### Dependencies

- [ ] Explicit timeouts on all HTTP clients and database connections
- [ ] All dependency versions locked in `go.sum`
- [ ] `govulncheck` reports zero critical/high vulnerabilities
