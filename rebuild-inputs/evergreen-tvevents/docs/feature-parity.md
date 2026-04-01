# Feature Parity Matrix: evergreen-tvevents → rebuilder-evergreen-tvevents

> **Reference document.** This matrix was generated during Step 10 of the ideation process. It tracks feature parity between the legacy and rebuilt services.

## Legend

| Status | Meaning |
|---|---|
| ✅ PARITY | Feature exists in both legacy and rebuilt, behavior identical |
| 🔄 REPLACED | Feature exists in legacy, replaced with equivalent in rebuilt |
| ➕ NEW | Feature does not exist in legacy, added in rebuilt |
| ❌ DROPPED | Feature exists in legacy, intentionally removed in rebuilt |
| ⚠️ MODIFIED | Feature exists in both, behavior intentionally changed |

## API Endpoints

| Feature | Legacy | Rebuilt | Status | Notes |
|---|---|---|---|---|
| POST `/` — TV event ingestion | ✅ | ✅ | ✅ PARITY | Same URL, same query params (tvid, event_type), same JSON body, same "OK" response |
| GET `/status` — health check | ✅ | ✅ | ✅ PARITY | Returns "OK" (200) — backward compatible with existing probes |
| GET `/health` — deep health | ❌ | ✅ | ➕ NEW | Returns dependency health (RDS, Kafka) with latency; 503 if unhealthy |
| GET `/ops/status` | ❌ | ✅ | ➕ NEW | Composite health verdict with uptime, version, dependency summary |
| GET `/ops/health` | ❌ | ✅ | ➕ NEW | Per-dependency health with latency measurements |
| GET `/ops/metrics` | ❌ | ✅ | ➕ NEW | Golden Signals + RED metrics |
| GET `/ops/config` | ❌ | ✅ | ➕ NEW | Runtime config (sanitized, no secrets) |
| GET `/ops/errors` | ❌ | ✅ | ➕ NEW | Recent error log |
| GET `/ops/cache` | ❌ | ✅ | ➕ NEW | Blacklist cache state and statistics |
| POST `/ops/cache/flush` | ❌ | ✅ | ➕ NEW | Flush blacklist cache |
| POST `/ops/cache/refresh` | ❌ | ✅ | ➕ NEW | Refresh blacklist from RDS |
| GET/POST `/ops/circuits` | ❌ | ✅ | ➕ NEW | Circuit breaker states |
| PUT `/ops/loglevel` | ❌ | ✅ | ➕ NEW | Dynamic log level adjustment |
| PUT `/ops/log-level` | ❌ | ✅ | ➕ NEW | Alias for /ops/loglevel |
| GET `/docs` — OpenAPI | ❌ | ✅ | ➕ NEW | Auto-generated OpenAPI documentation |

## Event Processing

| Feature | Legacy | Rebuilt | Status | Notes |
|---|---|---|---|---|
| NATIVEAPP_TELEMETRY validation | ✅ | ✅ | ✅ PARITY | Same validation: Timestamp required in EventData |
| NATIVEAPP_TELEMETRY output | ✅ | ✅ | ✅ PARITY | Same flattening, eventdata_timestamp field |
| ACR_TUNER_DATA validation | ✅ | ✅ | ✅ PARITY | Same: channelData or programData required; majorId/minorId validation |
| ACR_TUNER_DATA output | ✅ | ✅ | ✅ PARITY | Same flattening, programdata_starttime to ms, Heartbeat marking |
| PLATFORM_TELEMETRY validation | ✅ | ✅ | ✅ PARITY | Same JSON Schema: PanelData with Timestamp, PanelState, WakeupReason |
| PLATFORM_TELEMETRY output | ✅ | ✅ | ✅ PARITY | Same flattening, PanelState uppercase normalization |
| Event type registry | ✅ | ✅ | ✅ PARITY | Same mapping: event_type_map dict |
| Heartbeat detection | ✅ | ✅ | ✅ PARITY | Same logic: ACR_TUNER_DATA without channelData/programData at top level |

## Request Validation

| Feature | Legacy | Rebuilt | Status | Notes |
|---|---|---|---|---|
| Required params check | ✅ | ✅ | ✅ PARITY | Same required fields: tvid, h, client, timestamp, EventType |
| URL/payload param match | ✅ | ✅ | ✅ PARITY | tvid and event_type must match between URL params and payload |
| Timestamp validation | ✅ | ✅ | ✅ PARITY | Same validation: parseable, within acceptable range |
| HMAC security hash | ✅ (cnlib) | ✅ (inline) | 🔄 REPLACED | Same algorithm, inline implementation replaces cnlib.token_hash |

