#!/bin/bash
# Manual Slack Integration Testing Script
# This script helps you test the backend without going through Slack

set -e

echo "=========================================="
echo "CS Log Lens - Slack Integration Test"
echo "=========================================="
echo ""

# Check if backend is running
echo "1. Checking if backend is running..."
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
if curl -s "${BACKEND_URL}/health" > /dev/null 2>&1; then
    echo "✓ Backend is running at ${BACKEND_URL}"
else
    echo "✗ Backend is not responding at ${BACKEND_URL}"
    echo "  Start it with: cd backend && uvicorn main:app --reload"
    exit 1
fi
echo ""

# Test the analyze endpoint (without Slack signature)
echo "2. Testing /analyze endpoint..."
echo "   (This simulates what happens when Slack calls the backend)"
echo ""

RESPONSE=$(curl -s -X POST "${BACKEND_URL}/analyze" \
  -H "Content-Type: application/json" \
  -H "X-App-Password: Orbital2026" \
  -d '{
    "description": "User experiencing template error on dashboard",
    "timestamp": "2026-01-16T19:22:11.883Z",
    "customer_id": "test_customer"
  }')

if echo "$RESPONSE" | grep -q '"success":true'; then
    echo "✓ Analysis endpoint working!"
    echo ""
    echo "Response summary:"
    echo "$RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'  • Success: {data.get(\"success\")}')
    print(f'  • Events found: {data.get(\"events_found\")}')
    print(f'  • Causes identified: {len(data.get(\"causes\", []))}')
    print(f'  • Top cause: {data.get(\"causes\", [{}])[0].get(\"cause\", \"N/A\")[:60]}...')
except Exception as e:
    print(f'  Error parsing response: {e}')
"
else
    echo "✗ Analysis endpoint failed"
    echo "Response:"
    echo "$RESPONSE" | head -20
    exit 1
fi
echo ""

echo "=========================================="
echo "Backend Test Complete! ✓"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. If backend test passed, the backend is working correctly"
echo "2. Now test in Slack with this command:"
echo ""
echo "   /loglens User experiencing template error on dashboard | 2026-01-16T19:22:11.883Z | test_customer"
echo ""
echo "3. Make sure your Slack app's Request URL points to:"
echo "   ${BACKEND_URL}/slack/commands"
echo ""
echo "4. Check the SLACK_TESTING_GUIDE.md for detailed testing instructions"
echo ""
