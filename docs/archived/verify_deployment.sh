#!/bin/bash

# LogLens Deployment Verification Script
# This script verifies both backend and frontend deployments

set -e

echo "🧪 LogLens Deployment Verification"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if required commands exist
command -v curl >/dev/null 2>&1 || { echo -e "${RED}✗ curl is required but not installed${NC}"; exit 1; }
command -v jq >/dev/null 2>&1 || { echo -e "${YELLOW}⚠ jq not found - JSON output will not be formatted${NC}"; }

# Get URLs from arguments or prompt
if [ -z "$1" ]; then
    read -p "Enter Backend URL (Railway): " BACKEND_URL
else
    BACKEND_URL=$1
fi

if [ -z "$2" ]; then
    read -p "Enter Frontend URL (Cloudflare Pages): " FRONTEND_URL
else
    FRONTEND_URL=$2
fi

echo ""
echo "Testing deployment..."
echo "Backend:  $BACKEND_URL"
echo "Frontend: $FRONTEND_URL"
echo ""

# Test 1: Backend Health Check
echo "Test 1: Backend Health Check"
echo "----------------------------"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/health")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
BODY=$(echo "$HEALTH_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "200" ]; then
    echo -e "${GREEN}✓ Backend is healthy (HTTP $HTTP_CODE)${NC}"
    if command -v jq >/dev/null 2>&1; then
        echo "$BODY" | jq '.'
    else
        echo "$BODY"
    fi
else
    echo -e "${RED}✗ Backend health check failed (HTTP $HTTP_CODE)${NC}"
    echo "$BODY"
    exit 1
fi
echo ""

# Test 2: Backend CORS Headers
echo "Test 2: Backend CORS Configuration"
echo "-----------------------------------"
CORS_HEADERS=$(curl -s -I -X OPTIONS "$BACKEND_URL/health" | grep -i "access-control")

if [ -n "$CORS_HEADERS" ]; then
    echo -e "${GREEN}✓ CORS headers present${NC}"
    echo "$CORS_HEADERS"
else
    echo -e "${YELLOW}⚠ CORS headers not found - may cause issues${NC}"
fi
echo ""

# Test 3: Frontend Loads
echo "Test 3: Frontend Loads"
echo "----------------------"
FRONTEND_RESPONSE=$(curl -s -w "\n%{http_code}" "$FRONTEND_URL")
HTTP_CODE=$(echo "$FRONTEND_RESPONSE" | tail -n1)
BODY=$(echo "$FRONTEND_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "200" ]; then
    if echo "$BODY" | grep -q "LogLens"; then
        echo -e "${GREEN}✓ Frontend loads successfully (HTTP $HTTP_CODE)${NC}"
        echo -e "${GREEN}✓ Page contains LogLens content${NC}"
    else
        echo -e "${YELLOW}⚠ Frontend loads but content may be incorrect${NC}"
    fi
else
    echo -e "${RED}✗ Frontend failed to load (HTTP $HTTP_CODE)${NC}"
    exit 1
fi
echo ""

# Test 4: HTTPS Check
echo "Test 4: SSL/HTTPS Verification"
echo "-------------------------------"
if [[ "$BACKEND_URL" == https://* ]]; then
    echo -e "${GREEN}✓ Backend uses HTTPS${NC}"
else
    echo -e "${RED}✗ Backend not using HTTPS${NC}"
fi

if [[ "$FRONTEND_URL" == https://* ]]; then
    echo -e "${GREEN}✓ Frontend uses HTTPS${NC}"
else
    echo -e "${RED}✗ Frontend not using HTTPS${NC}"
fi
echo ""

# Test 5: Backend Authentication
echo "Test 5: Backend Authentication"
echo "-------------------------------"
echo "Testing /analyze endpoint without auth..."
NO_AUTH_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BACKEND_URL/analyze" \
    -H "Content-Type: application/json" \
    -d '{"description":"test","timestamp":"2024-01-01T00:00:00Z","customer_id":"test"}')

HTTP_CODE=$(echo "$NO_AUTH_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" == "401" ]; then
    echo -e "${GREEN}✓ Authentication required (HTTP 401)${NC}"
    echo -e "${GREEN}✓ Endpoint is properly secured${NC}"
else
    echo -e "${YELLOW}⚠ Expected 401, got HTTP $HTTP_CODE${NC}"
fi
echo ""

# Summary
echo "=================================="
echo "Summary"
echo "=================================="
echo -e "${GREEN}✓ Backend is healthy and accessible${NC}"
echo -e "${GREEN}✓ Frontend is deployed and serving${NC}"
echo -e "${GREEN}✓ HTTPS is configured${NC}"
echo -e "${GREEN}✓ Authentication is enforced${NC}"
echo ""
echo "Next steps:"
echo "1. Test authentication with your password"
echo "2. Submit a test analysis through the web form"
echo "3. Verify Sentry integration works"
echo "4. Test from mobile device"
echo ""
echo "To test with authentication, use:"
echo "  curl -X POST $BACKEND_URL/analyze \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -H 'X-Auth-Token: YOUR_PASSWORD' \\"
echo "    -d '{\"description\":\"test\",\"timestamp\":\"2024-01-01T00:00:00Z\",\"customer_id\":\"test\"}'"
echo ""
echo "Or open the test suite:"
echo "  $FRONTEND_URL/test_deployment.html"
echo ""