## Data Delivery

| Feature | Legacy | Rebuilt | Status | Notes |
|---|---|---|---|---|
| Evergreen stream delivery | ✅ (Firehose) | ✅ (Kafka) | 🔄 REPLACED | `EVERGREEN_FIREHOSE_NAME` → `KAFKA_TOPIC_EVERGREEN` |
| Legacy stream delivery | ✅ (Firehose) | ✅ (Kafka) | 🔄 REPLACED | `LEGACY_FIREHOSE_NAME` → `KAFKA_TOPIC_LEGACY` |
| Debug evergreen delivery | ✅ (Firehose) | ✅ (Kafka) | 🔄 REPLACED | `DEBUG_EVERGREEN_FIREHOSE_NAME` → `KAFKA_TOPIC_DEBUG_EVERGREEN` |
| Debug legacy delivery | ✅ (Firehose) | ✅ (Kafka) | 🔄 REPLACED | `DEBUG_LEGACY_FIREHOSE_NAME` → `KAFKA_TOPIC_DEBUG_LEGACY` |
| SEND_EVERGREEN flag | ✅ | ✅ | ✅ PARITY | Controls whether evergreen topic receives data |
| SEND_LEGACY flag | ✅ | ✅ | ✅ PARITY | Controls whether legacy topic receives data |
| TVEVENTS_DEBUG flag | ✅ | ✅ | ✅ PARITY | Controls whether debug topics receive data |
| Parallel multi-stream delivery | ✅ (ThreadPoolExecutor) | ✅ (sequential per topic) | ⚠️ MODIFIED | Kafka producer.poll(0) is non-blocking; explicit parallelism not needed |

## Obfuscation & Blacklisting

| Feature | Legacy | Rebuilt | Status | Notes |
|---|---|---|---|---|
| Channel blacklist lookup | ✅ | ✅ | ✅ PARITY | Same SQL: SELECT DISTINCT channel_id FROM tvevents_blacklisted_station_channel_map |
| 3-tier cache (memory → file → RDS) | ✅ | ✅ | ✅ PARITY | Same cache hierarchy |
| File cache path | ✅ | ✅ | ✅ PARITY | BLACKLIST_CHANNEL_IDS_CACHE_FILEPATH env var |
| Startup cache initialization | ✅ | ✅ | ✅ PARITY | Initialize cache on app startup |
| iscontentblocked obfuscation | ✅ | ✅ | ✅ PARITY | Same: obfuscate if iscontentblocked=true |
| Blacklisted channel obfuscation | ✅ | ✅ | ✅ PARITY | Same: obfuscate if channel_id in blacklist |
| Obfuscation fields | ✅ | ✅ | ✅ PARITY | Same: channelid, programid, channelname → "OBFUSCATED" |

## JSON Processing

| Feature | Legacy | Rebuilt | Status | Notes |
|---|---|---|---|---|
| Recursive JSON flattening | ✅ | ✅ | ✅ PARITY | Same algorithm with prefix and ignore_keys |
| Output field naming | ✅ | ✅ | ✅ PARITY | Same lowercase key concatenation |
| Zoo field in output | ✅ | ✅ | ✅ PARITY | Same: FLASK_ENV → ENV value appended to output |
| Namespace extraction | ✅ | ✅ | ✅ PARITY | Same case-insensitive key lookup |

## Observability

| Feature | Legacy | Rebuilt | Status | Notes |
|---|---|---|---|---|
| OTEL TracerProvider | ✅ | ✅ | ✅ PARITY | Same: OTLP HTTP exporter |
| OTEL MeterProvider | ✅ | ✅ | ✅ PARITY | Same: OTLP HTTP exporter |
| OTEL LoggerProvider | ✅ | ✅ | ✅ PARITY | Same: OTLP HTTP exporter |
| Flask/FastAPI auto-instrumentation | ✅ | ✅ | 🔄 REPLACED | FlaskInstrumentor → FastAPIInstrumentor |
| psycopg2 instrumentation | ✅ | ✅ | ✅ PARITY | Via rds_module OTEL spans |
| boto3/botocore instrumentation | ✅ | ❌ | ❌ DROPPED | No longer needed — Firehose replaced by Kafka |
| Custom business metrics | ✅ | ✅ | ✅ PARITY | Same counters for ingestion, validation, delivery |
| Golden Signals metrics | ❌ | ✅ | ➕ NEW | Latency, traffic, errors, saturation via middleware |
| RED metrics | ❌ | ✅ | ➕ NEW | Rate, errors, duration per endpoint |

