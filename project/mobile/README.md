# HealthSaathi Mobile App

A mobile-based secure healthcare management system built with Flutter.

## Features

- User authentication with JWT tokens
- Role-based access (Patient, Doctor, Nurse, Admin)
- Appointment booking and management
- Real-time queue status via WebSockets
- Medical records and prescription management
- Blockchain-based integrity verification

## Getting Started

### Prerequisites

- Flutter SDK (>=3.0.0)
- Dart SDK
- Android Studio / Xcode (for mobile development)

### Installation

1. Install dependencies:
```bash
flutter pub get
```

2. Configure API endpoint in `lib/config/app_config.dart`

3. Run the app:
```bash
flutter run
```

## Project Structure

```
lib/
├── main.dart                 # App entry point
├── config/                   # Configuration files
│   └── app_config.dart       # API base URL and settings
├── models/                   # Data models
│   ├── user.dart
│   ├── appointment.dart
│   ├── medical_record.dart
│   └── doctor.dart
├── services/                 # API and WebSocket services
│   ├── api_client.dart
│   └── websocket_service.dart
├── providers/                # State management
├── screens/                  # UI screens
└── widgets/                  # Reusable widgets
```

## Backend API

The app connects to the HealthSaathi backend API running at `http://localhost:8000` by default.

## License

Proprietary - HealthSaathi Healthcare System
