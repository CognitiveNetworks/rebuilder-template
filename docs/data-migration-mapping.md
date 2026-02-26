# Data Migration Mapping

> Schema mapping between the legacy application and the target system. Every table, column, and transformation is documented here.
>
> Fill this out during migration planning. See `WINDSURF.md` > Data Migration & Validation for requirements.

## Source: [Legacy Database]

| Legacy Table | Legacy Column | Type | Target Table | Target Column | Type | Transformation |
|---|---|---|---|---|---|---|
| | | | | | | |

## Mapping Notes

- [Document any schema changes, type conversions, or data transformations]
- [Note columns that are intentionally dropped and why]
- [Note new columns in the target that have no legacy equivalent]

## Edge Cases

- [Null handling — how are legacy nulls treated in the target?]
- [Encoding — character set conversions, timezone handling]
- [Truncation — fields that change max length]

## Reconciliation Queries

> Queries to validate data integrity after migration. Run these against both legacy and target databases.

| Check | Legacy Query | Target Query | Expected |
|---|---|---|---|
| Row count | | | Match |
| | | | |
