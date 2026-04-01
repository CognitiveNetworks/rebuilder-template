#!/bin/bash

# Legacy Rebuild Process Runner
# Launches Cascade to execute the rebuild analysis process
#
# Usage:
#   ./run.sh /path/to/inputs           # Reads from a directory containing input.md and scope.md
#
# The input directory should be created per project:
#   mkdir -p rebuild-inputs/my-project
#   git clone <legacy-repo-url> rebuild-inputs/my-project/repo
#   git clone <template-repo-url> rebuild-inputs/my-project/template
#   cp scope.md rebuild-inputs/my-project/scope.md
#   cp rebuild/input.md rebuild-inputs/my-project/input.md
#
# The template repo (build standard) goes in template/, not adjacent/.
# For multi-repo rebuilds, clone adjacent production code repos into adjacent/:
#   git clone <adjacent-repo-url> rebuild-inputs/my-project/adjacent/other-app
#
# All outputs (analysis, agent configs, ADRs) are written into the input directory,
# keeping each legacy repo's rebuild artifacts self-contained.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

# Input directory is required
if [ -z "$1" ]; then
    echo "Usage: ./run.sh /path/to/input-directory"
    echo ""
    echo "Create an input directory per project:"
    echo "  mkdir -p rebuild-inputs/my-project"
    echo "  cp scope.md rebuild-inputs/my-project/scope.md"
    echo "  cp rebuild/input.md rebuild-inputs/my-project/input.md"
    exit 1
fi

INPUT_DIR="$(cd "$1" && pwd)"
INPUT_FILE="$INPUT_DIR/input.md"
SCOPE_FILE="$INPUT_DIR/scope.md"

# Verify input files exist
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: input.md not found at $INPUT_FILE"
    exit 1
fi
if [ ! -f "$SCOPE_FILE" ]; then
    echo "Error: scope.md not found at $SCOPE_FILE"
    exit 1
fi

# Create output directories inside the input directory
mkdir -p "$INPUT_DIR/output"
mkdir -p "$INPUT_DIR/sre-agent"
mkdir -p "$INPUT_DIR/docs/adr"
mkdir -p "$INPUT_DIR/docs/postmortems"

# Detect target language from scope.md (default: python)
TARGET_LANG="python"
SCOPE_LANG=$(grep -i 'Target Language' "$SCOPE_FILE" | head -1 | sed 's/.*|\s*`\?\([a-zA-Z]*\)`\?.*/\1/' | tr '[:upper:]' '[:lower:]')
if [ -n "$SCOPE_LANG" ] && [[ "$SCOPE_LANG" =~ ^(python|c|go)$ ]]; then
    TARGET_LANG="$SCOPE_LANG"
fi
echo "Target language: $TARGET_LANG"

DEV_AGENT="${TARGET_LANG}-developer-agent"
QA_AGENT="${TARGET_LANG}-qa-agent"

mkdir -p "$INPUT_DIR/$DEV_AGENT"
mkdir -p "$INPUT_DIR/$QA_AGENT"

# Copy template agent configs into the project directory (skip if already present)
for file in skill.md config.md; do
    if [ ! -f "$INPUT_DIR/sre-agent/$file" ]; then
        cp "$REPO_DIR/sre-agent/$file" "$INPUT_DIR/sre-agent/$file"
    fi
done
# Copy SRE agent runtime code (critical for functionality)
if [ -d "$REPO_DIR/sre-agent/runtime" ] && [ ! -d "$INPUT_DIR/sre-agent/runtime" ]; then
    cp -r "$REPO_DIR/sre-agent/runtime" "$INPUT_DIR/sre-agent/"
    echo "✅ Copied SRE agent runtime code"
fi
# Add SRE agent to existing docker-compose.yml if applicable
if [ -f "$INPUT_DIR/docker-compose.yml" ]; then
    # Extract project name from PRD for service registry
    PROJECT_NAME=$(grep -i "^#.*" "$INPUT_DIR/prd.md" | head -1 | sed 's/^#.*//' | xargs | tr '[:upper:]' '[:lower:]')
    if [ -z "$PROJECT_NAME" ]; then
        PROJECT_NAME="app"
    fi
    
    # Add SRE agent service to docker-compose.yml
    "$REPO_DIR/sre-agent/add-sre-agent.sh" "$INPUT_DIR" "$PROJECT_NAME"
else
    echo "📝 No docker-compose.yml found - skipping SRE agent integration"
fi
for file in skill.md config.md; do
    if [ ! -f "$INPUT_DIR/$DEV_AGENT/$file" ]; then
        cp "$REPO_DIR/$DEV_AGENT/$file" "$INPUT_DIR/$DEV_AGENT/$file"
    fi
done
# Copy .windsurfrules template (goes into the built repo root at deploy time)
if [ -f "$REPO_DIR/$DEV_AGENT/.windsurfrules" ] && [ ! -f "$INPUT_DIR/$DEV_AGENT/.windsurfrules" ]; then
    cp "$REPO_DIR/$DEV_AGENT/.windsurfrules" "$INPUT_DIR/$DEV_AGENT/.windsurfrules"
fi
# Copy .github/copilot-instructions.md template (for VS Code + GitHub Copilot users)
if [ -d "$REPO_DIR/$DEV_AGENT/.github" ]; then
    mkdir -p "$INPUT_DIR/$DEV_AGENT/.github"
    if [ ! -f "$INPUT_DIR/$DEV_AGENT/.github/copilot-instructions.md" ]; then
        cp "$REPO_DIR/$DEV_AGENT/.github/copilot-instructions.md" "$INPUT_DIR/$DEV_AGENT/.github/copilot-instructions.md"
    fi
