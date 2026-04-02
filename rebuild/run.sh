#!/bin/bash

# Legacy Rebuild Process Runner
# Launches Cascade to execute the rebuild analysis process
#
# Usage:
#   ./run.sh /path/to/destination-repo
#
# The DESTINATION REPO is the working area. All outputs are written there.
# rebuilder-template is READ-ONLY — it provides the process definition and
# agent templates but is never modified.
#
# Before running, set up the destination repo:
#   mkdir -p /path/to/rebuilder-my-project/rebuild-inputs
#   git clone <legacy-repo-url> /path/to/rebuilder-my-project/rebuild-inputs/repo
#   git clone <template-repo-url> /path/to/rebuilder-my-project/template
#   cp scope.md /path/to/rebuilder-my-project/rebuild-inputs/scope.md
#   cp rebuild/input.md /path/to/rebuilder-my-project/rebuild-inputs/input.md
#
# For multi-repo rebuilds, clone adjacent production code repos:
#   git clone <adjacent-url> /path/to/rebuilder-my-project/rebuild-inputs/adjacent/other-app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="$(dirname "$SCRIPT_DIR")"

# Destination repo is required
if [ -z "$1" ]; then
    echo "Usage: ./run.sh /path/to/destination-repo"
    echo ""
    echo "The destination repo is the working area. Set it up first:"
    echo "  mkdir -p <dest>/rebuild-inputs"
    echo "  git clone <legacy-url> <dest>/rebuild-inputs/repo"
    echo "  git clone <template-url> <dest>/template"
    echo "  cp scope.md <dest>/rebuild-inputs/scope.md"
    echo "  cp rebuild/input.md <dest>/rebuild-inputs/input.md"
    exit 1
fi

DEST_DIR="$(cd "$1" && pwd)"
INPUT_FILE="$DEST_DIR/rebuild-inputs/input.md"
SCOPE_FILE="$DEST_DIR/rebuild-inputs/scope.md"

# Verify input files exist in the destination repo
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: input.md not found at $INPUT_FILE"
    echo "  Copy it: cp $TEMPLATE_DIR/rebuild/input.md $DEST_DIR/rebuild-inputs/input.md"
    exit 1
fi
if [ ! -f "$SCOPE_FILE" ]; then
    echo "Error: scope.md not found at $SCOPE_FILE"
    echo "  Copy it: cp $TEMPLATE_DIR/scope.md $DEST_DIR/rebuild-inputs/scope.md"
    exit 1
fi

# Detect target language from scope.md (default: python)
TARGET_LANG="python"
SCOPE_LANG=$(grep -i 'Target Language' "$SCOPE_FILE" | head -1 | sed 's/.*|\s*`\?\([a-zA-Z]*\)`\?.*/\1/' | tr '[:upper:]' '[:lower:]')
if [ -n "$SCOPE_LANG" ] && [[ "$SCOPE_LANG" =~ ^(python|c|go)$ ]]; then
    TARGET_LANG="$SCOPE_LANG"
fi
echo "Target language: $TARGET_LANG"

DEV_AGENT="${TARGET_LANG}-developer-agent"
QA_AGENT="${TARGET_LANG}-qa-agent"

# ── Clean the destination directory ──────────────────────────────────────
# Preserve .git/, rebuild-inputs/ (user's inputs + legacy repo), and template/
echo ""
echo "⚠️  Destination directory: $DEST_DIR"
echo "    Will clean all prior build artifacts (preserving .git/, rebuild-inputs/, template/)"
echo ""
read -p "    Proceed with cleanup? [y/N] " confirm
if [[ "$confirm" =~ ^[Yy]$ ]]; then
    find "$DEST_DIR" -mindepth 1 -maxdepth 1 \
        ! -name '.git' \
        ! -name 'rebuild-inputs' \
        ! -name 'template' \
        -exec rm -rf {} +
    echo "    ✅ Destination directory cleaned."
else
    echo "    ⏭  Skipping cleanup. Old files may remain."
fi

# ── Create output directories in the destination repo ────────────────────
mkdir -p "$DEST_DIR/output"
mkdir -p "$DEST_DIR/sre-agent"
mkdir -p "$DEST_DIR/docs/adr"
mkdir -p "$DEST_DIR/docs/postmortems"
mkdir -p "$DEST_DIR/$DEV_AGENT"
mkdir -p "$DEST_DIR/$QA_AGENT"

