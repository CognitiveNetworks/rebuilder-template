# ADR-003: Use Standalone RDS Module with Connection Pooling

## Status

Accepted

## Context

The legacy `dbhelper.py` uses direct psycopg2 connections (`_connect()` / `_execute()`) without connection pooling. Each query opens and closes a connection. At high throughput (up to 500 pods in production), this creates excessive connection churn on the RDS instance. The database is used for a single read-only operation: querying blacklisted channel IDs from `tvevents_blacklisted_station_channel_map`. A standalone RDS module (`rebuilder-evergreen-rds-python`) has already been built with `ThreadedConnectionPool`, retry logic, and OTEL instrumentation.

## Decision

Replace `TvEventsRds` with the standalone `rds_module` (`rebuilder-evergreen-rds-python`). Use `rds_module.client.execute_query(sql, params)` for all database operations.

## Rationale

1. **Connection pooling** — `ThreadedConnectionPool` with configurable `RDS_POOL_MIN_CONN` / `RDS_POOL_MAX_CONN` reduces connection overhead
2. **Retry logic** — Automatic retry on `DatabaseError` / `InterfaceError` with pool reconnect (from cntools PsqlHandler pattern)
3. **OTEL instrumentation** — Tracing spans (`db.connect`, `db.query`) with semantic conventions and metrics (connection counters, query duration histogram, read/write counters) matching the legacy instrumentation
4. **Module already built** — `rds_module/client.py` (298 lines) is tested and ready
5. **Eliminates cnlib dependency** — No longer needs cntools PsqlHandler

## Environment Variable Mapping

| Legacy | Rebuilt |
|---|---|
| `RDS_HOST` | `DB_HOST` |
| `RDS_DB` | `DB_NAME` |
| `RDS_USER` | `DB_USER` |
| `RDS_PASS` | `DB_PASSWORD` |
| `RDS_PORT` | `DB_PORT` |

## Consequences

- **Positive:** Reduced connection churn, automatic retry, OTEL-instrumented queries
- **Positive:** Module is reusable across other rebuilt services
- **Negative:** Environment variable names change (requires Helm chart and Secrets Manager updates)
- **Negative:** Module is a local path dependency, not pip-installable in CI (requires `--disable=import-error` for pylint)
