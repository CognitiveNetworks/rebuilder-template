#!/bin/bash
# =================================================================
# E2E TEST: Health Endpoints
# =================================================================
#
# Verifies /status and /health respond correctly on a live instance.
#
# Usage:
#   ./test_health.sh <base-url>
#   ./test_health.sh http://my-service.dev.evergreen.cognet.tv
#
# What This Tests:
#   - /status returns 200 with body "OK"
#   - /health returns 200 with JSON containing "status" field
#   - Service is reachable and responding
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

echo "═══════════════════════════════════════════════"
echo "  E2E Health Check — $URL"
echo "═══════════════════════════════════════════════"
echo ""

# Test 1: /status
echo "1. GET /status ..."
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/status")
STATUS_BODY=$(curl -s "$URL/status")
if [ "$STATUS_CODE" = "200" ] && [ "$STATUS_BODY" = "OK" ]; then
  echo "   ✅ /status → $STATUS_CODE, body: $STATUS_BODY"
  PASS=$((PASS + 1))
else
  echo "   ❌ /status → $STATUS_CODE, body: $STATUS_BODY (expected 200, OK)"
  FAIL=$((FAIL + 1))
fi

# Test 2: /health
echo "2. GET /health ..."
HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/health")
HEALTH_BODY=$(curl -s "$URL/health")
if [ "$HEALTH_CODE" = "200" ]; then
  echo "$HEALTH_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'status' in d" 2>/dev/null
  if [ $? -eq 0 ]; then
    echo "   ✅ /health → $HEALTH_CODE, has 'status' field"
    PASS=$((PASS + 1))
  else
    echo "   ❌ /health → $HEALTH_CODE, missing 'status' field"
    FAIL=$((FAIL + 1))
  fi
else
  echo "   ⚠️  /health → $HEALTH_CODE (may be degraded — check dependencies)"
  FAIL=$((FAIL + 1))
fi

echo ""
echo "═══════════════════════════════════════════════"
echo "  Results: $PASS passed, $FAIL failed"
echo "═══════════════════════════════════════════════"

[ "$FAIL" -eq 0 ] || exit 1
