# Rebuilder Template — Agent Instructions

This is the rebuilder template repository. It contains agent configurations,
development standards, and the ideation process for rebuilding legacy Evergreen
services as modern Python applications.

## Required Context

Before writing any code, making any changes, or answering any questions about
this project, read these four files in full:

### Developer Agent (development standards)

1. `developer-agent/skill.md` — development standards, coding practices,
   testing expectations, CI/CD pipeline structure, service bootstrap checklist,
   and observability requirements.
2. `developer-agent/config.md` — project-specific configuration: commands,
   environments, services, secrets references, and SRE agent integration.

### QA Agent (quality verification)

3. `qa-agent/skill.md` — QA standards, quality gates, test strategy,
   acceptance criteria, and verification procedures. The QA agent verifies
   the developer agent's output — it does not replace it.
4. `qa-agent/config.md` — project-specific QA configuration: test commands,
   thresholds, env var mapping, mock strategy, and acceptance criteria.

Do not proceed with any task until all four files have been read.

## SRE Agent

The SRE agent (`sre-agent/`) is a runtime operational agent. It is not loaded
during development or rebuild sessions. It is populated during the ideation
process (Step 7) and deployed alongside the built service.

## Rebuild Process

To run the legacy rebuild process, use the `/run-replicator` workflow in
Windsurf or invoke the `@legacy-rebuild` skill. See `rebuild/IDEATION_PROCESS.md`
for the full process definition.

## IDE Support

| IDE | Bootstrap Mechanism | Auto-loaded |
|---|---|---|
| Windsurf | `.windsurfrules` | Yes — every session |
| VS Code + GitHub Copilot | `.github/copilot-instructions.md` | Yes — every Copilot Chat |
| Other tools | This `AGENTS.md` file | Depends on tool support |
