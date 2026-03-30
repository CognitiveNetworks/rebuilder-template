#!/bin/bash

# Ideation Process Output Validator
# Checks that all expected output files exist and contain required sections.
#
# Usage:
#   ./validate.sh /path/to/rebuild-inputs/my-project          # Validate all steps
#   ./validate.sh /path/to/rebuild-inputs/my-project analyze   # Validate Steps 1-11 only
#   ./validate.sh /path/to/rebuild-inputs/my-project build     # Validate Steps 12-18 only
#
# Exit codes:
#   0 — all checks pass
#   1 — one or more checks failed

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BOLD='\033[1m'
NC='\033[0m'

if [ -z "${1:-}" ]; then
    echo "Usage: ./validate.sh /path/to/input-directory [analyze|build|all]"
    exit 1
fi

INPUT_DIR="$(cd "$1" && pwd)"
PHASE="${2:-all}"
PASS=0
FAIL=0
WARN=0

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

check_file_exists() {
    local step="$1"
    local file="$2"
    local description="$3"
    if [ -f "$INPUT_DIR/$file" ]; then
        printf "${GREEN}  ✓${NC} Step %-4s %-50s %s\n" "$step" "$description" "$file"
        PASS=$((PASS + 1))
        return 0
    else
        printf "${RED}  ✗${NC} Step %-4s %-50s %s ${RED}MISSING${NC}\n" "$step" "$description" "$file"
        FAIL=$((FAIL + 1))
        return 1
    fi
}

check_section_exists() {
    local file="$1"
    local heading="$2"
    local description="$3"
    if [ ! -f "$INPUT_DIR/$file" ]; then
        return 1
    fi
    if grep -qi "$heading" "$INPUT_DIR/$file" 2>/dev/null; then
        printf "${GREEN}    ✓${NC}   %-55s found in %s\n" "$description" "$file"
        PASS=$((PASS + 1))
        return 0
    else
        printf "${RED}    ✗${NC}   %-55s ${RED}MISSING in %s${NC}\n" "$description" "$file"
        FAIL=$((FAIL + 1))
        return 1
    fi
}

check_min_lines() {
    local file="$1"
    local min_lines="$2"
    local description="$3"
    if [ ! -f "$INPUT_DIR/$file" ]; then
        return 1
    fi
    local actual
    actual=$(wc -l < "$INPUT_DIR/$file" | tr -d ' ')
    if [ "$actual" -ge "$min_lines" ]; then
        printf "${GREEN}    ✓${NC}   %-55s %s lines (min: %s)\n" "$description" "$actual" "$min_lines"
        PASS=$((PASS + 1))
        return 0
    else
        printf "${YELLOW}    ⚠${NC}   %-55s %s lines ${YELLOW}(expected ≥%s)${NC}\n" "$description" "$actual" "$min_lines"
        WARN=$((WARN + 1))
        return 1
    fi
}

# --------------------------------------------------------------------------
# Phase 1: Analyze (Steps 1-11)
# --------------------------------------------------------------------------

