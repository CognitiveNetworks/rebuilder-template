---
description: Populate SRE agent templates with project-specific values during rebuild Step 7
---

# Populate SRE Agent Templates

When populating `skill.md` and `config.md` for a project, follow these rules **exactly**:

## Prompting Rules

Use this prompt prefix when asking the AI to populate templates:

```
You are populating a template file with project-specific values. Follow these rules strictly:

1. PRESERVE EVERY SECTION. Do not delete, merge, skip, or summarize any section from the template. Every heading, table, list, and block must appear in the output.
2. ONLY REPLACE PLACEHOLDERS. Find text wrapped in *[brackets]* or [brackets] and replace it with the real value. Do not rewrite surrounding prose.
3. DO NOT REPHRASE. Keep all instructional comments (lines starting with ">") exactly as they are. Do not reword them.
4. DO NOT ADD SECTIONS. If the template doesn't have a section for something, don't invent one.
5. KEEP FORMATTING IDENTICAL. Markdown heading levels, table column counts, list styles, code block languages — all must match the template exactly.
6. IF A VALUE IS UNKNOWN, leave the placeholder as-is and add a TODO comment: `<!-- TODO: fill after infra provisioning -->`.
7. DIFF CHECK. After generating the output, mentally diff it against the template. The only differences should be placeholder values replaced with real values. If any structural difference exists, fix it before outputting.

The template file is: [path to template]
The project-specific values come from: [path to scope.md, input.md, or other source]
```

## Step-by-Step Process

1. Read the **template** file from `sre-agent/skill.md` or `sre-agent/config.md`
2. Read the **project source** files (`scope.md`, `input.md`, any adjacent docs)
3. Apply the prompting rules above
4. Write the populated file to `rebuild-inputs/<project>/sre-agent/skill.md` or `config.md`
5. **Verification step**: Read both the template and the output, and confirm:
   - Same number of `##` headings
   - Same number of tables
   - Same number of list items (except where a table row was a single placeholder for N services)
   - No placeholder markers remain (unless genuinely unknown → TODO)

## Common Mistakes to Watch For

- **Condensing** — the AI drops "obvious" sections like Scaling Safety or Agent Auth because it thinks they're boilerplate. They're not. Every section must be preserved.
- **Rewriting prose** — the AI rephrases instructional blockquotes to sound "better". Don't. They're part of the template contract.
- **Adding cloud expertise** — the old verbose skill.md had huge cloud knowledge sections. The condensed template intentionally omits these. Do not re-add them.
- **Merging tables** — SLO Thresholds and Scaling Limits are separate tables. Don't merge them.
- **Dropping environment variable tables** — the Runtime Configuration section must be preserved verbatim. Only the PagerDuty Integration and Service Registry values change per project.
