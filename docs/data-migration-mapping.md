# Data Migration Mapping

> Schema and key-pattern mapping between the legacy application and the target system.
> Every table, column, key pattern, and transformation is documented here.
>
> Fill this out during migration planning. See `STANDARDS.md` > Data Migration & Validation for requirements.

## Migration Strategy

> Describe the phased migration approach — e.g., compatibility layer first, then
> gradual DAPR migration, then full cutover. Reference which phases from the
> feature parity matrix map to which migration stages.

*[Describe migration phases here]*

## Data Store Inventory

> Summary of every data store the legacy application touches. List before writing
> detailed per-store mappings below.

| # | Store | Type | Legacy Location | Target | Migration Phase |
|---|---|---|---|---|---|
| | | | | | |

## Relational Databases

> One section per relational database. Use the table-and-column mapping format.

### Source: *[Legacy Database]*

| Legacy Table | Legacy Column | Type | Target Table | Target Column | Type | Transformation |
|---|---|---|---|---|---|---|
| | | | | | | |

#### Mapping Notes

- *[Document any schema changes, type conversions, or data transformations]*
- *[Note columns that are intentionally dropped and why]*
- *[Note new columns in the target that have no legacy equivalent]*

## Key-Value / Document Stores

> One section per key-value store (Redis, Memcache, DynamoDB, etc.).
> Use the key-pattern mapping format.

### Key Pattern Migration — *[Store Name]*

| # | Key Pattern | Example | Data Type | TTL | DAPR Capable? | Migration Approach |
|---|---|---|---|---|---|---|
| | | | | | | |

#### Special Operations

> Document Lua scripts, atomic operations, pipeline batches, or other operations
> that cannot be expressed as simple key-value CRUD.

- *[Operation name — what it does, why it exists, code snippet if critical]*

#### DAPR Component

```yaml
# Paste the DAPR component YAML for this store
```

## Other Data Stores

> S3/GCS buckets, message queues, streaming sources, etc.

### *[Store Name]*

| Legacy Mechanism | Target Mechanism | Migration Approach |
|---|---|---|
| | | |

## Environment Variables for Data Store Configuration

> Document every connection string, DSN, host/port, and credential env var.

| Env Var | Purpose | Default (local dev) |
|---|---|---|
| | | |

## Migration Validation Checklist

> Run these checks against both legacy and target to confirm migration correctness.

- [ ] *[Store]: [specific validation criterion]*
- [ ] *[Store]: [specific validation criterion]*

## Edge Cases

- *[Null handling — how are legacy nulls treated in the target?]*
- *[Encoding — character set conversions, timezone handling]*
- *[Truncation — fields that change max length]*
- *[Include code snippets for any logic that must be preserved exactly during migration]*
