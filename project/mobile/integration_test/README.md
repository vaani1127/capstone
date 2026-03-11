# HealthSaathi Mobile Integration Tests

This directory contains comprehensive integration tests for the HealthSaathi mobile application.

## Test Suites

### 1. API Integration Tests (`api_integration_test.dart`)

Tests the mobile app's integration with the backend API:

- **Authentication Flow**
  - Login with valid/invalid credentials
  - Logout functionality
  - Token persistence across app restarts
  - Token expiration handling

- **Appointment Booking Flow**
  - Get available doctors
  - Book appointments
  - Cancel appointments
  - Reschedule appointments
  - Prevent double-booking

- **Medical Records Retrieval**
  - Get patient medical records
  - Get record by ID
  - Enforce read-only access for patients

- **Queue Status Updates**
  - Get queue status for doctors
  - Calculate estimated waiting time
  - Update queue position after booking

- **Role-Based Access Control**
  - Verify role-specific endpoint access
  - Deny unauthorized access

- **Error Handling**
  - Network errors
  - 404 errors
  - Malformed responses

### 2. WebSocket Integration Tests (`websocket_integration_test.dart`)

Tests real-time communication via WebSocket:

- **Connection Management**
  - Connect with JWT authentication
  - Fail to connect without authentication
  - Disconnect successfully
  - Emit connection status events
  - Auto-reconnect on connection loss

- **Real-Time Queue Updates**
  - Receive queue update events
  - Filter updates by doctor
  - Update queue length in real-time
  - Include estimated wait time

- **Appointment Status Notifications**
  - Receive status change events
  - Filter notifications by appointment

- **Message Handling**
  - Handle multiple concurrent messages
  - Filter messages by event type
  - Handle malformed messages gracefully

- **Performance**
  - Receive updates within 2 seconds (NFR-6)
  - Handle high-frequency updates

### 3. Navigation Flow Tests (`navigation_flow_test.dart`)

Tests app navigation and routing:

- **Login and Role-Based Routing**
  - Navigate to patient dashboard after patient login
  - Navigate to doctor dashboard after doctor login
  - Navigate to nurse dashboard after nurse login
  - Navigate to admin dashboard after admin login
  - Stay on login screen with invalid credentials
  - Navigate to registration screen

- **Patient Navigation Flows**
  - Navigate to appointment booking
  - Navigate to medical history
  - Navigate to queue status with doctor details
  - Complete appointment booking flow

- **Doctor Navigation Flows**
  - Navigate to queue management
  - Navigate to consultation screen

- **Nurse Navigation Flows**
  - Navigate to walk-in registration
  - Complete walk-in registration flow

- **Admin Navigation Flows**
  - Navigate to user management
  - Navigate to audit dashboard

- **Back Navigation**
  - Navigate back using system back button
  - Navigate back using app bar back button

- **Deep Linking**
  - Handle deep links with arguments

- **Logout Flow**
  - Logout and return to login screen

## Prerequisites

Before running integration tests, ensure:

1. **Backend server is running**
   ```bash
   cd backend
   python run.py
   # Or using uvicorn directly:
   # uvicorn app.main:app --reload
   ```

2. **Database is set up with test data**
   ```bash
   cd backend
   # Run migrations
   python -m alembic upgrade head
   # Seed data is automatically created by migration 002_seed_data.py
   ```

3. **Test users exist in the database**
   
   The seed data migration creates the following test users:
   - patient@test.com (password: password123) - Role: Patient
   - doctor@test.com (password: password123) - Role: Doctor
   - nurse@test.com (password: password123) - Role: Nurse
   - admin@test.com (password: password123) - Role: Admin

4. **Dependencies are installed**
   ```bash
   cd mobile
   flutter pub get
   ```

5. **Backend health check passes**
   ```bash
   curl http://localhost:8000/api/v1/health
   # Should return: {"status": "healthy"}
   ```

## Running Tests

### Quick Start (Recommended)

Use the provided test runner scripts:

**Linux/Mac:**
```bash
cd mobile/integration_test
chmod +x run_tests.sh
./run_tests.sh
```

**Windows:**
```cmd
cd mobile\integration_test
run_tests.bat
```

These scripts will:
1. Check if backend server is running
2. Verify database connectivity
3. Run all integration test suites
4. Report results

### Run All Integration Tests

```bash
cd mobile
flutter test integration_test/all_tests.dart
```

### Run Specific Test Suite

```bash
# API integration tests only
flutter test integration_test/api_integration_test.dart

# WebSocket integration tests only
flutter test integration_test/websocket_integration_test.dart

# Navigation flow tests only
flutter test integration_test/navigation_flow_test.dart
```

### Run on Physical Device or Emulator

Integration tests can also run on a physical device or emulator:

```bash
# Start an emulator or connect a device
flutter devices

# Run tests on device
flutter test integration_test/all_tests.dart --device-id=<device_id>
```

### Run with Integration Test Driver

For more advanced testing with screenshots and performance profiling:

```bash
flutter drive \
  --driver=test_driver/integration_test.dart \
  --target=integration_test/all_tests.dart
```

## Test Configuration

### API Configuration

Tests use the configuration from `lib/config/app_config.dart`:

- API Base URL: `http://localhost:8000`
- WebSocket URL: `ws://localhost:8000/ws`

To test against a different backend, update the configuration before running tests.

### Test Data

Tests assume the following test data exists:

- Test users with roles: Patient, Doctor, Nurse, Admin
- At least one doctor with specialization
- Sample appointments (optional, tests will create new ones)

## Test Isolation

Each test suite includes:

- **setUp**: Initializes services before each test
- **tearDown**: Cleans up (logout, disconnect) after each test

This ensures tests are isolated and don't interfere with each other.

## Troubleshooting

### Tests Fail with "Connection Refused"

- Ensure backend server is running on `http://localhost:8000`
- Check that the API is accessible from the test environment

### WebSocket Tests Timeout

- Verify WebSocket server is running and accessible
- Check that JWT authentication is working
- Increase timeout durations if network is slow

### Navigation Tests Fail to Find Widgets

- Ensure test users exist in the database
- Check that screens have the expected text/widgets
- Verify that keys are correctly set on form fields and buttons

### Tests Pass Locally but Fail in CI

- Ensure CI environment has backend server running
- Check that database is properly seeded
- Verify network connectivity between test runner and backend

## Performance Benchmarks

Integration tests verify the following performance requirements:

- **NFR-6**: Real-time queue updates within 2 seconds
- **NFR-9**: API response time < 500ms for 95th percentile
- **NFR-10**: Hash verification within 100ms

## Coverage

Integration tests cover:

- ✅ Authentication and authorization
- ✅ Appointment booking and management
- ✅ Medical records access
- ✅ Queue management
- ✅ Real-time WebSocket communication
- ✅ Role-based access control
- ✅ Navigation and routing
- ✅ Error handling

## Future Enhancements

Potential additions to integration tests:

- Screenshot testing for UI regression
- Performance profiling and metrics
- Accessibility testing
- Offline mode testing
- Multi-device synchronization tests
- Load testing with multiple concurrent users

## Contributing

When adding new features:

1. Write integration tests for new API endpoints
2. Add WebSocket tests for new real-time features
3. Update navigation tests for new screens
4. Ensure tests are isolated and repeatable
5. Update this README with new test descriptions

## Related Documentation

- [Widget Tests](../test/README.md)
- [API Documentation](../../backend/API_DOCUMENTATION.md)
- [Design Document](../../.kiro/specs/healthsaathi-healthcare-system/design.md)
- [Requirements](../../.kiro/specs/healthsaathi-healthcare-system/requirements.md)
