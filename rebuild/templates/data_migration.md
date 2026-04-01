# Data Migration Mapping

> Schema mapping between the legacy application and the target system.

## Source: [Legacy Database Engine and Name]

| Legacy Table | Legacy Column | Type | Target Table | Target Column | Type | Transformation |
|---|---|---|---|---|---|---|
| [table] | [column] | [type] | [table] | [column] | [type] | [description or "direct copy"] |

## Mapping Notes

- [Schema changes, type conversions, or data transformations]
- [Columns intentionally dropped and why]
- [New columns in the target that have no legacy equivalent]

## Edge Cases

- [Null handling — how are legacy nulls treated in the target?]
- [Encoding — character set conversions, timezone handling]
- [Truncation — fields that change max length]
- [Default values — what fills new required columns for migrated rows?]

## Reconciliation Queries

> Queries to validate data integrity after migration.

| Check | Legacy Query | Target Query | Expected |
|---|---|---|---|
| Total row count per table | [query] | [query] | Match |
| [additional checks] | [query] | [query] | [expected result] |
