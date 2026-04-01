# IDE Compatibility

The rebuilder template supports multiple IDEs through layered bootstrap mechanisms. Each mechanism points to the same canonical agent files (`{lang}-developer-agent/skill.md`, `{lang}-developer-agent/config.md`, `{lang}-qa-agent/skill.md`, `{lang}-qa-agent/config.md`).

| IDE | Bootstrap File | Auto-loaded | Notes |
|---|---|---|---|
| **Windsurf** | `.windsurfrules` | Yes — every session | Also discovers `AGENTS.md` and `.windsurf/skills/` |
| **VS Code + GitHub Copilot** | `.github/copilot-instructions.md` | Yes — every Copilot Chat | Reads agent files on demand |
| **Other tools** | `AGENTS.md` | Depends on tool support | Cross-tool standard; adopted by Claude Code and others |

---

## Windsurf

Windsurf users get the most integrated experience through the `.windsurf/` directory.

### Skills

`.windsurf/skills/` — Progressive disclosure: only the skill name and description are in the system prompt. Full content loads on demand. The `@legacy-rebuild` skill wraps the 90KB ideation process so it never occupies context unless invoked.

### Workflows

`.windsurf/workflows/` — Manual slash commands:

| Command | What it does |
|---|---|
| `/run-replicator` | Invokes `@legacy-rebuild` skill — starts the 18-step rebuild process |
| `/qa` | Runs all quality gates and generates an independent verification report |
| `/developer` | Reloads all developer + QA agent files mid-session |
| `/populate-templates` | Populates SRE agent templates with project-specific values (Step 7) |

### Rules

`.windsurfrules` at the repo root is always-on. `AGENTS.md` at the root is treated as an always-on rule.

---

## VS Code + GitHub Copilot

`.github/copilot-instructions.md` is auto-included in every Copilot Chat interaction. It instructs Copilot to read the developer and QA agent files on every session.

VS Code does not support Windsurf's `/run-replicator` workflow or `@legacy-rebuild` skill. Reference the process file directly:

> *"Read rebuild/IDEATION_PROCESS.md and rebuild my-service."*

---

## Windsurf Enterprise

For organizations on Windsurf Enterprise, system-level Skills and Rules can be deployed to all workspaces via IT-managed paths:

| OS | Skills Path | Rules Path |
|---|---|---|
| macOS | `/Library/Application Support/Windsurf/skills/` | `/Library/Application Support/Windsurf/rules/` |
| Linux/WSL | `/etc/windsurf/skills/` | `/etc/windsurf/rules/` |
| Windows | `C:\ProgramData\Windsurf\skills\` | `C:\ProgramData\Windsurf\rules\` |

This allows org-wide development standards to be enforced as read-only rules that individual developers cannot override. Project-specific config (`config.md`) remains at the workspace level.

---

## Cursor

Cursor IDE support (`.cursorrules`) is not currently included in this template. Cursor users can manually read the agent files or use `AGENTS.md` if their tool supports it. Adding `.cursorrules` is a future consideration — contributions welcome.
