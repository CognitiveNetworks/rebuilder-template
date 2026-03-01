# Spec Debt Tracker

> This file tracks divergences between the PRD (the spec) and the actual codebase.
> Every human code edit that changes behavior not captured in the PRD is spec debt.
>
> The spec-impact CI check appends entries here automatically when human PRs merge.
> Before a regeneration or language port, this file is read and its entries are
> reconciled into the PRD — closing the gap between spec and code.
>
> **Goal:** This file trends toward empty. Each entry either gets absorbed into
> the PRD (making the spec more precise) or gets tagged with `@spec-lock` (marking
> the code as authoritative for that requirement).

## Format

Each entry is added by the spec-impact GitHub Action on PR merge:

```
### [PR #NNN] — [PR title]
**Merged:** YYYY-MM-DD
**Author:** @github-username

| Changed File | PRD Section | What Changed | Why |
|---|---|---|---|
| [file] | [§N.N section] | [behavioral change] | [engineer's explanation] |

**Resolution:**
- [ ] Absorbed into PRD (update §N.N with the corrected behavior)
- [ ] Tagged with `@spec-lock` (code is authoritative — spec cannot express this)
- [ ] No action needed (cosmetic / refactor with no behavioral change)
```

## Active Debt

<!-- Entries are appended here by the spec-impact action on PR merge. -->
<!-- When an entry is resolved, move it to the Resolved section below. -->

## Resolved

<!-- Entries that have been absorbed into the PRD or tagged with @spec-lock. -->
<!-- Keep resolved entries for audit trail. -->