# ── Copy agent templates from rebuilder-template (read-only source) ──────
for file in skill.md config.md; do
    if [ ! -f "$DEST_DIR/sre-agent/$file" ]; then
        cp "$TEMPLATE_DIR/sre-agent/$file" "$DEST_DIR/sre-agent/$file"
    fi
done
# Copy SRE agent runtime code (critical for functionality)
if [ -d "$TEMPLATE_DIR/sre-agent/runtime" ] && [ ! -d "$DEST_DIR/sre-agent/runtime" ]; then
    cp -r "$TEMPLATE_DIR/sre-agent/runtime" "$DEST_DIR/sre-agent/"
    echo "✅ Copied SRE agent runtime code"
fi
# Add SRE agent to existing docker-compose.yml if applicable
if [ -f "$DEST_DIR/docker-compose.yml" ]; then
    PROJECT_NAME=$(grep -i "^#.*" "$DEST_DIR/prd.md" 2>/dev/null | head -1 | sed 's/^#.*//' | xargs | tr '[:upper:]' '[:lower:]')
    if [ -z "$PROJECT_NAME" ]; then
        PROJECT_NAME="app"
    fi
    "$TEMPLATE_DIR/sre-agent/add-sre-agent.sh" "$DEST_DIR" "$PROJECT_NAME"
else
    echo "📝 No docker-compose.yml found - skipping SRE agent integration"
fi
# Developer agent templates
for file in skill.md config.md; do
    if [ ! -f "$DEST_DIR/$DEV_AGENT/$file" ]; then
        cp "$TEMPLATE_DIR/$DEV_AGENT/$file" "$DEST_DIR/$DEV_AGENT/$file"
    fi
done
if [ -f "$TEMPLATE_DIR/$DEV_AGENT/.windsurfrules" ] && [ ! -f "$DEST_DIR/$DEV_AGENT/.windsurfrules" ]; then
    cp "$TEMPLATE_DIR/$DEV_AGENT/.windsurfrules" "$DEST_DIR/$DEV_AGENT/.windsurfrules"
fi
if [ -d "$TEMPLATE_DIR/$DEV_AGENT/.github" ]; then
    mkdir -p "$DEST_DIR/$DEV_AGENT/.github"
    if [ ! -f "$DEST_DIR/$DEV_AGENT/.github/copilot-instructions.md" ]; then
        cp "$TEMPLATE_DIR/$DEV_AGENT/.github/copilot-instructions.md" "$DEST_DIR/$DEV_AGENT/.github/copilot-instructions.md"
    fi
fi
# QA agent templates
for file in skill.md config.md TEST_RESULTS_TEMPLATE.md; do
    if [ -f "$TEMPLATE_DIR/$QA_AGENT/$file" ] && [ ! -f "$DEST_DIR/$QA_AGENT/$file" ]; then
        cp "$TEMPLATE_DIR/$QA_AGENT/$file" "$DEST_DIR/$QA_AGENT/$file"
    fi
done
if [ -d "$TEMPLATE_DIR/$QA_AGENT/examples" ] && [ ! -d "$DEST_DIR/$QA_AGENT/examples" ]; then
    cp -r "$TEMPLATE_DIR/$QA_AGENT/examples" "$DEST_DIR/$QA_AGENT/examples"
fi

# Copy doc templates (skip if already present)
for file in cutover-report.md disaster-recovery.md; do
    if [ ! -f "$DEST_DIR/docs/$file" ]; then
        cp "$TEMPLATE_DIR/docs/$file" "$DEST_DIR/docs/$file"
    fi
done

# ── Verify template repo exists (required) ──────────────────────────────
if [ ! -d "$DEST_DIR/template" ]; then
    echo "Warning: template/ not found at $DEST_DIR/template"
    echo "The template repo is required. Clone it: git clone <template-repo-url> $DEST_DIR/template"
fi
if [ -d "$DEST_DIR/template" ] && [ ! -f "$DEST_DIR/template/skill.md" ]; then
    echo "Warning: template/skill.md not found. The template repo may be incomplete."
fi

