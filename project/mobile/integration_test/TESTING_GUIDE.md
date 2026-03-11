# Integration Testing Guide for HealthSaathi Mobile App

## Quick Start

### 1. Start Backend Server

```bash
cd backend
python run.py
```

Verify backend is running:
```bash
curl http://localhost:8000/api/v1/health
# Expected: {"status": "healthy"}
```

### 2. Run Integration Tests

**Option A: Use Test Runner (Recommended)**

Linux/Mac:
```bash
cd mobile/integration_test
chmod +x run_tests.sh
./run_tests.sh
```

Windows:
```cmd
cd mobile\integration_test
run_tests.bat
```

**Option B: Run Manually**

```bash
cd mobile

# Run all tests
flutter test integration_test/all_tests.dart

# Run specific test suite
flutter test integration_test/api_integration_test.dart
flutter test integration_test/websocket_integration_test.dart
flutter test integration_test/navigation_flow_test.dart
```

## Test Suites Overview

### API Integration Tests
- **File**: `api_integration_test.dart`
- **Tests**: 25+ test cases
- **Coverage**: Authentication, appointments, medical records, queue management, RBAC, error handling
- **Duration**: ~2-3 minutes

### WebSocket Integration Tests
- **File**: `websocket_integration_test.dart`
- **Tests**: 20+ test cases
- **Coverage**: Connection management, real-time updates, message handling, performance
- **Duration**: ~3-4 minutes

### Navigation Flow Tests
- **File**: `navigation_flow_test.dart`
- **Tests**: 20+ test cases
- **Coverage**: Login flows, role-based routing, screen navigation, deep linking
- **Duration**: ~4-5 minutes

## Test Data Requirements

### Test Users

The following test users must exist in the database (created by seed migration):

| Email | Password | Role | Purpose |
|-------|----------|------|---------|
| patient@test.com | password123 | Patient | Patient flow testing |
| doctor@test.com | password123 | Doctor | Doctor flow testing |
| nurse@test.com | password123 | Nurse | Nurse flow testing |
| admin@test.com | password123 | Admin | Admin flow testing |

### Database Setup

```bash
cd backend

# Run migrations (creates schema)
python -m alembic upgrade head

# Seed data is automatically created by migration 002_seed_data.py
# This includes test users and sample data
```

## Understanding Test Results

### Successful Test Run

```
✓ should login with valid credentials
✓ should fail login with invalid credentials
✓ should logout successfully
...
All tests passed!
```

### Failed Test

```
✗ should login with valid credentials
  Expected: User object
  Actual: ApiException: Connection refused
```

Common failure reasons:
1. Backend server not running
2. Database not seeded
3. Network connectivity issues
4. Test data missing

## Troubleshooting

### Backend Connection Issues

**Problem**: Tests fail with "Connection refused" or "Unable to connect"

**Solutions**:
1. Verify backend is running: `curl http://localhost:8000/api/v1/health`
2. Check backend logs for errors
3. Ensure correct port (8000) is being used
4. Check firewall settings

### Authentication Failures

**Problem**: Tests fail with "Unauthorized" or "Invalid credentials"

**Solutions**:
1. Verify test users exist in database
2. Check password hashing is working correctly
3. Verify JWT token generation
4. Check token expiration settings

### WebSocket Connection Issues

**Problem**: WebSocket tests timeout or fail to connect

**Solutions**:
1. Verify WebSocket server is running
2. Check WebSocket URL configuration
3. Verify JWT authentication for WebSocket
4. Check for proxy/firewall blocking WebSocket connections

### Navigation Test Failures

**Problem**: Tests can't find widgets or screens

**Solutions**:
1. Verify widget keys are set correctly in screen files
2. Check that screen text matches test expectations
3. Ensure proper navigation routes are configured
4. Verify authentication state is correct

### Database Issues

**Problem**: Tests fail with "Record not found" or "Invalid data"

