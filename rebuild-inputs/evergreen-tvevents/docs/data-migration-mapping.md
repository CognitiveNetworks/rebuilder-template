# Data Migration Mapping: evergreen-tvevents → rebuilder-evergreen-tvevents

> **Reference document.** This mapping was generated during Step 11 of the ideation process.

## Migration Summary

**No data migration is required.** The rebuilt service reads from the same RDS PostgreSQL table (`tvevents_blacklisted_station_channel_map`) using the same query. The database schema is managed externally and shared with other services. The rebuilt service changes the client library (psycopg2 direct → rds_module with connection pooling) but not the database, table, or query.

## Database Schema

### Table: `tvevents_blacklisted_station_channel_map`

| Column | Type | Description | Access Pattern |
|---|---|---|---|
| `channel_id` | VARCHAR | Blacklisted channel identifier | SELECT DISTINCT (read-only) |

**Query (unchanged):**
```sql
SELECT DISTINCT channel_id FROM tvevents_blacklisted_station_channel_map
```

**Access pattern (unchanged):**
- Read-only from this service
- Queried at startup for cache initialization
- Queried on cache miss (3-tier cache: memory → file → RDS)
- Other services may write to this table (managed externally)

## Data Flow Changes

### Input Data (No Change)

| Aspect | Legacy | Rebuilt | Change |
|---|---|---|---|
| Source | SmartCast TVs via HTTP POST | SmartCast TVs via HTTP POST | None |
| Payload format | `{TvEvent: {...}, EventData: {...}}` | Same | None |
| Query params | `tvid`, `event_type` | Same | None |
| Auth | HMAC T1_SALT | HMAC T1_SALT (inline) | Implementation only |

### Output Data (Delivery Change)

| Aspect | Legacy | Rebuilt | Change |
|---|---|---|---|
| Destination | AWS Kinesis Data Firehose | Kafka topics | **Transport changed** |
| Payload format | JSON record via `send_records()` | JSON bytes via `send_message()` | Serialization format identical |
| Output fields | Flattened JSON with tvid, channelid, etc. | Same | None |
| Obfuscation | channelid, programid, channelname → "OBFUSCATED" | Same | None |
| Partitioning | N/A (Firehose has no key) | Kafka message key = tvid | **Added** — enables ordered per-device processing |

### Output Topic Mapping

| Legacy Stream | Legacy Env Var | Rebuilt Topic Env Var | Notes |
|---|---|---|---|
| Evergreen Firehose | `EVERGREEN_FIREHOSE_NAME` | `KAFKA_TOPIC_EVERGREEN` | Primary event delivery |
| Legacy Firehose | `LEGACY_FIREHOSE_NAME` | `KAFKA_TOPIC_LEGACY` | Controlled by `SEND_LEGACY` flag |
| Debug Evergreen Firehose | `DEBUG_EVERGREEN_FIREHOSE_NAME` | `KAFKA_TOPIC_DEBUG_EVERGREEN` | Active when `TVEVENTS_DEBUG=true` |
| Debug Legacy Firehose | `DEBUG_LEGACY_FIREHOSE_NAME` | `KAFKA_TOPIC_DEBUG_LEGACY` | Active when `TVEVENTS_DEBUG=true` + `SEND_LEGACY=true` |

### Downstream Consumer Impact

Downstream analytics pipelines currently read from Kinesis Firehose S3 destinations:
- `s3://cn-tvevents/<zoo>/tvevents/` (evergreen)
- `s3://cn-tvevents/<zoo>/tvevents_debug/` (debug)

**After rebuild:** Downstream consumers must be updated to consume from Kafka topics instead. The JSON payload format is identical — only the transport changes.

## Cache Data

### File Cache: `/tmp/.blacklisted_channel_ids_cache`

| Aspect | Legacy | Rebuilt | Change |
|---|---|---|---|
| Location | `BLACKLIST_CHANNEL_IDS_CACHE_FILEPATH` env var | Same env var | None |
| Format | JSON array of channel_id strings | Same | None |
| Lifecycle | Written on cache initialization and refresh | Same | None |
| Scope | Local to pod | Same | None |

### In-Memory Cache

| Aspect | Legacy | Rebuilt | Change |
|---|---|---|---|
| Storage | `TvEventsRds._blacklisted_channel_ids` (instance var) | Module-level or dependency-injected set | Implementation detail |
| Type | Set of channel_id strings | Same | None |
| Lifecycle | Populated from file cache or RDS | Same | None |

## Environment Variable Migration

### Renamed Variables

