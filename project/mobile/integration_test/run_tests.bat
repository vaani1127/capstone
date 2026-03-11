@echo off
REM Integration Test Runner for HealthSaathi Mobile App (Windows)
REM This script runs all integration tests with proper setup and teardown

echo =========================================
echo HealthSaathi Integration Test Runner
echo =========================================
echo.

REM Check if backend is running
echo Checking backend server...
curl -s http://localhost:8000/api/v1/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Backend server is running
) else (
    echo [ERROR] Backend server is not running
    echo.
    echo Please start the backend server first:
    echo   cd backend
    echo   python run.py
    echo.
    exit /b 1
)

echo.
echo Running integration tests...
echo.

REM Change to mobile directory
cd /d "%~dp0\.."

REM Run API integration tests
echo =========================================
echo Running API Integration Tests
echo =========================================
call flutter test integration_test/api_integration_test.dart
if %errorlevel% neq 0 (
    echo [ERROR] API integration tests failed
    exit /b 1
)

REM Run WebSocket integration tests
echo.
echo =========================================
echo Running WebSocket Integration Tests
echo =========================================
call flutter test integration_test/websocket_integration_test.dart
if %errorlevel% neq 0 (
    echo [ERROR] WebSocket integration tests failed
    exit /b 1
)

REM Run navigation flow tests
echo.
echo =========================================
echo Running Navigation Flow Tests
echo =========================================
call flutter test integration_test/navigation_flow_test.dart
if %errorlevel% neq 0 (
    echo [ERROR] Navigation flow tests failed
    exit /b 1
)

echo.
echo =========================================
echo [SUCCESS] All integration tests completed!
echo =========================================
