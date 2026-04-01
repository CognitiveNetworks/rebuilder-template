# Product Requirements Document: rebuilder-evergreen-tvevents

> **Reference document.** This PRD was generated during Step 6 of the ideation process. It informs decisions but does not override python-developer-agent/skill.md.

## 1. Overview

### 1.1 Problem Statement

The evergreen-tvevents (tvevents-k8s) application is a high-throughput TV telemetry collector that receives, validates, transforms, and forwards SmartCast TV event payloads. While functional, it carries significant technical debt: Python 3.10, Flask (synchronous WSGI), a fragile cnlib git submodule, no connection pooling, 87+ runtime dependencies (many unused), no OpenAPI spec, no /ops/* diagnostic endpoints, and no local development stack. These issues increase operational risk, slow developer onboarding, and prevent adoption of modern observability and SRE practices.

### 1.2 Goals

1. Modernize to Python 3.12 with FastAPI for async support, typed APIs, and auto-generated OpenAPI
2. Replace AWS Kinesis Data Firehose with Kafka via standalone `kafka_module`
3. Replace direct psycopg2 with pooled RDS client via standalone `rds_module`
4. Eliminate cnlib git submodule entirely
5. Add full /ops/* SRE diagnostic and remediation endpoints
6. Reduce runtime dependencies from 87+ to ~15-20
7. Enable local development via `docker compose up --build`
8. Achieve ≥80% test coverage with comprehensive quality gates
9. Conform to all template repo standards

### 1.3 Non-Goals

1. Changing the TV firmware payload format (backward compatibility is mandatory)
2. Migrating from AWS to GCP (staying on AWS)
3. Rebuilding downstream analytics pipelines
4. Modifying the RDS schema
5. Replacing HMAC-based TV authentication with a different auth model

### 1.4 Target Repository

`CognitiveNetworks/rebuilder-evergreen-tvevents`

## 2. Technical Approach

### 2.1 Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Language | Python | 3.12 |
| Framework | FastAPI | latest |
| ASGI Server | uvicorn | latest |
| Database Client | rds_module (psycopg2 + ThreadedConnectionPool) | local path |
| Message Broker Client | kafka_module (confluent-kafka) | local path |
| Validation | Pydantic v2 | latest |
| Observability | OpenTelemetry SDK | latest stable |
| Container | Docker (python:3.12-slim base) | — |
| Orchestration | Kubernetes (AWS EKS) | — |
| IaC | Terraform | — |
| CI/CD | GitHub Actions | — |
| Cloud Provider | AWS | — |

### 2.2 Architecture

Layered monolith with clear module boundaries:

```
src/
└── app/
    ├── __init__.py          # Package init
    ├── main.py              # FastAPI app factory, OTEL setup, lifespan events
    ├── config.py            # Pydantic Settings (centralized configuration)
    ├── deps.py              # Dependency injection (RDS, Kafka, blacklist cache)
    ├── routes.py            # Business endpoints: POST /, GET /status, GET /health
    ├── ops.py               # /ops/* SRE diagnostic and remediation endpoints
    ├── event_types.py       # Event classification, validation, output generation
    ├── output.py            # JSON flattening, output JSON generation
    ├── obfuscation.py       # Blacklist lookup, 3-tier cache, channel obfuscation
    ├── security.py          # HMAC T1_SALT hash validation (inline, replaces cnlib)
    ├── models.py            # Pydantic request/response models with OpenAPI examples
    ├── middleware.py         # Request logging, Golden Signals/RED metrics middleware
    └── exceptions.py        # Custom exceptions and FastAPI exception handlers
```

### 2.3 Module Dependency Graph

```
routes.py ──▶ models.py
    │         security.py
    │         event_types.py ──▶ output.py
    │         obfuscation.py ──▶ rds_module.client
    │         delivery (kafka_module.producer)
    │
ops.py ──▶ deps.py (RDS health, Kafka health, cache state, metrics)
    │
middleware.py ──▶ metrics collection (Golden Signals, RED)
    │
main.py ──▶ config.py
    │        deps.py (lifespan: init cache, connect pool)
    │        routes.py, ops.py (router registration)
    │        middleware.py (middleware registration)
```

### 2.4 External Module Integration

#### kafka_module (rebuilder-evergreen-kafka-python)

**Purpose:** Replaces cnlib.firehose.Firehose for data delivery.

**Integration:**
- pyproject.toml: `kafka-module = {path = "../rebuilder-evergreen-kafka-python"}` (local dev) or editable install
- docker-compose: volume mount `../rebuilder-evergreen-kafka-python:/modules/kafka_module`
- CI: `pip install ./kafka_module` or `--disable=import-error` for lint tools
- Usage: `from kafka_module.producer import send_message, health_check, flush`

**Topic Mapping:**

| Legacy Firehose | Kafka Topic | Condition |
|---|---|---|
| `EVERGREEN_FIREHOSE_NAME` | `tvevents-evergreen` | Always (replaces SEND_EVERGREEN) |
| `LEGACY_FIREHOSE_NAME` | `tvevents-legacy` | Configurable (replaces SEND_LEGACY) |
| `DEBUG_EVERGREEN_FIREHOSE_NAME` | `tvevents-debug-evergreen` | When TVEVENTS_DEBUG=true |
| `DEBUG_LEGACY_FIREHOSE_NAME` | `tvevents-debug-legacy` | When TVEVENTS_DEBUG=true and SEND_LEGACY=true |

#### rds_module (rebuilder-evergreen-rds-python)

**Purpose:** Replaces TvEventsRds with pooled, instrumented PostgreSQL client.

**Integration:**
- pyproject.toml: `rds-module = {path = "../rebuilder-evergreen-rds-python"}` (local dev) or editable install
- docker-compose: volume mount `../rebuilder-evergreen-rds-python:/modules/rds_module`
- CI: `pip install ./rds_module` or `--disable=import-error` for lint tools
- Usage: `from rds_module.client import execute_query, close_pool, health_check`

**Query Mapping:**

| Legacy Method | Target Call |
|---|---|
| `TvEventsRds._execute(query)` | `execute_query(sql, params)` |
| `TvEventsRds._connect()` | Handled internally by connection pool |

## 3. API Design

### 3.1 Business Endpoints

| Method | Path | Auth | Request | Response | Description |
|---|---|---|---|---|---|
| POST | `/` | HMAC (T1_SALT) | JSON: `{TvEvent: {...}, EventData: {...}}` + query params `tvid`, `event_type` | `"OK"` (200) or JSON error (400) | Main TV event ingestion — backward compatible |
| GET | `/status` | None | None | `"OK"` (200) | Simple health check — backward compatible |
| GET | `/health` | None | None | JSON: `{status, dependencies: {rds, kafka}}` | Deep health check with dependency status; returns 503 if unhealthy |

### 3.2 SRE Diagnostic Endpoints (/ops/*)

| Method | Path | Description |
|---|---|---|
| GET | `/ops/status` | Service status: uptime, version, build info, dependency health summary |
| GET | `/ops/health` | Deep health with per-dependency latency (RDS ping, Kafka metadata) |
| GET | `/ops/metrics` | Golden Signals (latency p50/p95/p99, traffic, errors, saturation) + RED metrics |
| GET | `/ops/config` | Runtime configuration (sanitized — no secrets) |
| GET | `/ops/errors` | Recent error log (last N errors with timestamps and stack traces) |
| GET | `/ops/cache` | Blacklist cache state: item count, last refresh time, source (memory/file/rds) |

### 3.3 SRE Remediation Endpoints (/ops/*)

| Method | Path | Description |
|---|---|---|
| POST | `/ops/cache/flush` | Flush blacklist cache (memory + file) |
| POST | `/ops/cache/refresh` | Refresh blacklist from RDS |
| GET/POST | `/ops/circuits` | Circuit breaker states for RDS and Kafka |
| PUT | `/ops/loglevel` | Set log level dynamically |
| PUT | `/ops/log-level` | Alias for /ops/loglevel |

### 3.4 Request/Response Models

All endpoints use Pydantic models with `json_schema_extra` examples for OpenAPI documentation. The POST `/` endpoint accepts the legacy JSON format wrapped in a Pydantic model for validation while maintaining backward compatibility.

### 3.5 Error Responses

| HTTP Code | Condition | Response Body |
|---|---|---|
| 200 | Success | `"OK"` (POST /) or JSON object |
| 400 | Missing required params | `{"error": "TvEventsMissingRequiredParamError", "message": "..."}` |
| 400 | Invalid payload | `{"error": "TvEventsInvalidPayloadError", "message": "..."}` |
| 400 | Security hash failure | `{"error": "TvEventsSecurityValidationError", "message": "..."}` |
| 503 | Unhealthy dependencies | `{"status": "unhealthy", "dependencies": {...}}` |

## 4. Data Model

### 4.1 Database Schema

Single read-only table in RDS PostgreSQL:

```sql
-- Table: public.tvevents_blacklisted_station_channel_map
-- Access: SELECT DISTINCT channel_id (read-only from this service)
CREATE TABLE IF NOT EXISTS public.tvevents_blacklisted_station_channel_map (
    channel_id VARCHAR NOT NULL
);
```

### 4.2 Blacklist Cache Architecture

3-tier cache preserved from legacy:

```
Tier 1: In-memory set (fastest, reset on pod restart)
    ↓ miss
Tier 2: File cache /tmp/.blacklisted_channel_ids_cache (JSON, survives process restart within pod)
    ↓ miss
Tier 3: RDS query SELECT DISTINCT channel_id FROM tvevents_blacklisted_station_channel_map
```

Cache refresh via `/ops/cache/refresh` forces Tier 3 → Tier 2 → Tier 1 update.

### 4.3 Event Payload Schema

```json
{
  "TvEvent": {
    "tvid": "string (device identifier)",
    "h": "string (HMAC security hash)",
    "client": "string (client identifier)",
    "timestamp": "number (epoch ms)",
    "EventType": "string (NATIVEAPP_TELEMETRY | ACR_TUNER_DATA | PLATFORM_TELEMETRY)"
  },
  "EventData": {
    "...event-type-specific fields..."
  }
}
```

## 5. Observability & SRE

### 5.1 Structured Logging

- Python `logging` module with structured JSON format
- Log correlation with OTEL trace_id and span_id
- Dynamic log level adjustment via `/ops/loglevel`

### 5.2 Metrics

**Application Metrics (via middleware + /ops/metrics):**
- Golden Signals: latency (p50/p95/p99), traffic (requests/sec), errors (error rate), saturation (active connections)
- RED Metrics: rate, errors, duration per endpoint

**Business Metrics (via OTEL counters):**
- `tvevents.ingestion_counter` — events received
- `tvevents.validation_error_counter` — validation failures
- `tvevents.kafka_send_counter` — messages sent to Kafka
- `tvevents.obfuscation_counter` — channels obfuscated
- `tvevents.cache_hit_counter` / `tvevents.cache_miss_counter` — blacklist cache performance

### 5.3 Tracing

- OTEL auto-instrumentation via `opentelemetry-instrument`
- Custom spans for business operations (validation, event processing, delivery)
- Trace context propagation across Kafka messages

### 5.4 Health Checks

- `/health` — deep check with RDS ping + Kafka metadata query; returns 503 if any dependency is down
- `/status` — shallow "OK" for backward compatibility with existing probes

## 6. Infrastructure

### 6.1 Container

- Base image: `python:3.12-slim`
- Non-root user
- `entrypoint.sh` sources `environment-check.sh`
- OTEL auto-instrumentation via `opentelemetry-instrument`
- Expose port 8000

### 6.2 Kubernetes (Helm)

- Deployment, Service, HTTPRoute, ScaledObject, PDB, ServiceAccount
- ExternalSecret for secrets management
- OTEL Collector sidecar
- KEDA autoscaling (CPU-based, matching legacy scaling profile)

### 6.3 Terraform

- `terraform/` directory with environment-specific variable files
- State backend: `s3://` with project name
- Resources: EKS service account, IAM roles, secrets manager entries

### 6.4 Local Development (docker-compose)

```yaml
services:
  app:         # FastAPI application (port 8000)
  postgres:    # PostgreSQL 16 (port 5432) with seed data
  kafka:       # Kafka broker (port 9092) with topic auto-creation
```

Module mounts:
- `../rebuilder-evergreen-kafka-python` → `/modules/kafka_module`
- `../rebuilder-evergreen-rds-python` → `/modules/rds_module`

Seed data: `scripts/init-db.sql` creates blacklist table and inserts test channel IDs.

## 7. CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci.yml`):

| Job | Tool | Threshold |
|---|---|---|
| lint | pylint | `--fail-under=10.0 --disable=import-error` |
| format | black | `--check` (0 unformatted) |
| type-check | mypy | `--ignore-missing-imports` on `src/app/` |
| test | pytest | 0 failures |
| coverage | pytest-cov | Report (no hard threshold) |
| complexity | complexipy | `src -mx 15` (0 issues) |
| helm-lint | helm lint | 0 errors |
| helm-test | helm unittest | 0 failures |
| build | docker build | Success |
| scan | trivy | CRITICAL/HIGH block |

Triggers: `push` (main, feature/**), `pull_request`.

Container registry: AWS ECR. Image tag strategy: commit SHA.

## 8. Security

### 8.1 HMAC Authentication

- T1_SALT secret used for HMAC hash validation
- Algorithm: `security_hash_match(tvid, h_value, salt)` — inline implementation matching cnlib behavior
- Applied to every POST `/` request

### 8.2 Secrets Management

- T1_SALT, DB_PASSWORD, KAFKA_SASL_PASSWORD via AWS Secrets Manager → ExternalSecret
- No secrets in .tfvars, docker-compose, or source code
- `.env.example` documents all variables with placeholder values

## 9. Migration Plan

### 9.1 Data Migration

**None required.** The rebuilt service reads from the same RDS table (`tvevents_blacklisted_station_channel_map`) using the same query. No schema changes.

### 9.2 Traffic Migration

1. Deploy rebuilt service alongside legacy in dev/staging
2. Validate output parity: same input payloads produce identical Kafka messages as Firehose records
3. Configure downstream consumers to read from Kafka topics
4. Route production traffic to rebuilt service via AGA weight shifting
5. Monitor error rates, latency, and throughput during cutover
6. Decommission legacy service after validation period

## 10. ADRs Required

1. **ADR-001: Use FastAPI as Web Framework** — replacing Flask
2. **ADR-002: Replace Kinesis Firehose with Kafka** — via standalone kafka_module
3. **ADR-003: Use Standalone RDS Module with Connection Pooling** — via rds_module
4. **ADR-004: Inline HMAC Security Hash** — replacing cnlib.token_hash
5. **ADR-005: Stay on AWS** — no cloud migration
6. **ADR-006: Use PostgreSQL via RDS** — same database engine, new client
7. **ADR-007: Use Kubernetes (EKS) for Container Orchestration** — same as legacy

## 11. Success Criteria

1. All template repo checklist items completed
2. POST `/` backward compatible with TV firmware payloads
3. All 11 /ops/* endpoints functional and returning real data
4. ≥80% test coverage on pure logic modules
5. 0 pylint errors (score ≥ 9.0), 0 black formatting issues, 0 mypy errors
6. `docker compose up --build` starts working local stack
7. Kafka delivery verified with test payloads
8. RDS blacklist lookup verified with test data
9. HMAC hash validation verified with known test vectors
10. CI pipeline passes all gates