## Infrastructure

| Feature | Legacy | Rebuilt | Status | Notes |
|---|---|---|---|---|
| Docker container | ✅ | ✅ | ⚠️ MODIFIED | python:3.10-bookworm → python:3.12-slim |
| Non-root user | ✅ | ✅ | ✅ PARITY | Same pattern: flaskuser group/user |
| entrypoint.sh | ✅ | ✅ | ⚠️ MODIFIED | Template pattern with uvicorn instead of gunicorn |
| environment-check.sh | ✅ | ✅ | ⚠️ MODIFIED | Updated env var names (RDS_* → DB_*, Firehose → Kafka) |
| Helm charts | ✅ | ✅ | ⚠️ MODIFIED | Template repo charts, updated for new env vars |
| KEDA autoscaling | ✅ | ✅ | ✅ PARITY | Same CPU-based scaling |
| Rolling update | ✅ | ✅ | ✅ PARITY | Same strategy |
| PDB | ✅ | ✅ | ✅ PARITY | Same pod disruption budget |
| Terraform IaC | ❌ | ✅ | ➕ NEW | Infrastructure as code (legacy has none) |
| docker-compose | ❌ | ✅ | ➕ NEW | Local development stack |
| CI pipeline | ✅ | ✅ | ⚠️ MODIFIED | Enhanced: added complexity, type check, coverage, helm lint |

## Dependencies

| Feature | Legacy | Rebuilt | Status | Notes |
|---|---|---|---|---|
| cnlib git submodule | ✅ | ❌ | ❌ DROPPED | Replaced by kafka_module, rds_module, inline security |
| Flask | ✅ | ❌ | ❌ DROPPED | Replaced by FastAPI |
| Gunicorn/gevent | ✅ | ❌ | ❌ DROPPED | Replaced by uvicorn |
| boto3 (Firehose) | ✅ | ❌ | ❌ DROPPED | Replaced by kafka_module (confluent-kafka) |
| pymemcache | ✅ | ❌ | ❌ DROPPED | Never imported — unused |
| PyMySQL | ✅ | ❌ | ❌ DROPPED | Never imported — unused |
| redis | ✅ | ❌ | ❌ DROPPED | Never imported — unused |
| fakeredis | ✅ | ❌ | ❌ DROPPED | Test dep listed as runtime — unused |
| google-cloud-monitoring | ✅ | ❌ | ❌ DROPPED | Never imported — OTEL replaces |
| pygerduty | ✅ | ❌ | ❌ DROPPED | Never imported — unused |
| pyzmq | ✅ | ❌ | ❌ DROPPED | Never imported — unused |
| python-consul | ✅ | ❌ | ❌ DROPPED | Never imported — unused |
| FastAPI | ❌ | ✅ | ➕ NEW | Web framework |
| uvicorn | ❌ | ✅ | ➕ NEW | ASGI server |
| pydantic | ❌ | ✅ | ➕ NEW | Request/response models |
| kafka_module | ❌ | ✅ | ➕ NEW | Kafka producer (local path dep) |
| rds_module | ❌ | ✅ | ➕ NEW | RDS client with pooling (local path dep) |

## Summary

| Category | Parity | Replaced | New | Dropped | Modified |
|---|---|---|---|---|---|
| API Endpoints | 2 | 0 | 13 | 0 | 0 |
| Event Processing | 8 | 0 | 0 | 0 | 0 |
| Request Validation | 3 | 1 | 0 | 0 | 0 |
| Data Delivery | 3 | 4 | 0 | 0 | 1 |
| Obfuscation | 7 | 0 | 0 | 0 | 0 |
| JSON Processing | 4 | 0 | 0 | 0 | 0 |
| Observability | 5 | 1 | 2 | 1 | 0 |
| Infrastructure | 4 | 0 | 2 | 0 | 4 |
| Dependencies | 0 | 0 | 5 | 12 | 0 |
| **Total** | **36** | **6** | **22** | **13** | **5** |