| Legacy | Rebuilt | Notes |
|---|---|---|
| `RDS_HOST` | `DB_HOST` | rds_module convention |
| `RDS_DB` | `DB_NAME` | rds_module convention |
| `RDS_USER` | `DB_USER` | rds_module convention |
| `RDS_PASS` | `DB_PASSWORD` | rds_module convention |
| `RDS_PORT` | `DB_PORT` | rds_module convention |
| `EVERGREEN_FIREHOSE_NAME` | `KAFKA_TOPIC_EVERGREEN` | Firehose → Kafka |
| `LEGACY_FIREHOSE_NAME` | `KAFKA_TOPIC_LEGACY` | Firehose → Kafka |
| `DEBUG_EVERGREEN_FIREHOSE_NAME` | `KAFKA_TOPIC_DEBUG_EVERGREEN` | Firehose → Kafka |
| `DEBUG_LEGACY_FIREHOSE_NAME` | `KAFKA_TOPIC_DEBUG_LEGACY` | Firehose → Kafka |
| `ACR_DATA_MSK_USERNAME` | `KAFKA_SASL_USERNAME` | kafka_module convention |
| `ACR_DATA_MSK_PASSWORD` | `KAFKA_SASL_PASSWORD` | kafka_module convention |
| `FLASK_ENV` | `ENV` | Framework-agnostic |

### New Variables

| Variable | Purpose | Source |
|---|---|---|
| `KAFKA_BROKERS` | Kafka bootstrap servers | Infrastructure config |
| `KAFKA_SECURITY_PROTOCOL` | SASL_SSL or PLAINTEXT | Infrastructure config |
| `KAFKA_SASL_MECHANISM` | SCRAM-SHA-256 or SCRAM-SHA-512 | Infrastructure config |
| `RDS_POOL_MIN_CONN` | Connection pool minimum (default: 1) | rds_module config |
| `RDS_POOL_MAX_CONN` | Connection pool maximum (default: 5) | rds_module config |

### Removed Variables

| Variable | Reason |
|---|---|
| `FLASK_APP` | FastAPI does not use this |
| `FLASK_ENV` | Renamed to `ENV` |
| `OTEL_PYTHON_AUTO_INSTRUMENTATION_ENABLED` | Replaced by `opentelemetry-instrument` in entrypoint |
| `WEB_CONCURRENCY` | Uvicorn uses `--workers` flag instead |

### Unchanged Variables

| Variable | Notes |
|---|---|
| `ENV` | Environment name |
| `LOG_LEVEL` | Logging verbosity |
| `SERVICE_NAME` | OTEL service name |
| `AWS_REGION` | AWS region |
| `T1_SALT` | HMAC secret |
| `BLACKLIST_CHANNEL_IDS_CACHE_FILEPATH` | File cache location |
| `SEND_EVERGREEN` | Evergreen topic toggle |
| `SEND_LEGACY` | Legacy topic toggle |
| `TVEVENTS_DEBUG` | Debug mode toggle |
| `OTEL_EXPORTER_OTLP_*` | OTEL exporter settings |
| `OTEL_PYTHON_LOG_*` | OTEL logging settings |

## Secrets Migration

| Legacy Secret | Legacy Source | Rebuilt Secret | Rebuilt Source | Notes |
|---|---|---|---|---|
| `RDS_PASS` | AWS Secrets Manager (`tvevents/tvcdb`) | `DB_PASSWORD` | AWS Secrets Manager (`tvevents/tvcdb`) | Same secret, new env var name |
| `T1_SALT` | AWS Secrets Manager (`tvevents/tvcdb`) | `T1_SALT` | AWS Secrets Manager (`tvevents/tvcdb`) | Unchanged |
| `ACR_DATA_MSK_USERNAME` | AWS Secrets Manager | `KAFKA_SASL_USERNAME` | AWS Secrets Manager (`tvevents/kafka`) | Same secret, new env var name |
| `ACR_DATA_MSK_PASSWORD` | AWS Secrets Manager | `KAFKA_SASL_PASSWORD` | AWS Secrets Manager (`tvevents/kafka`) | Same secret, new env var name |
| `OTEL_EXPORTER_OTLP_HEADERS` | AWS Secrets Manager (`inscape/o11y-config`) | `OTEL_EXPORTER_OTLP_HEADERS` | AWS Secrets Manager (`inscape/o11y-config`) | Unchanged |

## Rollback Plan

If the rebuilt service exhibits issues after deployment:

1. **Immediate:** Route traffic back to legacy service via AGA weight shifting
2. **Kafka consumers:** Repoint downstream to Firehose S3 destinations (if still active)
3. **No data loss:** Kafka topics retain messages for configured retention period; Firehose S3 data is immutable
4. **No schema changes:** Both services read from the same RDS table — no rollback needed for database