# ── Detect adjacent repos (optional) ────────────────────────────────────
ADJACENT_PROMPT=""
if [ -d "$DEST_DIR/rebuild-inputs/adjacent" ]; then
    ADJACENT_REPOS=""
    for dir in "$DEST_DIR/rebuild-inputs/adjacent"/*/; do
        if [ -d "$dir" ]; then
            ADJACENT_REPOS="$ADJACENT_REPOS $dir"
        fi
    done
    if [ -n "$ADJACENT_REPOS" ]; then
        ADJACENT_PROMPT=" Also read the adjacent codebases at:$ADJACENT_REPOS — these are repos that work with the primary codebase and are included in the rebuild scope. Analyze their integration points, shared state, and coupling with the primary repo as described in the process."
    fi
fi

# ── Summary ─────────────────────────────────────────────────────────────
echo ""
echo "Process definition (read-only): $TEMPLATE_DIR"
echo ""
echo "Destination repo (working area): $DEST_DIR"
echo "  Reading inputs from:"
echo "    input.md:      $INPUT_FILE"
echo "    scope.md:      $SCOPE_FILE"
if [ -d "$DEST_DIR/rebuild-inputs/repo" ]; then
    echo "    legacy repo:   $DEST_DIR/rebuild-inputs/repo/"
fi
if [ -d "$DEST_DIR/template" ]; then
    echo "    template repo: $DEST_DIR/template/"
fi
if [ -n "$ADJACENT_PROMPT" ]; then
    echo "    adjacent repos:"
    for dir in "$DEST_DIR/rebuild-inputs/adjacent"/*/; do
        [ -d "$dir" ] && echo "      $(basename "$dir"): $dir"
    done
fi
echo "  Writing outputs to:"
echo "    $DEST_DIR/output/"
echo "    $DEST_DIR/sre-agent/"
echo "    $DEST_DIR/$DEV_AGENT/"
echo "    $DEST_DIR/$QA_AGENT/"
echo "    $DEST_DIR/docs/"
echo ""

# ── Run ─────────────────────────────────────────────────────────────────
# Run from the destination repo so the agent works in the correct directory.
# The process definition is read from rebuilder-template (TEMPLATE_DIR).
# Use -p (print mode) for non-interactive execution
# Use --dangerously-skip-permissions since this is an automated analysis process
# Unset WINDSURF_SESSION to allow invocation from within another Windsurf session
(
  cd "$DEST_DIR" || exit 1
  unset WINDSURF_SESSION
  windsurf -p --dangerously-skip-permissions \
    "Read $SCRIPT_DIR/IDEATION_PROCESS.md, $INPUT_FILE, and $SCOPE_FILE. Execute the process. WORKSPACE ISOLATION: Only read from $DEST_DIR (destination repo), $DEST_DIR/rebuild-inputs/repo/ (legacy repo), $DEST_DIR/template/ (build standard), and $DEST_DIR/rebuild-inputs/adjacent/ (if present). Never read from any other rebuilder-* repo.$ADJACENT_PROMPT Write Steps 1-5 outputs to $DEST_DIR/output/. After generating the PRD (Step 6): update the SRE agent config at $DEST_DIR/sre-agent/skill.md and $DEST_DIR/sre-agent/config.md as described in Step 7, populate the developer agent config at $DEST_DIR/$DEV_AGENT/skill.md and $DEST_DIR/$DEV_AGENT/config.md as described in Step 8 (Steps 8a and 8b), then per Step 8c place the IDE instruction files (.windsurfrules and .github/copilot-instructions.md) at the repo root. CRITICAL: also copy $DEST_DIR/template/skill.md into template/skill.md and ensure .windsurfrules references it — this is the template compliance checklist (HOW TO BUILD) that must be auto-loaded every session alongside the developer agent files (HOW TO WRITE CODE). Populate the QA agent config at $DEST_DIR/$QA_AGENT/config.md as described in Step 8d — fill in project-specific test commands, env vars, event types, and acceptance criteria. Generate ADRs in $DEST_DIR/docs/adr/ as described in Step 9, generate the feature parity matrix at $DEST_DIR/docs/feature-parity.md as described in Step 10, and generate the data migration mapping at $DEST_DIR/docs/data-migration-mapping.md as described in Step 11."
)