**Solutions**:
1. Run migrations: `python -m alembic upgrade head`
2. Verify seed data was created
3. Check database connection in backend
4. Reset database if needed: `python -m alembic downgrade base && python -m alembic upgrade head`

## Test Configuration

### API Configuration

Tests use configuration from `lib/config/app_config.dart`:

```dart
static const String apiBaseUrl = 'http://localhost:8000';
static const String wsBaseUrl = 'ws://localhost:8000';
```

To test against a different backend:
1. Update `app_config.dart`
2. Ensure backend is accessible from test environment
3. Verify CORS settings allow test requests

### Test Timeouts

Default timeouts in tests:
- API requests: 30 seconds
- WebSocket connection: 5 seconds
- Widget interactions: 2 seconds

Adjust timeouts in test files if needed for slower environments.

## Best Practices

### Writing New Integration Tests

1. **Follow existing patterns**: Use the same structure as existing tests
2. **Use setUp/tearDown**: Ensure proper initialization and cleanup
3. **Test isolation**: Each test should be independent
4. **Clear assertions**: Use descriptive expect statements
5. **Handle async properly**: Use async/await correctly
6. **Add comments**: Explain what each test validates

### Test Maintenance

1. **Update tests when APIs change**: Keep tests in sync with backend
2. **Update test data**: Ensure test users and data are current
3. **Review failing tests**: Don't ignore failures, investigate root cause
4. **Keep tests fast**: Optimize slow tests, use appropriate timeouts
5. **Document changes**: Update README when adding new test suites

## CI/CD Integration

### Running Tests in CI Pipeline

```yaml
# Example GitHub Actions workflow
- name: Start Backend
  run: |
    cd backend
    python run.py &
    sleep 10

- name: Run Integration Tests
  run: |
    cd mobile
    flutter test integration_test/all_tests.dart
```

### CI Requirements

1. Backend server must be running
2. Database must be accessible
3. Test data must be seeded
4. Network connectivity required
5. Flutter SDK installed

## Performance Benchmarks

Integration tests validate these performance requirements:

| Metric | Requirement | Test |
|--------|-------------|------|
| API Response Time | < 500ms | ✅ Validated |
| WebSocket Update Latency | < 2 seconds | ✅ Validated |
| Queue Calculation | < 100ms | ✅ Validated |
| Authentication | < 1 second | ✅ Validated |

## Test Coverage Report

### Functional Coverage

- ✅ User authentication and authorization
- ✅ Appointment booking and management
- ✅ Medical records access
- ✅ Queue management and updates
- ✅ Real-time WebSocket communication
- ✅ Role-based access control
- ✅ Navigation and routing
- ✅ Error handling

### User Story Coverage

All user stories from requirements.md are covered:
- ✅ US-1: User Registration and Authentication
- ✅ US-2: Role-Based Access Control
- ✅ US-3: Patient Appointment Booking
- ✅ US-4: Walk-in Patient Registration
- ✅ US-5: Real-Time Queue Status
- ✅ US-6: Appointment Management
- ✅ US-7: Intelligent Queue Management
- ✅ US-10: Patient Medical History Access

## Additional Resources

- [Integration Test Summary](INTEGRATION_TEST_SUMMARY.md) - Detailed test coverage
- [README](README.md) - Complete test documentation
- [API Documentation](../../backend/API_DOCUMENTATION.md) - Backend API reference
- [Design Document](../../.kiro/specs/healthsaathi-healthcare-system/design.md) - System design
- [Requirements](../../.kiro/specs/healthsaathi-healthcare-system/requirements.md) - Requirements specification

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review test logs for error details
3. Verify backend and database are working
4. Check that test data exists
5. Review related documentation

## Summary

Integration tests provide comprehensive validation of:
- ✅ 65+ test cases across 3 test suites
- ✅ Complete API integration testing
- ✅ Real-time WebSocket communication
- ✅ End-to-end navigation flows
- ✅ Role-based access control
- ✅ Performance requirements
- ✅ Error handling scenarios

All tests are designed to be reliable, maintainable, and provide confidence in the mobile app's integration with the backend system.
