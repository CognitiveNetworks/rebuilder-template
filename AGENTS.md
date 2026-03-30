# Rebuilder Template — Agent Instructions

This is the rebuilder template repository. It contains agent configurations,
development standards, and the ideation process for rebuilding legacy Evergreen
services as modern applications in Python, C, or Go.

## Required Context

Before writing any code, making any changes, or answering any questions about
this project, read the agent files for the **target language**. The target
language is determined by the PRD or `scope.md`.

### Developer Agents (development standards)

| Language | skill.md | config.md |
|---|---|---|
| Python | `python-developer-agent/skill.md` | `python-developer-agent/config.md` |
| C | `c-developer-agent/skill.md` | `c-developer-agent/config.md` |
| Go | `go-developer-agent/skill.md` | `go-developer-agent/config.md` |

### QA Agents (quality verification)

| Language | skill.md | config.md |
|---|---|---|
| Python | `python-qa-agent/skill.md` | `python-qa-agent/config.md` |
| C | `c-qa-agent/skill.md` | `c-qa-agent/config.md` |
| Go | `go-qa-agent/skill.md` | `go-qa-agent/config.md` |

The QA agent verifies the developer agent's output — it does not replace it.

Do not proceed with any task until the relevant agent files have been read.

## Performance Agent

The performance agent (`performance-agent/`) provides specialized Python
profiling and optimization capabilities. It is loaded on demand — not
always-on like the developer and QA agents. Reference
`performance-agent/skill.md` and `performance-agent/config.md` when
investigating latency, memory, or throughput issues.

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
