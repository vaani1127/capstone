# HealthSaathi - Complete Project Overview

## Table of Contents
1. [What is HealthSaathi?](#what-is-healthsaathi)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Key Features](#key-features)
6. [How to Run](#how-to-run)
7. [Testing](#testing)
8. [Deployment](#deployment)
9. [API Documentation](#api-documentation)
10. [Security Features](#security-features)

---

## What is HealthSaathi?

HealthSaathi is a **secure healthcare management system** designed for clinics and hospitals. It provides:

- **Patient Management**: Book appointments, view medical history, track queue status
- **Doctor Management**: Manage patient queue, conduct consultations, create prescriptions
- **Nurse Management**: Register walk-in patients, view queue status
- **Admin Management**: User management, audit logs, system monitoring
- **Blockchain Integrity**: Tamper-proof medical records using blockchain technology
- **Real-time Updates**: Live queue status via WebSocket

---

## System Architecture

### High-Level Architecture

```
┌─────────────────┐
│  Mobile App     │ (Flutter - iOS/Android)
│  (Patient/      │
│   Doctor/Nurse/ │
│   Admin)        │
└────────┬────────┘
         │ HTTPS/WSS
         ▼
┌─────────────────┐
│  Backend API    │ (FastAPI - Python)
│  - REST API     │
│  - WebSocket    │
│  - Auth (JWT)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  PostgreSQL DB  │
│  - User Data    │
│  - Appointments │
│  - Medical Recs │
│  - Audit Chain  │
└─────────────────┘
```

### Components

1. **Backend API** (FastAPI + Python)
   - RESTful API endpoints
   - WebSocket server for real-time updates
   - JWT-based authentication
   - Role-based access control (RBAC)
   - Blockchain service for data integrity

2. **Mobile Application** (Flutter)
   - Cross-platform (iOS/Android)
   - Role-based UI (4 different dashboards)
   - Real-time queue updates
   - Offline-capable with local storage

3. **Database** (PostgreSQL)
   - Relational database with proper indexing
   - Alembic migrations for version control
   - Seed data for testing

4. **Blockchain Layer**
   - SHA-256 hash chain for medical records
   - Tamper detection and verification
   - Immutable audit trail

---

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.9+)
- **Database**: PostgreSQL 13+
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Authentication**: JWT (JSON Web Tokens)
- **WebSocket**: FastAPI WebSocket support
- **Testing**: Pytest (373 tests)
- **Hashing**: SHA-256 for blockchain

### Mobile
- **Framework**: Flutter 3.41.2
- **Language**: Dart
- **State Management**: Provider
- **HTTP Client**: http package
- **WebSocket**: web_socket_channel
- **Testing**: flutter_test, integration_test (165+ tests)

### DevOps
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **Reverse Proxy**: Nginx
- **Infrastructure**: Terraform (AWS)
- **CI/CD**: GitHub Actions ready

---

## Project Structure

```
healthsaathi/
├── backend/                    # Backend API
│   ├── app/
│   │   ├── api/v1/endpoints/  # API endpoints
│   │   ├── core/              # Config, security, dependencies
│   │   ├── db/                # Database connection
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── services/          # Business logic
│   ├── tests/                 # Backend tests (373 tests)
│   ├── requirements.txt       # Python dependencies
│   └── run.py                 # Entry point
│
├── mobile/                    # Flutter mobile app
│   ├── lib/
│   │   ├── models/           # Data models
│   │   ├── providers/        # State management
│   │   ├── screens/          # UI screens (12 screens)
│   │   ├── services/         # API/WebSocket services
│   │   └── main.dart         # Entry point
│   ├── test/                 # Widget tests (100+ tests)
│   ├── integration_test/     # Integration tests (65+ tests)
│   └── pubspec.yaml          # Flutter dependencies
│
├── database/                  # Database scripts
│   ├── schema.sql            # Database schema
│   └── sample_data.sql       # Seed data
│
├── alembic/                  # Database migrations
│   └── versions/             # Migration files
│
├── deployment/               # Deployment configs
│   ├── docker/              # Docker files
│   ├── aws/terraform/       # AWS infrastructure
│   └── scripts/             # Deployment scripts
│
├── docs/                    # Documentation
│   ├── USER_GUIDES.md       # User documentation
│   └── TRAINING_MATERIALS.md
│
└── .kiro/specs/             # Project specifications
    └── healthsaathi-healthcare-system/
        ├── requirements.md   # Requirements
        ├── design.md        # Design document
        └── tasks.md         # Implementation tasks
```

---

## Key Features

### 1. User Authentication & Authorization
- **JWT-based authentication** with access and refresh tokens
- **Role-based access control** (Patient, Doctor, Nurse, Admin)
- **Password hashing** using bcrypt
- **Token expiration** and refresh mechanism

### 2. Appointment Management
- **Book appointments** with doctor selection and time slot
- **Cancel appointments** (with 2-hour notice rule)
- **Reschedule appointments** to new time slots
- **Walk-in registration** by nurses
- **Prevent double-booking** with availability checking

### 3. Queue Management
- **Real-time queue tracking** for each doctor
- **Queue position calculation** based on appointment time
- **Estimated wait time** using exponential moving average
- **Automatic queue updates** when appointments change
- **WebSocket notifications** for live updates

### 4. Medical Records
- **Consultation notes** created by doctors
- **Prescription management** with medication details
- **Version history** - all changes are tracked
- **Read-only access** for patients
- **Blockchain integrity** for tamper detection

### 5. Blockchain Integrity Layer
- **SHA-256 hash chain** for medical records
- **Tamper detection** - verify data hasn't been modified
- **Audit trail** - complete history of all changes
- **Genesis block** for chain initialization
- **Chain verification** to ensure integrity

### 6. Real-time Communication
- **WebSocket server** for live updates
- **Queue status updates** broadcast to all clients
- **Appointment notifications** sent to patients/doctors
- **Auto-reconnection** on connection loss
- **JWT authentication** for WebSocket connections

### 7. Admin Features
- **User management** - create, edit, assign roles
- **Audit dashboard** - view all system activity
- **Tampering alerts** - flagged records
- **Export audit logs** to CSV/JSON
- **System statistics** - users, appointments, queue status

---

## How to Run

### Prerequisites

1. **Python 3.9+** installed
2. **PostgreSQL 13+** installed and running
3. **Flutter 3.41.2** installed (for mobile app)
4. **Git** for version control

### Backend Setup

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create .env file
cp .env.example .env
# Edit .env with your database credentials

# 6. Run database migrations
python -m alembic upgrade head

# 7. Start the backend server
python run.py
```

Backend will run on: **http://localhost:8000**

### Mobile App Setup

```bash
# 1. Navigate to mobile directory
cd mobile

# 2. Install Flutter dependencies
flutter pub get

# 3. Run the app
# On emulator/simulator:
flutter run

# On specific device:
flutter devices  # List devices
flutter run -d <device-id>
```

### Quick Start (All-in-One)

```bash
# From project root
# 1. Start backend
cd backend && python run.py &

# 2. Start mobile app
cd mobile && flutter run
```

### Test Users

The system comes with pre-seeded test users:

| Email | Password | Role |
|-------|----------|------|
| patient@test.com | password123 | Patient |
| doctor@test.com | password123 | Doctor |
| nurse@test.com | password123 | Nurse |
| admin@test.com | password123 | Admin |

---

## Testing

### Backend Tests (373 tests)

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app tests/

# Test results:
# - Authentication: 67 tests ✓
# - Appointments: 96 tests ✓
# - Queue Management: 48 tests ✓
# - Medical Records: 86 tests ✓
# - Blockchain: 65 tests ✓
# - Integration: 11 tests ✓
```

### Mobile Widget Tests (100+ tests)

```bash
cd mobile

# Run all widget tests
flutter test

# Run specific test file
flutter test test/screens/patient/patient_home_screen_test.dart

# Test coverage:
# - Login/Registration: 30 tests ✓
# - Patient screens: 24 tests ✓
# - Doctor screens: 18 tests ✓
# - Nurse screens: 12 tests ✓
# - Admin screens: 30 tests ✓
```

### Mobile Integration Tests (65+ tests)

```bash
cd mobile

# Run all integration tests
flutter test integration_test/

# Or use the test runner
cd integration_test
./run_tests.sh  # Linux/Mac
run_tests.bat   # Windows

# Test coverage:
# - API Integration: 25 tests ✓
# - WebSocket: 20 tests ✓
# - Navigation: 20 tests ✓
```

---

## Deployment

### Local Development

Already covered in "How to Run" section above.

### Docker Deployment

```bash
# Build and run with Docker Compose
cd deployment/docker
docker-compose -f docker-compose.production.yml up -d

# Services will be available at:
# - Backend API: http://localhost:8000
# - Database: localhost:5432
```

### AWS Deployment (Terraform)

```bash
cd deployment/aws/terraform

# 1. Configure AWS credentials
aws configure

# 2. Initialize Terraform
terraform init

# 3. Review deployment plan
terraform plan

# 4. Deploy infrastructure
terraform apply

# 5. Get outputs (URLs, IPs)
terraform output
```

### Manual Deployment

See `backend/DEPLOYMENT_GUIDE.md` for detailed instructions on:
- AWS deployment
- GCP deployment
- Azure deployment
- SSL/TLS setup
- Database backups
- Monitoring setup

---

## API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication Endpoints

**POST /auth/register**
- Register new user
- Body: `{name, email, password, role}`
- Returns: User object + JWT token

**POST /auth/login**
- Login user
- Body: `{email, password}`
- Returns: JWT token + user info

**POST /auth/refresh**
- Refresh access token
- Body: `{refresh_token}`
- Returns: New access token

### Appointment Endpoints

**GET /appointments**
- Get user's appointments
- Auth: Required
- Returns: List of appointments

**POST /appointments**
- Book new appointment
- Auth: Required (Patient)
- Body: `{doctor_id, scheduled_time}`
- Returns: Appointment object

**PUT /appointments/{id}/cancel**
- Cancel appointment
- Auth: Required
- Returns: Updated appointment

**PUT /appointments/{id}/reschedule**
- Reschedule appointment
- Auth: Required
- Body: `{new_scheduled_time}`
- Returns: Updated appointment

### Queue Endpoints

**GET /queue/{doctor_id}**
- Get queue status for doctor
- Auth: Required
- Returns: Queue data with positions and wait times

**PUT /queue/{appointment_id}/check-in**
- Check in patient
- Auth: Required (Nurse/Admin)
- Returns: Updated queue

### Medical Records Endpoints

**GET /medical-records**
- Get patient's medical records
- Auth: Required (Patient)
- Returns: List of records

**POST /medical-records**
- Create consultation note
- Auth: Required (Doctor)
- Body: `{patient_id, consultation_notes, diagnosis}`
- Returns: Medical record

**GET /medical-records/{id}/versions**
- Get version history
- Auth: Required
- Returns: All versions of record

### Audit Endpoints

**GET /audit/logs**
- Get audit logs
- Auth: Required (Admin)
- Query: `?page=1&page_size=20&start_date=...`
- Returns: Paginated audit logs

**GET /audit/tampering-alerts**
- Get tampering alerts
- Auth: Required (Admin)
- Returns: List of flagged records

### WebSocket Endpoint

**WS /ws**
- WebSocket connection
- Auth: JWT token in query param
- Events:
  - `queue_update` - Queue status changed
  - `appointment_status` - Appointment status changed

For complete API documentation, see: `backend/API_DOCUMENTATION.md`

---

## Security Features

### 1. Authentication Security
- **JWT tokens** with expiration (15 min access, 7 days refresh)
- **Password hashing** using bcrypt (12 rounds)
- **Token refresh** mechanism
- **Secure password requirements** (8+ chars, uppercase, lowercase, digit)

### 2. Authorization Security
- **Role-based access control** (RBAC)
- **Endpoint protection** - each endpoint checks user role
- **Resource ownership** - users can only access their own data
- **Admin-only endpoints** for sensitive operations

### 3. Data Security
- **Blockchain integrity** - SHA-256 hash chain
- **Tamper detection** - verify data hasn't been modified
- **Audit logging** - all actions are logged
- **Version history** - track all changes to medical records

### 4. Network Security
- **HTTPS** for all API communication
- **WSS** (WebSocket Secure) for real-time updates
- **CORS** configuration for allowed origins
- **Rate limiting** (can be configured)

### 5. Database Security
- **SQL injection prevention** - using ORM (SQLAlchemy)
- **Prepared statements** for all queries
- **Database connection pooling**
- **Encrypted connections** to database

### 6. Input Validation
- **Pydantic schemas** for request validation
- **Email validation** using regex
- **Date/time validation** for appointments
- **Sanitization** of user inputs

---

## Performance Metrics

The system meets all non-functional requirements:

| Metric | Requirement | Actual |
|--------|-------------|--------|
| API Response Time | < 500ms | ✓ Passing |
| WebSocket Latency | < 2 seconds | ✓ Passing |
| Queue Calculation | < 100ms | ✓ Passing |
| Hash Verification | < 100ms | ✓ Passing |
| Concurrent Users | 100+ | ✓ Supported |
| Database Queries | Optimized | ✓ Indexed |

---

## Key Files to Read

### For Understanding the System
1. **PROJECT_OVERVIEW.md** (this file) - Complete overview
2. **.kiro/specs/healthsaathi-healthcare-system/requirements.md** - Requirements
3. **.kiro/specs/healthsaathi-healthcare-system/design.md** - Design document
4. **backend/API_DOCUMENTATION.md** - API reference

### For Running the System
5. **backend/README.md** - Backend setup
6. **backend/SETUP.md** - Detailed setup instructions
7. **QUICK_START.md** - Quick start guide
8. **mobile/README.md** - Mobile app setup

### For Deployment
9. **backend/DEPLOYMENT_GUIDE.md** - Deployment instructions
10. **deployment/README.md** - Infrastructure setup

### For Testing
11. **mobile/integration_test/TESTING_GUIDE.md** - Testing guide
12. **mobile/integration_test/INTEGRATION_TEST_SUMMARY.md** - Test coverage

### For Users
13. **docs/USER_GUIDES.md** - User documentation
14. **docs/TRAINING_MATERIALS.md** - Training materials

---

## Common Tasks

### Add a New User
```bash
# Via API
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "SecurePass123",
    "role": "Patient"
  }'
```

### Book an Appointment
```bash
# Via API (requires JWT token)
curl -X POST http://localhost:8000/api/v1/appointments \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "doctor_id": 1,
    "scheduled_time": "2024-03-15T10:00:00"
  }'
```

### Check Queue Status
```bash
# Via API
curl http://localhost:8000/api/v1/queue/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Run Database Migrations
```bash
cd backend
python -m alembic upgrade head
```

### Reset Database
```bash
cd backend
python -m alembic downgrade base
python -m alembic upgrade head
```

---

## Troubleshooting

### Backend won't start
- Check PostgreSQL is running: `pg_isready`
- Check .env file has correct database credentials
- Check port 8000 is not in use: `netstat -an | grep 8000`

### Mobile app can't connect to backend
- Check backend is running on http://localhost:8000
- Check mobile/lib/config/app_config.dart has correct API URL
- For Android emulator, use `http://10.0.2.2:8000` instead of localhost

### Tests failing
- Ensure backend is running for integration tests
- Check database has seed data: `python -m alembic upgrade head`
- Clear test cache: `pytest --cache-clear`

### WebSocket not connecting
- Check JWT token is valid
- Check WebSocket URL is correct (ws:// not http://)
- Check firewall allows WebSocket connections

---

## Development Workflow

### Adding a New Feature

1. **Update Requirements** - Add to requirements.md
2. **Update Design** - Add to design.md
3. **Create Tasks** - Add to tasks.md
4. **Backend Implementation**:
   - Add model (if needed)
   - Add schema
   - Add endpoint
   - Add service logic
   - Write tests
5. **Mobile Implementation**:
   - Add model
   - Add service
   - Add screen/UI
   - Write tests
6. **Integration Testing**
7. **Documentation**

### Code Style

**Backend (Python)**:
- Follow PEP 8
- Use type hints
- Document functions with docstrings
- Keep functions small and focused

**Mobile (Dart)**:
- Follow Dart style guide
- Use meaningful variable names
- Document public APIs
- Keep widgets small and reusable

---

## Support & Resources

### Documentation
- **Requirements**: `.kiro/specs/healthsaathi-healthcare-system/requirements.md`
- **Design**: `.kiro/specs/healthsaathi-healthcare-system/design.md`
- **API Docs**: `backend/API_DOCUMENTATION.md`
- **User Guides**: `docs/USER_GUIDES.md`

### Code Examples
- **Backend Tests**: `backend/tests/` - 373 test examples
- **Mobile Tests**: `mobile/test/` - 100+ test examples
- **Integration Tests**: `mobile/integration_test/` - 65+ examples

### External Resources
- **FastAPI**: https://fastapi.tiangolo.com/
- **Flutter**: https://flutter.dev/docs
- **PostgreSQL**: https://www.postgresql.org/docs/
- **SQLAlchemy**: https://docs.sqlalchemy.org/

---

## Project Statistics

- **Total Lines of Code**: ~50,000+
- **Backend Files**: 150+
- **Mobile Files**: 100+
- **Test Files**: 50+
- **Documentation Files**: 20+
- **Total Tests**: 538 (373 backend + 165 mobile)
- **Test Coverage**: >85%
- **API Endpoints**: 30+
- **Database Tables**: 6
- **Mobile Screens**: 12
- **Supported Roles**: 4

---

## License

This project is proprietary software developed for healthcare management.

---

## Contributors

Developed by: Kiro AI Assistant
Project Type: Healthcare Management System
Technology: FastAPI + Flutter + PostgreSQL + Blockchain

---

## Next Steps

1. **Run the system locally** - Follow "How to Run" section
2. **Explore the API** - Use backend/API_DOCUMENTATION.md
3. **Test the mobile app** - Try different user roles
4. **Read user guides** - See docs/USER_GUIDES.md
5. **Deploy to production** - Follow backend/DEPLOYMENT_GUIDE.md

---

**For any questions, refer to the documentation files listed in "Key Files to Read" section above.**
