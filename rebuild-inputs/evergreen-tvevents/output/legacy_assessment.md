# Legacy Assessment: evergreen-tvevents (tvevents-k8s)

> **Reference document.** This assessment was generated during Step 1 of the ideation process. It informs decisions but does not override python-developer-agent/skill.md.

## Executive Summary

The tvevents-k8s application is a high-throughput TV telemetry collector running on AWS EKS. It receives HTTP POST payloads from millions of SmartCast TVs, validates security hashes and event schemas, transforms payloads into flattened JSON, applies channel blacklist obfuscation, and forwards processed data to AWS Kinesis Data Firehose streams. The application is functional and actively maintained but carries significant technical debt: Python 3.10, Flask (synchronous WSGI), a fragile cnlib git submodule, no connection pooling, 87+ runtime dependencies (many unused), no OpenAPI spec, no /ops/* diagnostic endpoints, and no local development stack (docker-compose).

## Codebase Inventory

| Metric | Value |
|---|---|
| Primary Language | Python 3.10 |
| Framework | Flask 3.1.1 + Gunicorn 23.0.0 (gevent workers) |
| Source files (app/) | 5 (.py) |
| Source lines (app/) | 1,169 |
| Test files | 18 (.py) |
| Test lines | 1,898 |
| Total runtime dependencies | 87+ |
| Dev dependencies | 14 |
| Helm chart templates | 16 |
| CI/CD workflows | 6 |
| Container base image | python:3.10-bookworm (pinned SHA) |

### Source File Breakdown

| File | Lines | Purpose |
|---|---|---|
| `app/__init__.py` | 104 | App factory, OTEL setup (TracerProvider, MeterProvider, LoggerProvider), Flask app creation |
| `app/routes.py` | 94 | HTTP endpoints: POST `/` (firehose ingestion), GET `/status` (health), request logging, error handler |
| `app/event_type.py` | 260 | Event type classes: EventType (ABC), NativeAppTelemetryEventType, AcrTunerDataEventType, PlatformTelemetryEventType |
| `app/dbhelper.py` | 298 | RDS client: TvEventsRds class with psycopg2 direct connections, file cache, blacklist channel ID operations |
| `app/utils.py` | 418 | Business logic: validation, security hash, JSON flattening, Firehose delivery, obfuscation, output generation |

### Test File Breakdown

| Test File | Tests For |
|---|---|
| `tests/routes/routes_test.py` | HTTP route handlers |
| `tests/init/test_init.py` | App initialization |
| `tests/db_helper/db_helper_test.py` | RDS client operations |
| `tests/event_type/event_type_test.py` | Base EventType class |
| `tests/event_type/acr_tuner_data_event_type_test.py` | ACR tuner data validation |
| `tests/event_type/platform_telemetry_event_type_test.py` | Platform telemetry validation |
| `tests/utils/validate_request_test.py` | Request validation |
| `tests/utils/verify_required_params_test.py` | Required parameter checks |
| `tests/utils/flatten_request_json_test.py` | JSON flattening |
| `tests/utils/generate_output_json_test.py` | Output JSON generation |
| `tests/utils/push_changes_to_firehose_test.py` | Firehose delivery |
| `tests/utils/send_to_valid_firehose_test.py` | Multi-firehose send |
| `tests/utils/should_obfuscate_channel_test.py` | Obfuscation logic |
| `tests/utils/is_blacklist_channel_test.py` | Blacklist lookup |
| `tests/utils/params_match_check_test.py` | Parameter matching |
| `tests/utils/timestamp_check_test.py` | Timestamp validation |
| `tests/utils/unix_time_to_ms_test.py` | Timestamp conversion |
| `tests/utils/get_event_type_mapping_test.py` | Event type mapping |

## Architecture Health

**Rating: ⚠️ MODERATE**

The application is a monolithic Flask service with a clear data flow: receive → validate → classify → transform → obfuscate → deliver. This pipeline is appropriate for the workload. However:

- **No separation of concerns** — `utils.py` (418 lines) mixes validation, security, business logic, data transformation, and I/O delivery in a single module
- **Tight coupling to cnlib** — security hash (`token_hash.security_hash_match`) and data delivery (`firehose.Firehose`) are imported from a git submodule that requires `setup.py install`
- **No dependency injection** — `TVEVENTS_RDS = dbhelper.TvEventsRds()` instantiated at module level, making testing require mocks at import time
- **Module-level side effects** — Firehose lists populated from environment variables at import time (`VALID_TVEVENTS_FIREHOSES`)
- **Flask app factory pattern** used correctly via `create_app()`, but routes registered inside `app_context()` block

### Data Flow

```
TV → POST / → validate_request() → generate_output_json() → push_changes_to_firehose()
                    ↓                        ↓                          ↓
              verify_required_params   event_type_map[ET]          should_obfuscate_channel()
              params_match_check       .validate_event_type_payload    ↓
              timestamp_check          .generate_event_data_output_json  blacklisted_channel_ids()
              validate_security_hash                                    ↓
                                                                   send_to_valid_firehoses()
                                                                       ↓
                                                                   cnlib.firehose.Firehose.send_records()
```

## API Surface Health

**Rating: ⚠️ MODERATE**

| Endpoint | Method | Auth | Description | Issues |
|---|---|---|---|---|
| `/` | POST | HMAC (T1_SALT) | Main ingestion | Returns bare `"OK"` string, no structured response model |
| `/status` | GET | None | Health check | Always returns `"OK"` — does not check dependencies |

- **No OpenAPI spec** — API undocumented, no typed request/response models
- **No /ops/* endpoints** — no SRE diagnostic or remediation capabilities
- **Health check is shallow** — `/status` always returns OK even if RDS or Firehose are down
- **No rate limiting** — relies on infrastructure-level throttling
- **Error responses** are JSON `{"error": type, "message": msg}` with 400 status — reasonable but not OpenAPI-documented
- **Backward compatibility critical** — TV firmware sends specific payload format that cannot change

## Observability & SRE

**Rating: ⚠️ MODERATE**

**Strengths:**
- Comprehensive OTEL instrumentation: TracerProvider, MeterProvider, LoggerProvider all configured
- OTLP HTTP exporters to New Relic
- Flask, psycopg2, boto3/botocore, requests, urllib3 auto-instrumented
- Custom OTEL counters for business operations (firehose sends, DB ops, event validation, heartbeats)
- DB query duration histogram with operation/status labels

**Weaknesses:**
- **No /ops/* endpoints** — cannot query metrics, health, config, errors, or cache status via HTTP
- **No Golden Signals or RED metrics** served by the application — only emitted via OTEL
- **No circuit breakers** — Firehose/RDS failures propagate directly
- **No SLOs/SLAs defined**
- **Logging via cnlib.log wrapper** — adds unnecessary indirection
- **No structured JSON logging** — log messages are formatted strings

## Auth & Access Control

**Rating: ✅ ADEQUATE**

- HMAC-based security hash validation via `cnlib.cnlib.token_hash.security_hash_match(tvid, h_value, SALT_KEY)`
- T1_SALT environment variable provides the secret key
- Hash validation is mandatory for every POST request
- No RBAC needed — single authentication model for TV payloads
- AWS IAM handles service-to-service auth (Firehose, RDS)

**Risk:** cnlib dependency means the hash algorithm is opaque — must be extracted or replicated in the rebuild.

## Code & Dependency Health

**Rating: ❌ POOR**

### Dependency Issues

**87+ runtime dependencies** — many are unused or unnecessary:

| Dependency | Issue |
|---|---|
| `pymemcache` | Not imported anywhere in app/ |
| `PyMySQL` | Not imported anywhere — app uses PostgreSQL |
| `redis` | Not imported anywhere in app/ |
| `fakeredis` | Test dependency listed as runtime |
| `google-cloud-monitoring` | Not imported — OTEL replaces Stackdriver |
| `google-api-core`, `google-auth`, `google-cloud-core` | Not imported — no GCP usage |
| `pygerduty` | Not imported — PagerDuty alerting is external |
| `pyzmq` | Not imported — ZeroMQ not used |
| `python-consul` | Not imported — Consul not used in K8s |
| `boto` (v2) | Listed alongside `boto3` — legacy SDK |
| `schema` | Not imported anywhere |
| `sortedcontainers` | Not imported anywhere |
| `cachetools` | Not imported in app/ |

### Code Quality Issues

1. **Mutable default argument** — `flatten_request_json(ignore_keys=[])` (line 218, utils.py)
2. **Multiple pylint disables** — `W0107`, `W0246`, `C0415`, `R1710`, `C0301`, `R1720`, `W1508`, `W0707` scattered throughout
3. **Broad exception handling** — `except Exception as catchall_exception` pattern in routes
4. **No type annotations** — functions lack parameter and return type hints
5. **f-string/format mixing** — inconsistent string formatting (some f-strings, some `.format()`)
6. **Module-level state** — `TVEVENTS_RDS`, `VALID_TVEVENTS_FIREHOSES`, `SALT_KEY` instantiated at import
7. **`setup.py install`** for cnlib — deprecated, should use pip install -e or modern packaging

### cnlib Dependency Analysis

The application imports from cnlib:
- `cnlib.cnlib.firehose.Firehose` → `send_records([{'Data': json.dumps(data)}])` — Kinesis Data Firehose delivery
- `cnlib.cnlib.token_hash.security_hash_match(tvid, h_value, salt_key)` → HMAC security validation
- `cnlib.cnlib.log.getLogger(__name__)` → logging wrapper

All three can be replaced: Firehose → kafka_module, token_hash → inline implementation or extracted utility, log → standard Python logging.

## Operational Health

**Rating: ⚠️ MODERATE**

**Strengths:**
- Docker container with non-root user (`flaskuser`)
- `environment-check.sh` validates all required env vars at startup
- `entrypoint.sh` handles AWS config, OTEL setup, cache initialization
- Gunicorn with configurable workers (`WEB_CONCURRENCY`), max-requests for worker recycling
- HEALTHCHECK in Dockerfile
- Liveness and readiness probes in Helm chart
- Rolling update deployment strategy with PDB
- KEDA ScaledObject for autoscaling (up to 500 pods in prod)

**Weaknesses:**
- `/status` health check doesn't verify dependencies
- Cache initialization failure at startup logs warning but continues (`|| printf "Cache initialization failed, continuing..."`)
- No graceful shutdown handling beyond Gunicorn defaults
- No docker-compose for local development
- `env.list` incomplete — only 9 of 40+ required env vars

## Data Health

**Rating: ✅ ADEQUATE**

- **Single table:** `tvevents_blacklisted_station_channel_map` with `channel_id` column
- **3-tier cache:** in-memory `_blacklisted_channel_ids` → file cache `/tmp/.blacklisted_channel_ids_cache` → RDS query
- **Cache initialized at startup** via `initialize_blacklisted_channel_ids_cache()`
- **Cache miss fallback** properly implemented in `blacklisted_channel_ids()`
- **No connection pooling** — each `_execute()` call opens and closes a connection via `_connect()`
- **SQL injection risk low** — queries use string formatting but with no user-provided values in channel ID query
- **No ORM** — direct SQL, appropriate for single-table lookups

## Developer Experience

**Rating: ❌ POOR**

- **No docker-compose** — cannot run the full stack locally without manual RDS/Firehose/AWS setup
- **cnlib git submodule** — requires `git submodule init && update` and `pip install -e cntools_py3/cnlib`
- **No OpenAPI spec** — developers must read source to understand the API
- **Incomplete env.list** — only 9 of 40+ environment variables
- **No IDE agent instructions** — no `.windsurfrules` or `.github/copilot-instructions.md`
- **6 CI workflows** but no local `act` config for all of them
- **Pytest config in pytest.ini** (separate file) rather than unified in pyproject.toml
- **No pre-commit hook automation** — `hooks/pre-commit` exists but must be manually enabled via `git config core.hooksPath hooks`

## Infrastructure Health

**Rating: ✅ ADEQUATE**

- **Dockerfile** follows reasonable patterns: pinned base image SHA, non-root user, CVE remediation, HEALTHCHECK
- **Helm charts** comprehensive: ClusterDeployment, HTTPRoute, ScaledObject, PDB, ServiceAccount, OtelCollector
- **KEDA autoscaling** — CPU-based with configurable min/max replicas per environment
- **Rolling update** strategy with maxSurge 50%, maxUnavailable 25%
- **AGA (Global Accelerator)** for traffic management with traffic shift script

**Gaps:**
- No Terraform — infrastructure managed via Helm only
- Dockerfile uses `python:3.10-bookworm` (full image) — should use `slim` variant
- Many `apt-get install` of system libraries that may not be needed
- `pip install --no-cache-dir -r requirements.txt` without hash verification

## External Dependencies

**Rating: ⚠️ MODERATE**

| Dependency | Interface | Risk |
|---|---|---|
| AWS RDS PostgreSQL | psycopg2 direct | Low — well-understood, but no pooling |
| AWS Kinesis Data Firehose | cnlib.firehose (boto3) | Medium — AWS-specific, to be replaced with Kafka |
| cnlib (git submodule) | Python import | High — fragile dependency, opaque implementations |
| AWS Global Accelerator | Traffic routing | Low — infrastructure concern, not app-level |
| New Relic (via OTEL) | OTLP HTTP | Low — standard OTEL exporters |

## Health Summary Scorecard

| Dimension | Rating | Key Finding |
|---|---|---|
| Architecture Health | ⚠️ MODERATE | Clear pipeline but tight coupling, no separation of concerns in utils.py |
| API Surface Health | ⚠️ MODERATE | Only 2 endpoints, no OpenAPI, shallow health check, no /ops/* |
| Observability & SRE | ⚠️ MODERATE | Good OTEL instrumentation but no diagnostic endpoints |
| Auth & Access Control | ✅ ADEQUATE | HMAC validation works but depends on cnlib |
| Code & Dependency Health | ❌ POOR | 87+ deps (many unused), no type hints, mutable defaults |
| Operational Health | ⚠️ MODERATE | Good Helm/K8s setup but shallow health checks |
| Data Health | ✅ ADEQUATE | Simple schema, good cache pattern, no pooling |
| Developer Experience | ❌ POOR | No docker-compose, no OpenAPI, cnlib submodule friction |
| Infrastructure Health | ✅ ADEQUATE | Solid Helm charts, KEDA scaling, but no Terraform |
| External Dependencies | ⚠️ MODERATE | AWS-locked (Firehose), cnlib fragility |