validate_analyze() {
    echo ""
    printf "${BOLD}Phase 1: Analyze (Steps 1–11)${NC}\n"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Detect target language (same logic as run.sh)
    local target_lang="python"
    if [ -f "$INPUT_DIR/scope.md" ]; then
        local scope_lang
        scope_lang=$(grep -i 'Target Language' "$INPUT_DIR/scope.md" 2>/dev/null | head -1 | sed 's/.*|\s*`\?\([a-zA-Z]*\)`\?.*/\1/' | tr '[:upper:]' '[:lower:]')
        if [ -n "$scope_lang" ] && echo "$scope_lang" | grep -qE '^(python|c|go)$'; then
            target_lang="$scope_lang"
        fi
    fi
    local dev_agent="${target_lang}-developer-agent"
    local qa_agent="${target_lang}-qa-agent"

    # Step 1: Legacy Assessment
    if check_file_exists "1" "output/legacy_assessment.md" "Legacy Assessment"; then
        check_section_exists "output/legacy_assessment.md" "## Application Overview" "Application Overview section"
        check_section_exists "output/legacy_assessment.md" "## Architecture Health" "Architecture Health section"
        check_section_exists "output/legacy_assessment.md" "## Code & Dependency Health" "Code & Dependency Health section"
        check_section_exists "output/legacy_assessment.md" "## API Surface Health" "API Surface Health section"
        check_section_exists "output/legacy_assessment.md" "## Observability" "Observability section"
        check_section_exists "output/legacy_assessment.md" "## Operational Health" "Operational Health section"
        check_section_exists "output/legacy_assessment.md" "## Data Health" "Data Health section"
        check_section_exists "output/legacy_assessment.md" "## Developer Experience" "Developer Experience section"
        check_section_exists "output/legacy_assessment.md" "## Infrastructure Health" "Infrastructure Health section"
        check_section_exists "output/legacy_assessment.md" "## External Dependencies" "External Dependencies section"
        check_section_exists "output/legacy_assessment.md" "## Summary" "Summary section"
        check_min_lines "output/legacy_assessment.md" 80 "Legacy assessment minimum length"
    fi

    # Step 2: Component Overview
    if check_file_exists "2" "docs/component-overview.md" "Component Overview"; then
        check_section_exists "docs/component-overview.md" "## What Is This" "What Is This section"
        check_section_exists "docs/component-overview.md" "## Why Does It Exist" "Why Does It Exist section"
        check_section_exists "docs/component-overview.md" "## Key Concepts" "Key Concepts section"
        check_section_exists "docs/component-overview.md" "## What It Does" "What It Does section"
        check_min_lines "docs/component-overview.md" 60 "Component overview minimum length"
    fi

    # Step 3: Modernization Opportunities
    if check_file_exists "3" "output/modernization_opportunities.md" "Modernization Opportunities"; then
        check_min_lines "output/modernization_opportunities.md" 40 "Modernization opps minimum length"
    fi

    # Step 4: Feasibility Analysis
    if check_file_exists "4" "output/feasibility.md" "Feasibility Analysis"; then
        check_min_lines "output/feasibility.md" 30 "Feasibility minimum length"
    fi

    # Step 5: Rebuild Candidate(s)
    local candidate_count=0
    for f in "$INPUT_DIR"/output/candidate_*.md; do
        [ -f "$f" ] && candidate_count=$((candidate_count + 1))
    done
    if [ "$candidate_count" -gt 0 ]; then
        printf "${GREEN}  ✓${NC} Step %-4s %-50s %s file(s)\n" "5" "Rebuild Candidate(s)" "$candidate_count"
        PASS=$((PASS + 1))
    else
        printf "${RED}  ✗${NC} Step %-4s %-50s ${RED}MISSING${NC}\n" "5" "Rebuild Candidate(s) (output/candidate_*.md)"
        FAIL=$((FAIL + 1))
    fi

    # Step 6: PRD
    if check_file_exists "6" "output/prd.md" "PRD"; then
        check_section_exists "output/prd.md" "## Goals" "Goals section"
        check_section_exists "output/prd.md" "## Non-Goals" "Non-Goals section"
        check_section_exists "output/prd.md" "## Technical Approach" "Technical Approach section"
        check_section_exists "output/prd.md" "## API Design" "API Design section"
        check_section_exists "output/prd.md" "## Observability" "Observability section"
        check_section_exists "output/prd.md" "## Success Criteria" "Success Criteria section"
        check_min_lines "output/prd.md" 80 "PRD minimum length"
    fi

    # Step 7: SRE Agent Config
    check_file_exists "7" "sre-agent/skill.md" "SRE agent skill.md"
    check_file_exists "7" "sre-agent/config.md" "SRE agent config.md"

    # Step 8: Developer + QA Agent Config
    check_file_exists "8" "$dev_agent/skill.md" "Developer agent skill.md"
    check_file_exists "8" "$dev_agent/config.md" "Developer agent config.md"
    check_file_exists "8" "$qa_agent/skill.md" "QA agent skill.md"
    check_file_exists "8" "$qa_agent/config.md" "QA agent config.md"
    if [ -f "$INPUT_DIR/$qa_agent/TEST_RESULTS_TEMPLATE.md" ]; then
        check_file_exists "8" "$qa_agent/TEST_RESULTS_TEMPLATE.md" "QA TEST_RESULTS_TEMPLATE.md"
    fi

    # Step 9: ADRs
    local adr_count=0
    for f in "$INPUT_DIR"/docs/adr/0*.md; do
        [ -f "$f" ] && adr_count=$((adr_count + 1))
    done
    if [ "$adr_count" -gt 0 ]; then
        printf "${GREEN}  ✓${NC} Step %-4s %-50s %s ADR(s)\n" "9" "Architecture Decision Records" "$adr_count"
        PASS=$((PASS + 1))
    else
        printf "${RED}  ✗${NC} Step %-4s %-50s ${RED}MISSING (docs/adr/0*.md)${NC}\n" "9" "Architecture Decision Records"
        FAIL=$((FAIL + 1))
    fi

    # Step 10: Feature Parity Matrix
    if check_file_exists "10" "docs/feature-parity.md" "Feature Parity Matrix"; then
        check_section_exists "docs/feature-parity.md" "Must Rebuild\|Rebuild Improved" "Feature status labels"
        check_section_exists "docs/feature-parity.md" "## Intentionally Dropped" "Intentionally Dropped section"
        check_min_lines "docs/feature-parity.md" 30 "Feature parity minimum length"
    fi

    # Step 11: Data Migration Mapping
    check_file_exists "11" "docs/data-migration-mapping.md" "Data Migration Mapping"

    # Step 11a: Consistency check (no file — just verify cross-references)
    printf "${YELLOW}  ℹ${NC} Step %-4s %-50s %s\n" "11a" "Cross-Artifact Consistency Check" "(manual — verify terminology alignment)"
}

