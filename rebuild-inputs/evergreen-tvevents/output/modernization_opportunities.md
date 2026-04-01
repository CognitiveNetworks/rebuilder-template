# Modernization Opportunities: evergreen-tvevents

> **Reference document.** This analysis was generated during Step 3 of the ideation process. It informs decisions but does not override python-developer-agent/skill.md.

## Opportunity 1: Replace Flask with FastAPI

**Pain Point:** Flask is a synchronous WSGI framework requiring gevent workers for concurrency. No auto-generated OpenAPI spec, no typed request/response models, no native async support.

**Current State:** Flask 3.1.1 with Gunicorn + gevent. Routes return bare strings ("OK"). No request/response validation beyond manual checks. No OpenAPI documentation.

**Target State:** FastAPI with uvicorn. Auto-generated OpenAPI spec with typed Pydantic models for all request/response shapes. Native async support. Automatic request validation.

**Impact:** High — enables OpenAPI documentation, typed APIs, better performance, and modern Python patterns.

**Risk:** Low — the application has only 2 endpoints (POST `/`, GET `/status`). Migration is straightforward. TV firmware sends JSON payloads that map directly to Pydantic models.

**Evidence:** `app/routes.py` (94 lines) — only 2 route handlers. `app/utils.py` — manual validation logic that Pydantic can replace or complement.

---

## Opportunity 2: Replace Kinesis Data Firehose with Kafka

**Pain Point:** AWS Kinesis Data Firehose creates provider lock-in. Data delivery is via cnlib.firehose.Firehose which wraps boto3. Multiple firehose streams (evergreen, legacy, debug variants) add configuration complexity.

**Current State:** 4 Firehose streams configured via environment variables. Delivery via `cnlib.firehose.Firehose.send_records()`. Parallel delivery via ThreadPoolExecutor.

**Target State:** Kafka topics via `kafka_module.producer.send_message()` from the standalone `rebuilder-evergreen-kafka-python` module. Single producer with topic-based routing.

**Impact:** High — removes AWS Firehose lock-in, simplifies delivery logic, enables replay/reprocessing via Kafka retention.

**Risk:** Low — the standalone kafka_module already exists and is tested. The interface is simpler than the Firehose pattern (topic + payload bytes vs. stream name + records list).

**Evidence:** `app/utils.py:270-317` — `send_to_valid_firehoses()` uses ThreadPoolExecutor to send to multiple Firehose streams. `kafka_module/producer.py` — drop-in replacement with `send_message(topic, payload_bytes, key)`.

---

## Opportunity 3: Replace cnlib Git Submodule with Standalone Modules

**Pain Point:** cnlib is a git submodule (`cntools_py3/cnlib`) that requires `git submodule init/update` and `setup.py install`. It provides 3 functions used by tvevents: Firehose delivery, token hash validation, and logging. The entire cnlib package is installed for 3 functions.

**Current State:** `cnlib.cnlib.firehose.Firehose`, `cnlib.cnlib.token_hash.security_hash_match`, `cnlib.cnlib.log.getLogger` imported from git submodule.

**Target State:**
- `firehose.Firehose` → `kafka_module.producer.send_message()` (already built)
- `token_hash.security_hash_match` → inline HMAC utility in the rebuilt service
- `log.getLogger` → standard Python `logging.getLogger`

**Impact:** High — eliminates the most fragile dependency in the project. Removes git submodule management, `setup.py install`, and the entire cntools_py3 directory.

**Risk:** Low — all 3 replacements are straightforward. The token_hash algorithm must be extracted and verified for correctness.

**Evidence:** `Dockerfile:35` — `COPY ./cntools_py3/cnlib ./cnlib`; `Dockerfile:49-51` — `cd cnlib && python setup.py install`. Only 3 imports from cnlib in all of `app/`.

---

## Opportunity 4: Add Connection Pooling for RDS

**Pain Point:** Each database query opens a new psycopg2 connection and closes it after execution. No connection pooling. At high throughput (hundreds of millions of events/day, up to 500 pods), this creates excessive connection churn.

**Current State:** `dbhelper.py:_connect()` creates a new connection per `_execute()` call. Connection is closed in the `finally` block.

**Target State:** `rds_module.client` from `rebuilder-evergreen-rds-python` provides `ThreadedConnectionPool` with configurable min/max connections, retry logic, and OTEL instrumentation.

**Impact:** Medium — reduces connection overhead, improves query performance, adds retry resilience. The blacklist lookup is infrequent (cached), so the impact is primarily at pod startup and cache miss scenarios.

**Risk:** Low — the standalone rds_module already exists and is tested. It's a direct replacement for `TvEventsRds._connect()` + `_execute()`.

**Evidence:** `rds_module/client.py` — `ThreadedConnectionPool` with retry logic, OTEL spans, and semantic conventions matching the legacy instrumentation.

---

## Opportunity 5: Add /ops/* SRE Diagnostic Endpoints

**Pain Point:** No SRE diagnostic endpoints. Debugging requires kubectl exec or log inspection. No way to query application state, metrics, health status, or cache state via HTTP.

**Current State:** Only `/status` returning bare "OK". No dependency health checks, no metrics endpoint, no cache inspection, no error reporting, no config visibility.

**Target State:** Full SRE contract per template repo standards:
- `/ops/status` — service status with uptime, version, dependency health
- `/ops/health` — deep health check with RDS and Kafka latency
- `/ops/metrics` — Golden Signals (latency p50/p95/p99, traffic, errors, saturation) and RED metrics
- `/ops/config` — runtime configuration (sanitized)
- `/ops/errors` — recent error log
- `/ops/cache` — blacklist cache state and statistics
- `/ops/cache/flush` — flush blacklist cache
- `/ops/cache/refresh` — refresh blacklist from RDS
- `/ops/circuits` — circuit breaker states
- `/ops/loglevel`, `/ops/log-level` — dynamic log level adjustment

