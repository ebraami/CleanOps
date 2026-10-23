#!/usr/bin/env bash
# =============================================================================
# CleanOps - Sprint 01 Security & Authentication Boundary Test Suite
# Owner: Ebraam Ibrahim (Cybersecurity & QA Lead)
# Usage: ./tests/security/auth_security_test.sh [API_BASE_URL]
# Default URL: http://localhost:8080/api/v1
# =============================================================================

set -e

API_URL="${1:-http://localhost:8080/api/v1}"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}  CleanOps Sprint 01: API Security & Auth Boundary Tests${NC}"
echo -e "${BLUE}  Target Endpoint: ${API_URL}${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""

# Helper to evaluate results
assert_equals() {
    local test_name="$1"
    local expected="$2"
    local actual="$3"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ "$expected" == "$actual" ]; then
        echo -e "  [${GREEN}PASS${NC}] $test_name (Expected: $expected, Got: $actual)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "  [${RED}FAIL${NC}] $test_name (Expected: $expected, Got: $actual)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# -----------------------------------------------------------------------------
# Test 1: Missing Authorization Header
# -----------------------------------------------------------------------------
echo -e "${YELLOW}Running Test 1: Missing Authorization Header...${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/users/me")
HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$RESPONSE" | head -n -1)

assert_equals "HTTP Status for Missing Token" "401" "$HTTP_STATUS"

if echo "$RESPONSE_BODY" | grep -q "Missing or invalid token"; then
    echo -e "  [${GREEN}PASS${NC}] Error message correctly masked ('Missing or invalid token')"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "  [${RED}FAIL${NC}] Unexpected error body: $RESPONSE_BODY"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo ""

# -----------------------------------------------------------------------------
# Test 2: Forged / Fake Bearer Token
# -----------------------------------------------------------------------------
echo -e "${YELLOW}Running Test 2: Forged / Tampered Bearer Token...${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer forged_jwt_signature_abc123" "$API_URL/users/me")
HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$RESPONSE" | head -n -1)

assert_equals "HTTP Status for Forged Token" "401" "$HTTP_STATUS"

if echo "$RESPONSE_BODY" | grep -q "Invalid or expired token"; then
    echo -e "  [${GREEN}PASS${NC}] Error message correctly masked ('Invalid or expired token')"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "  [${RED}FAIL${NC}] Unexpected error body: $RESPONSE_BODY"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo ""

# -----------------------------------------------------------------------------
# Test 3: Malformed Authorization Header (No 'Bearer ' prefix)
# -----------------------------------------------------------------------------
echo -e "${YELLOW}Running Test 3: Malformed Header (Missing 'Bearer ' Prefix)...${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" -H "Authorization: Basic dXNlcjpwYXNz" "$API_URL/users/me")
HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)

assert_equals "HTTP Status for Non-Bearer Header" "401" "$HTTP_STATUS"
echo ""

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}  Test Execution Summary${NC}"
echo -e "  Total Assertions: $TOTAL_TESTS"
echo -e "  Passed:           ${GREEN}$PASSED_TESTS${NC}"
echo -e "  Failed:           ${RED}$FAILED_TESTS${NC}"
echo -e "${BLUE}======================================================================${NC}"

if [ "$FAILED_TESTS" -eq 0 ]; then
    echo -e "${GREEN}ALL SECURITY BOUNDARY CHECKS PASSED SUCCESSFULLY.${NC}"
    exit 0
else
    echo -e "${RED}ONE OR MORE SECURITY BOUNDARY CHECKS FAILED.${NC}"
    exit 1
fi