# --------------------------------------------------------------------------
# Phase 2: Build (Steps 12-18)
# --------------------------------------------------------------------------

validate_build() {
    echo ""
    printf "${BOLD}Phase 2: Build (Steps 12–18)${NC}\n"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Step 12: Standards Compliance Audit / TEST_RESULTS.md
    if check_file_exists "12" "tests/TEST_RESULTS.md" "TEST_RESULTS.md (quality gate report)"; then
        check_section_exists "tests/TEST_RESULTS.md" "## Core.*Gate\|## Core Gates" "Core Gates section"
        check_section_exists "tests/TEST_RESULTS.md" "## Extended.*Gate\|## Extended Gates" "Extended Gates section"
        check_section_exists "tests/TEST_RESULTS.md" "pytest\|Unit Test" "Test results present"
        check_section_exists "tests/TEST_RESULTS.md" "pylint\|Lint" "Lint results present"
        check_section_exists "tests/TEST_RESULTS.md" "black\|Format" "Format results present"
        check_section_exists "tests/TEST_RESULTS.md" "mypy\|Type Check" "Type check results present"
        check_section_exists "tests/TEST_RESULTS.md" "coverage\|Coverage" "Coverage results present"
        check_min_lines "tests/TEST_RESULTS.md" 100 "TEST_RESULTS.md minimum length"
    fi

    # Step 13: Documentation-Code Consistency (no dedicated file — README updated)
    check_file_exists "13" "README.md" "README.md (updated per Step 13)"

    # Step 14: Template Compliance Audit (optional dedicated file)
    # Some rebuilds put this in TEST_RESULTS.md, some in a separate file
    if [ -f "$INPUT_DIR/output/template-compliance-audit.md" ]; then
        printf "${GREEN}  ✓${NC} Step %-4s %-50s %s\n" "14" "Template Compliance Audit" "output/template-compliance-audit.md"
        PASS=$((PASS + 1))
    else
        printf "${YELLOW}  ⚠${NC} Step %-4s %-50s %s\n" "14" "Template Compliance Audit" "(may be in TEST_RESULTS.md)"
        WARN=$((WARN + 1))
    fi

    # Step 15: QA Agent Verification (updates TEST_RESULTS.md — check for QA markers)
    if [ -f "$INPUT_DIR/tests/TEST_RESULTS.md" ]; then
        if grep -qi "QA.*agent\|QA.*verif\|independent.*verif\|second.*pass" "$INPUT_DIR/tests/TEST_RESULTS.md" 2>/dev/null; then
            printf "${GREEN}  ✓${NC} Step %-4s %-50s %s\n" "15" "QA Agent Verification" "QA verification markers found"
            PASS=$((PASS + 1))
        else
            printf "${YELLOW}  ⚠${NC} Step %-4s %-50s ${YELLOW}No QA verification markers in TEST_RESULTS.md${NC}\n" "15" "QA Agent Verification"
            WARN=$((WARN + 1))
        fi
    fi

    # Step 16: Container Build (no file — verified in CI)
    printf "${YELLOW}  ℹ${NC} Step %-4s %-50s %s\n" "16" "Container Build" "(verified in CI — check Dockerfile exists)"
    check_file_exists "16" "Dockerfile" "Dockerfile"

    # Step 17: Process Feedback
    check_file_exists "17" "output/process-feedback.md" "Process Feedback"

    # Step 18: Summary of Work
    if check_file_exists "18" "output/summary-of-work.md" "Summary of Work"; then
        check_section_exists "output/summary-of-work.md" "## Overview" "Overview section"
        check_section_exists "output/summary-of-work.md" "### Estimated Human Time Equivalent" "Estimated Human Time section"
        check_section_exists "output/summary-of-work.md" "## Spec-Driven Approach" "Spec-Driven Approach section"
        check_section_exists "output/summary-of-work.md" "## Source Code Metrics" "Source Code Metrics section"
        check_section_exists "output/summary-of-work.md" "### Legacy Codebase" "Legacy Codebase subsection"
        check_section_exists "output/summary-of-work.md" "### Rebuilt Codebase" "Rebuilt Codebase subsection"
        check_section_exists "output/summary-of-work.md" "### Comparison" "Comparison subsection"
        check_section_exists "output/summary-of-work.md" "## Dependency Cleanup" "Dependency Cleanup section"
        check_section_exists "output/summary-of-work.md" "## Legacy Health Scorecard" "Legacy Health Scorecard section"
        check_section_exists "output/summary-of-work.md" "## New Capabilities" "New Capabilities section"
        check_section_exists "output/summary-of-work.md" "## Compliance Result" "Compliance Result section"
        check_section_exists "output/summary-of-work.md" "## Extended Quality Gate Results" "Quality Gate Results section"
        check_section_exists "output/summary-of-work.md" "## Architecture Decisions" "Architecture Decisions section"
        check_section_exists "output/summary-of-work.md" "## File Inventory" "File Inventory section"
        check_min_lines "output/summary-of-work.md" 200 "Summary-of-work minimum length"
    fi
}

