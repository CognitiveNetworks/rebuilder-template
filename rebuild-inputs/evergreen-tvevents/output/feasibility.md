# Feasibility Analysis: evergreen-tvevents

> **Reference document.** This analysis was generated during Step 4 of the ideation process. It informs decisions but does not override python-developer-agent/skill.md.

## Assessment Summary

The evergreen-tvevents rebuild is **highly feasible**. The application is small (1,169 source lines across 5 files), has a clear data pipeline architecture, well-understood business logic, and existing test coverage (18 test files). The two most significant dependencies — Firehose delivery and RDS client — already have standalone replacement modules built and tested (`kafka_module` and `rds_module`). The remaining cnlib dependency (token_hash) is a single function that can be inlined.

## Feasibility by Opportunity

### 1. Flask → FastAPI

| Factor | Assessment |
|---|---|
| **Complexity** | Low — 2 endpoints, 1 error handler, 1 before_request hook |
| **Data model compatibility** | High — JSON payloads map directly to Pydantic models |
| **Test migration** | Straightforward — Flask test client → FastAPI TestClient (httpx) |
| **OTEL compatibility** | Full — OpenTelemetry has FastAPI auto-instrumentation |
| **Breaking changes** | None for TV firmware — POST `/` and GET `/status` remain identical |
| **Effort estimate** | 1-2 days |
| **Verdict** | ✅ **FEASIBLE** |

### 2. Firehose → Kafka

| Factor | Assessment |
|---|---|
| **Module readiness** | Complete — `kafka_module/producer.py` (268 lines) is built and tested |
| **Interface mapping** | Direct — `Firehose.send_records([{'Data': json.dumps(data)}])` → `send_message(topic, json.dumps(data).encode(), key=tvid)` |
| **Configuration** | Simpler — single `KAFKA_BROKERS` + optional SASL vs. 7 firehose env vars |
| **Multi-stream routing** | Topic-based — replace 4 firehose streams with Kafka topics |
| **OTEL instrumentation** | Already in kafka_module — tracing spans and metrics match legacy patterns |
| **Local development** | Standard Kafka Docker image available |
| **Effort estimate** | 0.5 days (integration only — module already exists) |
| **Verdict** | ✅ **FEASIBLE** |

### 3. cnlib → Standalone Modules + Inline

| Factor | Assessment |
|---|---|
| **firehose.Firehose** | Replaced by kafka_module (see #2 above) |
| **token_hash.security_hash_match** | Single function — HMAC comparison. Can be inlined as ~10 lines of Python using `hashlib.md5` or extracted from cnlib source. Must verify algorithm matches production behavior. |
| **log.getLogger** | Drop-in replacement: `logging.getLogger(__name__)` |
| **Risk** | The token_hash algorithm must be verified. If it uses a non-standard hashing scheme, extraction may require reading cnlib source. |
| **Effort estimate** | 0.5 days |
| **Verdict** | ✅ **FEASIBLE** |

### 4. RDS Connection Pooling

| Factor | Assessment |
|---|---|
| **Module readiness** | Complete — `rds_module/client.py` (298 lines) is built and tested |
| **Interface mapping** | `TvEventsRds._execute(query)` → `rds_module.client.execute_query(sql, params)` |
| **Connection pooling** | ThreadedConnectionPool with configurable min/max, retry logic |
| **OTEL instrumentation** | Already in rds_module — tracing spans and metrics match legacy patterns |
| **Cache layer** | The 3-tier cache (memory → file → RDS) remains in the rebuilt service; rds_module handles only the database layer |
| **Effort estimate** | 0.5 days (integration only — module already exists) |
| **Verdict** | ✅ **FEASIBLE** |

### 5. /ops/* SRE Endpoints

| Factor | Assessment |
|---|---|
| **Complexity** | Moderate — 6 diagnostic + 5 remediation endpoints |
| **Data availability** | All required data is accessible: health from RDS/Kafka, metrics from OTEL, config from env vars, cache from blacklist state |
| **Template pattern** | Available in template repo — standard implementation pattern |
| **Dependencies** | RDS health → `rds_module.client.execute_query("SELECT 1")`, Kafka health → `kafka_module.producer.health_check()` |
| **Effort estimate** | 1-2 days |
| **Verdict** | ✅ **FEASIBLE** |

### 6. Dependency Cleanup

| Factor | Assessment |
|---|---|
| **Risk** | Low — unused packages confirmed by grep analysis |
| **Target dependency count** | ~15-20 runtime dependencies (from 87+) |
| **Compatibility** | All target dependencies (FastAPI, uvicorn, psycopg2-binary, confluent-kafka, pydantic, OTEL) have Python 3.12 wheels |
| **Effort estimate** | 0.5 days |
| **Verdict** | ✅ **FEASIBLE** |

### 7. Python 3.12 Upgrade

| Factor | Assessment |
|---|---|
| **Compatibility** | No Python 3.10-specific code patterns used |
| **Dependencies** | All target dependencies support 3.12 |
| **Base image** | `python:3.12-slim` available and actively maintained |
| **Effort estimate** | Included in rebuild (not a separate migration) |
| **Verdict** | ✅ **FEASIBLE** |

### 8. docker-compose Local Stack

| Factor | Assessment |
|---|---|
| **Components** | App, PostgreSQL, Kafka (3 containers + optional OTEL collector) |
| **Images** | Official images available: `postgres:16`, `bitnami/kafka:latest` or `confluentinc/cp-kafka` |
| **Seed data** | Blacklist table seed script needed (single table, simple INSERT) |
| **Module mounts** | rds_module and kafka_module mounted as volumes for local development |
| **Effort estimate** | 0.5-1 day |
| **Verdict** | ✅ **FEASIBLE** |

## Blocking Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| token_hash algorithm incompatibility | Low | High — breaks TV authentication | Extract algorithm from cnlib source; verify with known tvid/hash/salt test vectors from production |
| Kafka topic configuration mismatch | Low | Medium — data delivery disruption | Use kafka_module health_check() to validate connectivity; test with local Kafka |
| TV firmware payload format drift | Very Low | High — breaking change | POST `/` endpoint preserves exact same URL params and JSON schema |
| RDS schema changes | Very Low | Low — single read-only table | Schema is managed externally; rebuilt service only reads |

## Overall Feasibility

**Rating: ✅ HIGHLY FEASIBLE**

The rebuild is a clean modernization of a small, well-understood application. All major replacements (Firehose → Kafka, psycopg2 → rds_module, cnlib → inline/standalone) are already built. The application's limited scope (2 endpoints, 5 source files, 1,169 lines) and clear data pipeline make this an ideal candidate for a full rebuild rather than incremental refactoring.

**Estimated total rebuild effort:** 5-8 days for a single developer familiar with the codebase (including all template compliance, testing, documentation).
