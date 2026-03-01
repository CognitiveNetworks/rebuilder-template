#!/usr/bin/env bash
# scan-spec-locks.sh — Extract @spec-lock annotations from any codebase
#
# Produces spec-locks.yaml with all locked blocks, their contracts, reasons,
# and file locations. Language-agnostic: matches @spec-lock / @end-spec-lock
# in any comment style (#, //, /* */, --, <!--).
#
# Usage:
#   ./scripts/scan-spec-locks.sh [directory]
#   ./scripts/scan-spec-locks.sh src/
#   ./scripts/scan-spec-locks.sh .          # scan entire repo
#
# Output: spec-locks.yaml in the current directory

set -euo pipefail

SCAN_DIR="${1:-.}"
OUTPUT_FILE="spec-locks.yaml"

# Validate directory exists
if [[ ! -d "$SCAN_DIR" ]]; then
  echo "Error: directory '$SCAN_DIR' does not exist" >&2
  exit 1
fi

# Find all files containing @spec-lock (skip binary, .git, node_modules, __pycache__)
LOCK_FILES=$(grep -rl '@spec-lock' "$SCAN_DIR" \
  --include='*.py' --include='*.js' --include='*.ts' --include='*.go' \
  --include='*.java' --include='*.rb' --include='*.rs' --include='*.c' \
  --include='*.cpp' --include='*.h' --include='*.cs' --include='*.kt' \
  --include='*.swift' --include='*.sh' --include='*.yaml' --include='*.yml' \
  2>/dev/null || true)

if [[ -z "$LOCK_FILES" ]]; then
  echo "# spec-locks.yaml (auto-generated — do not edit)" > "$OUTPUT_FILE"
  echo "# Scanned: $SCAN_DIR" >> "$OUTPUT_FILE"
  echo "# Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUTPUT_FILE"
  echo "locks: []" >> "$OUTPUT_FILE"
  echo "No @spec-lock annotations found in $SCAN_DIR"
  exit 0
fi

# Begin YAML output
cat > "$OUTPUT_FILE" << HEADER
# spec-locks.yaml (auto-generated — do not edit)
# Scanned: $SCAN_DIR
# Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
locks:
HEADER

LOCK_COUNT=0
ERROR_COUNT=0

while IFS= read -r file; do
  # Extract spec-lock blocks using awk
  # Matches: @spec-lock §SECTION LOCK-ID on the opening tag
  # Reads contract:, raises:, reason: fields from subsequent comment lines
  # Identifies the function/class name on the first non-comment line after metadata
  awk -v file="$file" '
    /^[[:space:]]*(#|\/\/|\/\*|\*|--|<!--)[[:space:]]*@spec-lock / {
      in_lock = 1
      # Extract spec section and lock ID from the tag line
      match($0, /@spec-lock[[:space:]]+§([^[:space:]]+)[[:space:]]+([^[:space:]]+)/, parts)
      if (RSTART > 0) {
        spec_section = parts[1]
        lock_id = parts[2]
      } else {
        # Fallback: try simpler extraction
        gsub(/.*@spec-lock[[:space:]]+§/, "", $0)
        split($0, tag_parts, /[[:space:]]+/)
        spec_section = tag_parts[1]
        lock_id = tag_parts[2]
      }
      contract = ""
      raises = ""
      reason = ""
      func_name = ""
      lock_line = NR
      next
    }

    in_lock && /^[[:space:]]*(#|\/\/|\/\*|\*|--|<!--)[[:space:]]*contract:/ {
      sub(/^[[:space:]]*(#|\/\/|\/\*|\*|--|<!--)[[:space:]]*contract:[[:space:]]*/, "")
      contract = $0
      next
    }

    in_lock && /^[[:space:]]*(#|\/\/|\/\*|\*|--|<!--)[[:space:]]*raises:/ {
      sub(/^[[:space:]]*(#|\/\/|\/\*|\*|--|<!--)[[:space:]]*raises:[[:space:]]*/, "")
      raises = $0
      next
    }

    in_lock && /^[[:space:]]*(#|\/\/|\/\*|\*|--|<!--)[[:space:]]*reason:/ {
      sub(/^[[:space:]]*(#|\/\/|\/\*|\*|--|<!--)[[:space:]]*reason:[[:space:]]*/, "")
      reason = $0
      # Collect multi-line reasons (indented continuation lines)
      next
    }

    # Multi-line reason continuation (indented comment lines after reason:)
    in_lock && reason != "" && func_name == "" && /^[[:space:]]*(#|\/\/|\/\*|\*|--|<!--)[[:space:]]+[^@]/ {
      sub(/^[[:space:]]*(#|\/\/|\/\*|\*|--|<!--)[[:space:]]*/, "")
      if ($0 !~ /^(contract|raises|reason):/) {
        reason = reason " " $0
      }
      next
    }

    # First non-comment line after metadata = function/class definition
    in_lock && func_name == "" && !/^[[:space:]]*(#|\/\/|\/\*|\*|--|<!--)/ && !/^[[:space:]]*$/ {
      func_name = $0
      # Clean up: extract just the function/class name
      gsub(/^[[:space:]]*/, "", func_name)
      # For Python: def foo(...) or class Foo(...)
      if (match(func_name, /^(def|class|func|fn|function|public|private|protected)[[:space:]]+([^(:{[:space:]]+)/, parts)) {
        func_name = parts[2]
      }
    }

    /^[[:space:]]*(#|\/\/|\/\*|\*|--|<!--)[[:space:]]*@end-spec-lock/ {
      if (in_lock) {
        # Escape YAML special characters in strings
        gsub(/"/, "\\\"", contract)
        gsub(/"/, "\\\"", raises)
        gsub(/"/, "\\\"", reason)

        printf "  - id: \"%s\"\n", lock_id
        printf "    spec_section: \"§%s\"\n", spec_section
        printf "    file: \"%s\"\n", file
        printf "    line: %d\n", lock_line
        printf "    function: \"%s\"\n", func_name
        printf "    contract: \"%s\"\n", contract
        if (raises != "") {
          printf "    raises: \"%s\"\n", raises
        }
        printf "    reason: |\n      %s\n", reason
      }
      in_lock = 0
    }
  ' "$file" >> "$OUTPUT_FILE" && ((LOCK_COUNT += 1)) || true

done <<< "$LOCK_FILES"

# Count actual locks in output (not files)
ACTUAL_LOCKS=$(grep -c '^  - id:' "$OUTPUT_FILE" 2>/dev/null || echo "0")

echo ""
echo "Scan complete:"
echo "  Directory: $SCAN_DIR"
echo "  Files with @spec-lock: $(echo "$LOCK_FILES" | wc -l | tr -d ' ')"
echo "  Locked blocks found: $ACTUAL_LOCKS"
echo "  Output: $OUTPUT_FILE"

if [[ "$ACTUAL_LOCKS" -gt 0 ]]; then
  echo ""
  echo "Spec-lock health: $ACTUAL_LOCKS locked block(s)"
  echo "Goal: trending toward zero (spec gets more expressive over time)"
fi
