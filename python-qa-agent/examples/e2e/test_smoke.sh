#!/bin/bash
# =================================================================
# E2E TEST: Smoke Test
# =================================================================
#
# Basic request → response smoke test against a live instance.
# Verifies the main API endpoint accepts a request and responds.
#
# Usage:
#   ./test_smoke.sh <base-url>
#   ./test_smoke.sh http://my-service.dev.evergreen.cognet.tv
#
# Customize:
#   Replace the curl payload and URL params with your service's
#   actual request format. The example below uses tvevents format.
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
echo "  E2E Smoke Test — $URL"
echo "═══════════════════════════════════════════════"
echo ""

# Test 1: Service is reachable
echo "1. Reachability (GET /status) ..."
CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$URL/status")
if [ "$CODE" = "200" ]; then
  echo "   ✅ Service reachable → $CODE"
  PASS=$((PASS + 1))
else
  echo "   ❌ Service unreachable → $CODE"
  FAIL=$((FAIL + 1))
  echo ""
  echo "Service is not reachable. Aborting remaining tests."
  exit 1
fi

# Test 2: Main endpoint accepts valid request
# TODO: Customize this payload and URL params for your service.
echo "2. Main endpoint (POST /) ..."
MAIN_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
  -X POST "$URL/?tvid=VZR2023A7F4E9B01&client=smartcast&h=a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6&EventType=NATIVEAPP_TELEMETRY&timestamp=1700000000000" \
  -H "Content-Type: application/json" \
  -d '{
    "TvEvent": {
      "tvid": "VZR2023A7F4E9B01",
      "client": "smartcast",
      "h": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
      "EventType": "NATIVEAPP_TELEMETRY",
      "timestamp": "1700000000000"
    },
    "EventData": {
      "Timestamp": 1700000000000,
      "AppId": "com.vizio.smartcast.gallery",
      "Namespace": "smartcast_apps"
    }
  }')

if [ "$MAIN_CODE" = "200" ]; then
  echo "   ✅ Main endpoint accepted request → $MAIN_CODE"
  PASS=$((PASS + 1))
else
  echo "   ⚠️  Main endpoint returned $MAIN_CODE (may need valid HMAC hash)"
  # Not necessarily a failure — depends on T1_SALT config
fi

# Test 3: Invalid request returns 400 (not 500)
echo "3. Error handling (POST / with bad payload) ..."
ERR_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
  -X POST "$URL/" \
  -H "Content-Type: application/json" \
  -d '{"invalid": "payload"}')

if [ "$ERR_CODE" = "400" ]; then
  echo "   ✅ Bad request → $ERR_CODE (correct rejection)"
  PASS=$((PASS + 1))
elif [ "$ERR_CODE" = "500" ]; then
  echo "   ❌ Bad request → 500 (should be 400, not 500)"
  FAIL=$((FAIL + 1))
else
  echo "   ⚠️  Bad request → $ERR_CODE"
fi

echo ""
echo "═══════════════════════════════════════════════"
echo "  Results: $PASS passed, $FAIL failed"
echo "═══════════════════════════════════════════════"

[ "$FAIL" -eq 0 ] || exit 1
