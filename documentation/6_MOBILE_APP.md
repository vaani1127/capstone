# Mobile App Guide

HealthSaathi Flutter mobile application for all user roles.

## Overview

Cross-platform mobile app built with Flutter supporting iOS and Android. Features real-time queue updates, appointment management, and secure medical record access.

## Prerequisites

- Flutter SDK (>=3.0.0)
- Dart SDK
- Android Studio or Xcode

## Installation

### 1. Install Dependencies

```bash
cd mobile
flutter pub get
```

### 2. Configure API Endpoint

Edit `lib/config/app_config.dart`:

```dart
class AppConfig {
  static const String apiBaseUrl = 'http://localhost:8000';
  static const String apiVersion = 'v1';
}
```

### 3. Run the App

#### Android
```bash
flutter run -d android
```

#### iOS
```bash
flutter run -d ios
```

## Project Structure

```
mobile/
├── lib/
│   ├── main.dart                 # App entry point
│   ├── config/
│   │   └── app_config.dart       # API and app settings
│   ├── models/                   # Data models
│   │   ├── user.dart
│   │   ├── appointment.dart
│   │   ├── medical_record.dart
│   │   └── doctor.dart
│   ├── services/                 # API and WebSocket services
│   │   ├── api_client.dart       # HTTP client
│   │   └── websocket_service.dart # Real-time updates
│   ├── providers/                # State management
│   ├── screens/                  # UI screens
│   │   ├── auth/                 # Login/Register
│   │   ├── patient/              # Patient screens
│   │   ├── doctor/               # Doctor screens
│   │   ├── nurse/                # Nurse screens
│   │   └── admin/                # Admin screens
│   │       ├── admin_home_screen.dart
│   │       └── anomaly_alerts_screen.dart  # Security Alerts dashboard
│   └── widgets/                  # Reusable UI widgets
├── pubspec.yaml                  # Flutter dependencies
└── analysis_options.yaml         # Linter configuration
```

## Features by Role

### Patient

- **Registration & Login** - Create account and authenticate
- **Book Appointments** - Search doctors, select time slots
- **View Queue Position** - Real-time queue status with WebSocket
- **Medical History** - View past consultations and prescriptions
- **Appointment Management** - Cancel or reschedule appointments

### Doctor

- **Patient Queue** - View real-time queue with patient info
- **Consultation Notes** - Create and edit medical records
- **Prescriptions** - Issue prescriptions to patients
- **Appointment Management** - Check-in patients, mark complete

### Nurse

- **Walk-in Registration** - Register new patients on the fly
- **Queue Management** - Update queue status
- **Patient Check-in** - Mark patients as checked in
- **Queue Monitoring** - Monitor doctor queues

### Admin

- **User Management** - Create, edit, delete users
- **Audit Logs** - View system activity and tampering alerts
- **Queue Monitoring** - Overview of all queues
- **Record Verification** - Verify medical record integrity
- **Security Alerts** (`anomaly_alerts_screen.dart`) - ML-powered behavioural anomaly dashboard. Fetches alert list and summary stats on load (parallel requests), then subscribes to `WS /anomaly/ws/admin` for real-time push of MEDIUM/HIGH alerts. Displays a stats bar (Total / Unread / HIGH count), alert cards with colour-coded severity badges (RED=HIGH, ORANGE=MEDIUM, YELLOW=LOW), SHAP-based explanation text, anomaly score as a percentage, and a per-card **Acknowledge** button with optimistic UI update. Accessible from the admin home "Security Alerts" quick-link card.

## Key Technologies

- **Framework**: Flutter 3.0+
- **State Management**: Provider / Riverpod
- **HTTP Client**: Dio with retry logic
- **WebSocket**: Socket.io for real-time updates
- **Authentication**: JWT tokens (secure storage)
- **Database**: Hive (local caching)

## API Integration

### Authentication

```dart
// Login
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "SecurePass123"
}

// Response includes access_token and refresh_token
```

### Real-Time Queue Updates

WebSocket connection for live updates:

```dart
// Connect
WS /api/v1/ws/queue/{doctor_id}

// Receive queue position updates
{
  "type": "queue_update",
  "queue_position": 3,
  "estimated_wait_minutes": 15
}
```

## Token Management

```dart
// Tokens stored securely
- AccessToken: 30-minute expiry
- RefreshToken: 7-day expiry
- Stored in: FlutterSecureStorage

// Auto-refresh before expiry
if (tokenExpiresIn < 5 minutes) {
  refreshToken()
}
```

## Offline Support

- Cache user profile locally
- Queue updates only available online
- Medical records cached after first load
- Sync when connection restored

## Building for Release

### Android

```bash
flutter build apk --release
# Output: build/app/outputs/flutter-apk/app-release.apk

# Or for App Bundle (Google Play)
flutter build appbundle --release
# Output: build/app/outputs/bundle/release/app-release.aab
```

### iOS

```bash
flutter build ios --release
# Open in Xcode for final processing
open ios/Runner.xcworkspace

# Archive and upload to App Store
```

## Testing

```bash
# Run all tests
flutter test

# Run specific test file
flutter test test/unit/auth_test.dart

# With coverage
flutter test --coverage
```

## Troubleshooting

**API Connection Failed**
- Verify API_BASE_URL in app_config.dart
- Check if backend is running
- Ensure device can reach backend server

**WebSocket Connection Issues**
- Verify WebSocket endpoint is correct
- Check firewall rules
- Ensure backend WebSocket is enabled

**Token Expired Error**
- App should auto-refresh token
- If persists, clear app cache and re-login
- Delete app and reinstall

**Build Issues**
- Update Flutter: `flutter upgrade`
- Clean build: `flutter clean && flutter pub get`
- Check minimum SDK versions in pubspec.yaml

---

For backend setup, see [2_BACKEND_SETUP.md](2_BACKEND_SETUP.md)  
For deployment, see [5_DEPLOYMENT.md](5_DEPLOYMENT.md)