fi
# Copy QA agent templates (skill.md, config.md, and any additional files)
for file in skill.md config.md TEST_RESULTS_TEMPLATE.md; do
    if [ -f "$REPO_DIR/$QA_AGENT/$file" ] && [ ! -f "$INPUT_DIR/$QA_AGENT/$file" ]; then
        cp "$REPO_DIR/$QA_AGENT/$file" "$INPUT_DIR/$QA_AGENT/$file"
    fi
done
if [ -d "$REPO_DIR/$QA_AGENT/examples" ] && [ ! -d "$INPUT_DIR/$QA_AGENT/examples" ]; then
    cp -r "$REPO_DIR/$QA_AGENT/examples" "$INPUT_DIR/$QA_AGENT/examples"
fi

# Copy doc templates that are filled out later (skip if already present)
for file in cutover-report.md disaster-recovery.md; do
    if [ ! -f "$INPUT_DIR/docs/$file" ]; then
        cp "$REPO_DIR/docs/$file" "$INPUT_DIR/docs/$file"
    fi
done
# feature-parity.md and data-migration-mapping.md are generated by Steps 10-11

# Verify template repo exists (required)
if [ ! -d "$INPUT_DIR/template" ]; then
    echo "Warning: template/ not found at $INPUT_DIR/template"
    echo "The template repo is required. Clone it: git clone <template-repo-url> $INPUT_DIR/template"
fi
if [ -d "$INPUT_DIR/template" ] && [ ! -f "$INPUT_DIR/template/skill.md" ]; then
    echo "Warning: template/skill.md not found. The template repo may be incomplete."
fi

# Detect adjacent repos (optional — for multi-repo rebuilds)
ADJACENT_PROMPT=""
if [ -d "$INPUT_DIR/adjacent" ]; then
    ADJACENT_REPOS=""
    for dir in "$INPUT_DIR/adjacent"/*/; do
        if [ -d "$dir" ]; then
            ADJACENT_REPOS="$ADJACENT_REPOS $dir"
        fi
    done
    if [ -n "$ADJACENT_REPOS" ]; then
        ADJACENT_PROMPT=" Also read the adjacent codebases at:$ADJACENT_REPOS — these are repos that work with the primary codebase and are included in the rebuild scope. Analyze their integration points, shared state, and coupling with the primary repo as described in the process."
    fi
fi

echo "Reading inputs from:"
echo "  input.md: $INPUT_FILE"
echo "  scope.md: $SCOPE_FILE"
if [ -d "$INPUT_DIR/template" ]; then
    echo "  template repo: $INPUT_DIR/template/"
fi
if [ -n "$ADJACENT_PROMPT" ]; then
    echo "  adjacent repos:"
    for dir in "$INPUT_DIR/adjacent"/*/; do
        [ -d "$dir" ] && echo "    $(basename "$dir"): $dir"
    done
fi
echo ""
echo "Writing outputs to:"
echo "  $INPUT_DIR/output/"
echo "  $INPUT_DIR/sre-agent/"
echo "  $INPUT_DIR/$DEV_AGENT/"
echo "  $INPUT_DIR/$QA_AGENT/"
echo "  $INPUT_DIR/docs/"
echo ""

# Run from the repo root so the CLI can access both rebuild/ and rebuild-inputs/
# Use -p (print mode) for non-interactive execution
# Use --dangerously-skip-permissions since this is an automated analysis process
# Unset WINDSURF_SESSION to allow invocation from within another Windsurf session
(
  cd "$REPO_DIR" || exit 1
  unset WINDSURF_SESSION
  windsurf -p --dangerously-skip-permissions \
    "Read $SCRIPT_DIR/IDEATION_PROCESS.md, $INPUT_FILE, and $SCOPE_FILE. Execute the process.$ADJACENT_PROMPT Write Steps 1-5 outputs to $INPUT_DIR/output/. After generating the PRD (Step 6): update the SRE agent config at $INPUT_DIR/sre-agent/skill.md and $INPUT_DIR/sre-agent/config.md as described in Step 7, populate the developer agent config at $INPUT_DIR/$DEV_AGENT/skill.md and $INPUT_DIR/$DEV_AGENT/config.md as described in Step 8 (Steps 8a and 8b), then per Step 8c place the IDE instruction files (.windsurfrules and .github/copilot-instructions.md) AND the populated $DEV_AGENT/skill.md and $DEV_AGENT/config.md inside the built repository directory so developers get auto-loaded configs when they clone and open the repo in any IDE. CRITICAL: also copy $INPUT_DIR/template/skill.md into the built repo at <repo>/template/skill.md and ensure .windsurfrules references it — this is the template compliance checklist (HOW TO BUILD) that must be auto-loaded every session alongside the developer agent files (HOW TO WRITE CODE). Populate the QA agent config at $INPUT_DIR/$QA_AGENT/config.md as described in Step 8d — fill in project-specific test commands, env vars, event types, and acceptance criteria, then copy the populated $QA_AGENT/ directory into the built repo. Generate ADRs in $INPUT_DIR/docs/adr/ as described in Step 9, generate the feature parity matrix at $INPUT_DIR/docs/feature-parity.md as described in Step 10, and generate the data migration mapping at $INPUT_DIR/docs/data-migration-mapping.md as described in Step 11."
)