**Impact:** High — transforms the service from opaque to observable. Enables SRE agent automation, reduces MTTR.

**Risk:** Low — these are standard endpoints with well-defined contracts. The template repo provides the pattern.

**Evidence:** Legacy assessment — "No /ops/* endpoints" rated as a key gap. Template repo requires all 6 diagnostic + 5 remediation endpoints.

---

## Opportunity 6: Dependency Cleanup

**Pain Point:** 87+ runtime dependencies, many unused. Increases container image size, attack surface, and dependency vulnerability exposure.

**Current State:** `pyproject.toml` lists 87+ runtime dependencies including pymemcache, PyMySQL, redis, fakeredis, google-cloud-monitoring, pygerduty, pyzmq, python-consul, boto (v2), and others never imported in app code.

**Target State:** Lean dependency set: FastAPI, uvicorn, psycopg2-binary (via rds_module), confluent-kafka (via kafka_module), pydantic, opentelemetry SDK, and only the packages actually imported.

**Impact:** High — estimated 60-70% reduction in runtime dependencies. Smaller container image, fewer CVE alerts, faster builds.

**Risk:** Low — unused dependencies are confirmed by grep analysis showing no imports in `app/`.

**Evidence:** Legacy assessment Code & Dependency Health section — 13+ unused packages identified.

---

## Opportunity 7: Python 3.12 Upgrade

**Pain Point:** Python 3.10 is behind LTS. Missing modern type hint features (PEP 695 type aliases, `type` statement), performance improvements (PEP 684 per-interpreter GIL), and security patches.

**Current State:** `python:3.10-bookworm` base image. `.python-version: 3.10`. No type annotations in source code.

**Target State:** Python 3.12 with full type annotations, modern syntax, `python:3.12-slim` base image.

**Impact:** Medium — better performance, smaller base image (slim vs full), type safety, modern language features.

**Risk:** Low — no Python 3.10-specific features are used. All dependencies have 3.12 wheels.

---

## Opportunity 8: Local Development Stack (docker-compose)

**Pain Point:** No way to run the full application locally without manual setup of RDS, Firehose, and AWS credentials. The README describes a 7-step minikube process.

**Current State:** Local development requires: Docker build → manual env var injection → minikube setup → helm install → port forward. No docker-compose.

**Target State:** `docker compose up --build` starts the entire stack: app, PostgreSQL, Kafka (replacing Firehose), with seed data and health checks. Standalone rds_module and kafka_module mounted as local paths.

**Impact:** High — dramatically reduces time-to-first-request for new developers. Enables integration testing locally.

**Risk:** Low — standard Docker Compose pattern. PostgreSQL and Kafka have well-maintained official images.

**Evidence:** README.md "Running Minikube locally" — 7-step manual process. No docker-compose.yml exists.

---

## Opportunity 9: Structured Error Handling

**Pain Point:** Broad `except Exception as catchall_exception` pattern in routes. Custom exceptions all use status code 400. Nested exception wrapping: `raise TvEventsCatchallException(TvEventsCatchallException(msg))`.

**Current State:** 5 custom exception classes all inheriting from `TvEventsDefaultException(Exception)` with hardcoded `status_code = 400`. Error handler returns `jsonify(error=type, message=msg)`.

**Target State:** FastAPI exception handlers with Pydantic error response models. HTTP status codes appropriate to error type (400 for validation, 401 for auth, 500 for internal). Structured error logging with correlation IDs.

**Impact:** Medium — better API consumer experience, clearer error diagnostics.

**Risk:** Low — FastAPI has built-in exception handling and HTTP exception classes.

---

## Opportunity 10: Separate Business Logic from I/O

**Pain Point:** `utils.py` (418 lines) combines pure business logic (validation, flattening, obfuscation) with I/O operations (Firehose delivery, RDS queries). Makes testing difficult and violates single responsibility.

**Current State:** All business logic and I/O in one module. Module-level state (`TVEVENTS_RDS`, `VALID_TVEVENTS_FIREHOSES`, `SALT_KEY`) instantiated at import time.

**Target State:** Separate modules:
- `validation.py` — request validation, parameter checks, timestamp validation
- `security.py` — HMAC hash validation (replaces cnlib.token_hash)
- `event_types.py` — event classification and type-specific validation
- `output.py` — JSON flattening, output generation
- `obfuscation.py` — blacklist lookup, channel obfuscation
- `delivery.py` — Kafka delivery (wraps kafka_module)

**Impact:** Medium — cleaner architecture, easier testing, clear dependency boundaries.

**Risk:** Low — pure refactoring of existing logic into separate modules.

---

## Priority Summary

| # | Opportunity | Impact | Risk | Priority |
|---|---|---|---|---|
| 1 | Flask → FastAPI | High | Low | **P0** |
| 2 | Firehose → Kafka | High | Low | **P0** |
| 3 | cnlib → Standalone modules | High | Low | **P0** |
| 4 | Add RDS connection pooling | Medium | Low | **P1** |
| 5 | Add /ops/* endpoints | High | Low | **P0** |
| 6 | Dependency cleanup | High | Low | **P0** |
| 7 | Python 3.12 upgrade | Medium | Low | **P1** |
| 8 | docker-compose local stack | High | Low | **P0** |
| 9 | Structured error handling | Medium | Low | **P1** |
| 10 | Separate business logic from I/O | Medium | Low | **P1** |
