#!/bin/bash
# HealthSaathi Health Check Script

set -e

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
TIMEOUT="${TIMEOUT:-10}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}HealthSaathi Health Check${NC}"
echo -e "${GREEN}========================================${NC}"
echo "API URL: $API_URL"
echo "Timestamp: $(date)"
echo ""

# Function to check endpoint
check_endpoint() {
    local endpoint=$1
    local description=$2
    
    echo -n "Checking $description... "
    
    if response=$(curl -s -f -m "$TIMEOUT" "$API_URL$endpoint" 2>&1); then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "  Error: $response"
        return 1
    fi
}

# Function to check database
check_database() {
    echo -n "Checking database connection... "
    
    if response=$(curl -s -f -m "$TIMEOUT" "$API_URL/health/db" 2>&1); then
        if echo "$response" | grep -q '"status":"healthy"'; then
            echo -e "${GREEN}✓ OK${NC}"
            return 0
        else
            echo -e "${RED}✗ FAILED${NC}"
            echo "  Response: $response"
            return 1
        fi
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "  Error: $response"
        return 1
    fi
}

# Track failures
FAILURES=0

# Check main health endpoint
check_endpoint "/health" "API health" || ((FAILURES++))

# Check database health
check_database || ((FAILURES++))

# Check API documentation
check_endpoint "/docs" "API documentation" || ((FAILURES++))

# Check specific API endpoints (if authenticated)
# check_endpoint "/api/v1/appointments" "Appointments API" || ((FAILURES++))

echo ""
echo -e "${GREEN}========================================${NC}"

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}All health checks passed!${NC}"
    exit 0
else
    echo -e "${RED}$FAILURES health check(s) failed${NC}"
    exit 1
fi