# --------------------------------------------------------------------------
# Run
# --------------------------------------------------------------------------

echo ""
printf "${BOLD}Ideation Process Output Validator${NC}\n"
printf "Input directory: %s\n" "$INPUT_DIR"
printf "Phase: %s\n" "$PHASE"

case "$PHASE" in
    analyze) validate_analyze ;;
    build)   validate_build ;;
    all)     validate_analyze; validate_build ;;
    *)       echo "Unknown phase: $PHASE (use: analyze, build, or all)"; exit 1 ;;
esac

# --------------------------------------------------------------------------
# Summary
# --------------------------------------------------------------------------

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
printf "${BOLD}Results:${NC} "
printf "${GREEN}%d passed${NC}  " "$PASS"
if [ "$FAIL" -gt 0 ]; then
    printf "${RED}%d failed${NC}  " "$FAIL"
fi
if [ "$WARN" -gt 0 ]; then
    printf "${YELLOW}%d warnings${NC}  " "$WARN"
fi
echo ""

if [ "$FAIL" -gt 0 ]; then
    echo ""
    printf "${RED}${BOLD}VALIDATION FAILED${NC} — %d required output(s) missing or incomplete.\n" "$FAIL"
    echo "Fix the failures above before declaring the rebuild complete."
    exit 1
else
    if [ "$WARN" -gt 0 ]; then
        echo ""
        printf "${YELLOW}VALIDATION PASSED WITH WARNINGS${NC} — review warnings above.\n"
    else
        echo ""
        printf "${GREEN}${BOLD}VALIDATION PASSED${NC} — all required outputs present and structurally complete.\n"
    fi
    exit 0
fi
