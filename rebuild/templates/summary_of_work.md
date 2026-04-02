# Summary of Work: [Application Name]

> **Reference document.** This is a summary generated during the ideation process. It informs decisions but does not override {lang}-developer-agent/skill.md.

## Overview

[Two-column layout using an HTML table. Left column (55%) contains the 3
executive summary paragraphs. Right column (45%) contains the Key Numbers table.
This keeps the narrative and metrics side-by-side so executives see both at a
glance without scrolling.]

<table>
<tr>
<td width="55%" valign="top">

[Paragraph 1: What the legacy application was, its problems, and why it needed
rebuilding.]

[Paragraph 2: How the rebuild was executed (spec-driven automated process).]

[Paragraph 3 ("Bottom line"): Synthesize three things for a non-technical reader:
(1) how long the rebuild would take a human engineer, (2) how long it actually
took with AI-driven automation, and (3) why the rebuilt codebase is more
maintainable going forward (reduced lines, type safety, automated quality gates,
observability, CI/CD enforcement).]

</td>
<td width="45%" valign="top">

**Key Numbers**

[Summary table of headline metrics. Measure programmatically — do not estimate.]

| Metric | Value |
|--------|-------|
| Source lines eliminated | [n] |
| Source code reduction | [n%] |
| ... | ... |
| Total files delivered | [n] |

</td>
</tr>
</table>

### Estimated Human Time Equivalent

[Two engineer profiles: a senior engineer already familiar with the legacy
codebase ("Familiar Engineer") and an engineer new to the codebase
("Unfamiliar Engineer"). Both assume full-time work (8h days). This dual-column
format is required for every rebuild.]

| Phase | Deliverables | Familiar Engineer | Unfamiliar Engineer | Basis |
|-------|-------------|-------------------|---------------------|-------|
| **Legacy analysis** (Steps 1–3) | [artifacts] | **[n–n days]** | **[n–n days]** | [justification with LOC counts, file counts, domain complexity¹] |
| **Architecture & design** (Steps 4–8) | [artifacts] | **[n–n days]** | **[n–n days]** | [justification citing ADR count, PRD complexity²] |
| **Feature parity & data mapping** (Steps 9–10) | [artifacts] | **[n–n days]** | **[n–n days]** | [justification citing feature count, data complexity] |
| **Implementation** | [file/line/module count] | **[n–n days]** | **[n–n days]** | [justification citing production LOC³] |
| **Testing** | [test file/count/gate count] | **[n–n days]** | **[n–n days]** | [justification citing test LOC, fixture complexity⁴] |
| **Compliance & docs** (Steps 11–16) | [audit scope, doc count] | **[n–n days]** | **[n–n days]** | [justification citing compliance check count] |
| **Total** | **[total files]** | **[n–n days]** | **[n–n days]** | **[~n–n weeks (familiar) / ~n–n weeks (unfamiliar)]** |

[After the table, state:]
- The AI-driven pipeline compressed this into [timeframe] of human oversight
- **Estimated acceleration:** [n–n×] for familiar, [n–n×] for unfamiliar
- Human role shifted from execution to review and judgment

> ¹ McConnell, Steve. *Code Complete* (2004), Ch. 20 — code review rates and unfamiliarity overhead.
> ² Jones, Capers. *Applied Software Measurement* (2008) — architectural decision productivity and domain familiarity impact.
> ³ Jones, Capers. *Applied Software Measurement* (2008) — lines per day for experienced (100–150) vs. unfamiliar (50–80) engineers.
> ⁴ Meszaros, Gerard. *xUnit Test Patterns* (2007) — test design effort multiplier for services with external dependencies.

## Spec-Driven Approach

| Step | Name | Output |
|---|---|---|
| 1 | Legacy Assessment | output/legacy_assessment.md |
| 2 | Component Overview | docs/component-overview.md |
| ... | ... | ... |

## Source Code Metrics

### Legacy Codebase
| Metric | Value |
|---|---|
| Source files | [count from repo/ and adjacent/] |
| Total lines | [count] |
| Test files | [count] |
| Test lines | [count] |

