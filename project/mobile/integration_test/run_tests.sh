#!/bin/bash

# Integration Test Runner for HealthSaathi Mobile App
# This script runs all integration tests with proper setup and teardown

set -e

echo "========================================="
echo "HealthSaathi Integration Test Runner"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is running
echo "Checking backend server..."
if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend server is running${NC}"
else
    echo -e "${RED}✗ Backend server is not running${NC}"
    echo ""
    echo "Please start the backend server first:"
    echo "  cd backend"
    echo "  python run.py"
    echo ""
    exit 1
fi

# Check if database is set up
echo "Checking database..."
if curl -s http://localhost:8000/api/v1/users > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database is accessible${NC}"
else
    echo -e "${YELLOW}⚠ Database may not be properly set up${NC}"
fi

echo ""
echo "Running integration tests..."
echo ""

# Run tests
cd "$(dirname "$0")/.."

# Run API integration tests
echo "========================================="
echo "Running API Integration Tests"
echo "========================================="
flutter test integration_test/api_integration_test.dart

# Run WebSocket integration tests
echo ""
echo "========================================="
echo "Running WebSocket Integration Tests"
echo "========================================="
flutter test integration_test/websocket_integration_test.dart

# Run navigation flow tests
echo ""
echo "========================================="
echo "Running Navigation Flow Tests"
echo "========================================="
flutter test integration_test/navigation_flow_test.dart

echo ""
echo "========================================="
echo -e "${GREEN}All integration tests completed!${NC}"
echo "========================================="
