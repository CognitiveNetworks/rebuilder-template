# ADR-006: Use PostgreSQL via RDS

## Status

Accepted

## Context

The legacy application uses PostgreSQL on AWS RDS for a single read-only operation: querying blacklisted channel IDs from the `tvevents_blacklisted_station_channel_map` table. The database schema is managed externally and shared with other services. There is no reason to change the database engine.

## Decision

Continue using PostgreSQL on AWS RDS. Access via the standalone `rds_module` with connection pooling (see ADR-003).

## Rationale

1. **Same engine** — No data migration needed; the rebuilt service reads from the same table
2. **Simple access pattern** — Single SELECT DISTINCT query, cached in memory and file
3. **Shared resource** — Other services depend on this table; changing engines would affect them
4. **rds_module provides pooling** — The new client adds connection pooling without changing the database

## Consequences

- **Positive:** Zero data migration, same query, same results
- **Positive:** Connection pooling reduces load on RDS instance
- **Negative:** PostgreSQL-specific SQL (minimal — only one query)