### Rebuilt Codebase
| Metric | Value |
|---|---|
| Source files | [count] |
| Total lines | [count] |
| Test files | [count] |
| Test lines | [count] |

### Comparison
| Metric | Legacy | Rebuilt | Change |
|---|---|---|---|
| Source files | [n] | [n] | [% change] |
| Source lines | [n] | [n] | [% change] |
| Test files | [n] | [n] | [% change] |
| Largest file (lines) | [name: n] | [name: n] | [comparison] |

## Dependency Cleanup

### Removed
| Dependency | Issue | Replacement |
|---|---|---|
| [name] | [reason] | [replacement — **never leave blank**; state "No replacement needed (dead code)" if applicable] |

### Current
| Dependency | Version | Purpose |
|---|---|---|
| [name] | [version] | [what it does] |

| Metric | Legacy | Rebuilt |
|---|---|---|
| Runtime dependencies | [n] | [n] |
| Pinned versions | [Yes/No] | [Yes/No] |

## Legacy Health Scorecard

| Dimension | Rating |
|---|---|
| Architecture Health | [rating] |
| API Surface Health | [rating] |
| Observability & SRE | [rating] |
| Auth & Access Control | [rating] |
| Code & Dependency Health | [rating] |
| Operational Health | [rating] |
| Data Health | [rating] |
| Developer Experience | [rating] |
| Infrastructure Health | [rating] |
| External Dependencies | [rating] |

## New Capabilities

| Capability | Legacy | Rebuilt |
|---|---|---|
| HTTP API | [status] | [status] |
| OpenAPI Spec | [status] | [status] |
| Structured Logging | [status] | [status] |
| Distributed Tracing | [status] | [status] |
| Health Checks | [status] | [status] |
| Container Image | [status] | [status] |
| Infrastructure as Code | [status] | [status] |
| CI/CD Pipeline | [status] | [status] |
| SRE Diagnostic Endpoints | [status] | [status] |
| [additional capabilities] | ... | ... |

## Compliance Result

| Category | Checks | Passed | Failed |
|---|---|---|---|
| [category] | [n] | [n] | [n] |
| **Total** | **[n]** | **[n]** | **[n]** |

## Extended Quality Gate Results

**Core Gates (all must pass):**

| Gate | Tool | Threshold | Result | Status |
|---|---|---|---|---|
| Unit Tests | pytest | 0 failures | [n passed, n failed] | [PASS/FAIL] |
| Lint | pylint | 0 errors | [n errors] | [PASS/FAIL] |
| Format | black | 0 unformatted | [n/n formatted] | [PASS/FAIL] |
| Type Check | mypy (strict) | 0 errors | [n errors in n files] | [PASS/FAIL] |

**Extended Gates (measured baselines):**

| Gate | Tool | Threshold | Result | Status |
|---|---|---|---|---|
| Test Coverage | pytest-cov | measured | [n% overall] | [MEASURED] |
| Dependency Vulnerabilities | pip-audit | 0 critical/high | [n CVEs] | [PASS/FLAGGED] |
| Docstring Coverage | interrogate | measured | [n%] | [MEASURED] |
| Duplicate Code (DRY) | pylint + jscpd | < 3% duplication | [n% duplication] | [PASS/FAIL] |
| Cognitive Complexity | complexipy | 0 issues | [n issues] | [PASS/FAIL] |

[Brief notes on coverage gaps, flagged vulnerabilities, justified exceptions.]

**Full machine-verified output:** [`tests/TEST_RESULTS.md`](../[built-repo]/tests/TEST_RESULTS.md)

## Architecture Decisions

| ADR | Title | Decision | Key Trade-off |
|---|---|---|---|
| 001 | [title] | [chosen option] | [what was traded] |

## File Inventory

[Tree view of all delivered files, organized by category.]

### Source
[file tree]

### Tests
[file tree]

### Infrastructure
[file tree]

### Documentation
[file tree]
