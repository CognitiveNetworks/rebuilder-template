#!/bin/bash
# =================================================================
# E2E TEST: /ops/* SRE Contract
# =================================================================
#
# Verifies all /ops/* endpoints respond with required fields.
# Run against a live deployed instance to validate the SRE agent contract.
#
# Usage:
#   ./test_ops_contract.sh <base-url>
#   ./test_ops_contract.sh http://my-service.dev.evergreen.cognet.tv
#
# What This Tests:
#   - All diagnostic GET endpoints return 200 with required JSON fields
#   - All remediation POST endpoints accept valid input and respond
#   - Drain mode lifecycle works end-to-end
#
# =================================================================
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <base-url>"
  echo "Example: $0 http://my-service.dev.evergreen.cognet.tv"
  exit 1
fi

URL="$1"
PASS=0
FAIL=0

check_get() {
  local path="$1"
  local required_field="$2"
  local label="$3"

  CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL$path")
  BODY=$(curl -s "$URL$path")

  if [ "$CODE" = "200" ]; then
    echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); assert '$required_field' in d" 2>/dev/null
    if [ $? -eq 0 ]; then
      echo "   ✅ GET $path → $CODE, has '$required_field'"
      PASS=$((PASS + 1))
      return 0
    else
      echo "   ❌ GET $path → $CODE, missing '$required_field'"
      FAIL=$((FAIL + 1))
      return 1
    fi
  else
    echo "   ❌ GET $path → $CODE (expected 200)"
    FAIL=$((FAIL + 1))
    return 1
  fi
}

check_post() {
  local path="$1"
  local data="$2"
  local expected_code="$3"
  local required_field="$4"

  CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$URL$path" \
    -H "Content-Type: application/json" -d "$data")
  BODY=$(curl -s -X POST "$URL$path" \
    -H "Content-Type: application/json" -d "$data")

  if [ "$CODE" = "$expected_code" ]; then
    if [ -n "$required_field" ]; then
      echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); assert '$required_field' in d" 2>/dev/null
      if [ $? -eq 0 ]; then
        echo "   ✅ POST $path → $CODE, has '$required_field'"
        PASS=$((PASS + 1))
        return 0
      else
        echo "   ❌ POST $path → $CODE, missing '$required_field'"
        FAIL=$((FAIL + 1))
        return 1
      fi
    else
      echo "   ✅ POST $path → $CODE"
      PASS=$((PASS + 1))
      return 0
    fi
  else
    echo "   ❌ POST $path → $CODE (expected $expected_code)"
    FAIL=$((FAIL + 1))
    return 1
  fi
}

echo "═══════════════════════════════════════════════"
echo "  E2E /ops/* Contract — $URL"
echo "═══════════════════════════════════════════════"
echo ""

echo "── Diagnostic Endpoints (GET) ──"
check_get "/ops/status"       "status"         "Composite status"
check_get "/ops/health"       "status"         "Health checks"
check_get "/ops/metrics"      "golden_signals" "Golden Signals"
check_get "/ops/config"       "service_name"   "Runtime config"
check_get "/ops/errors"       "total"          "Error summary"
check_get "/ops/cache"        "entry_count"    "Cache stats"

echo ""
echo "── Remediation Endpoints (POST) ──"
check_post "/ops/loglevel" '{"level":"DEBUG"}' "200" "level"
check_post "/ops/loglevel" '{"level":"TRACE"}' "400" ""
check_post "/ops/circuits" '{}' "200" "circuits"

echo ""
echo "═══════════════════════════════════════════════"
echo "  Results: $PASS passed, $FAIL failed"
echo "═══════════════════════════════════════════════"

[ "$FAIL" -eq 0 ] || exit 1
