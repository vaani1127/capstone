# HealthSaathi Project Documentation

Complete, consolidated documentation for the HealthSaathi healthcare management system.

## Quick Navigation

### 🚀 Getting Started

**First time developers?** Start here:
1. [1_QUICK_START.md](1_QUICK_START.md) - Get running in 5 minutes
2. [2_BACKEND_SETUP.md](2_BACKEND_SETUP.md) - Backend configuration details
3. [3_DATABASE_SETUP.md](3_DATABASE_SETUP.md) - Database setup and migrations

### 📚 API & Development

- [4_API_DOCUMENTATION.md](4_API_DOCUMENTATION.md) - Complete API reference, authentication, all endpoints
  - Public endpoints (registration, login)
  - Protected endpoints by role
  - Request/response examples
  - Security requirements
  - Code examples for endpoint protection
  - Anomaly Detection endpoints (alerts list, acknowledge, stats, admin WebSocket)
- [8_BLOCKCHAIN_AUDIT.md](8_BLOCKCHAIN_AUDIT.md) - Blockchain audit chain deep-dive
  - Hash-linkage design and table schema
  - `create_audit_entry` API and transaction safety
  - Verification workflow and REST endpoints

### 📱 Mobile Development

- [6_MOBILE_APP.md](6_MOBILE_APP.md) - Flutter mobile app guide
  - Installation and setup
  - Project structure
  - Features by role
  - API integration
  - Building for release

### 🚢 Deployment

- [5_DEPLOYMENT.md](5_DEPLOYMENT.md) - Production deployment
  - Docker setup
  - AWS deployment with Terraform
  - SSL/TLS configuration
  - Backup & recovery
  - Health checks & monitoring

### 👥 User Guides

- [7_USER_GUIDE.md](7_USER_GUIDE.md) - Complete user guide for all roles
  - Patient: Booking appointments, checking queue, medical history
  - Doctor: Managing queue, creating medical records, prescriptions
  - Nurse: Walk-in registration, queue management
  - Admin: User management, audit logs, security monitoring

### 📋 Project Overview

- [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) - Complete capstone project report
  - System architecture and design
  - Literature survey and research
  - Objectives and methodology
  - Individual roles and outcomes
- [CAPSTONE_REPORT.md](CAPSTONE_REPORT.md) - Alternative link to project overview

---

## Documentation Organization

### By Role

**For System Administrators**
1. Read: [1_QUICK_START.md](1_QUICK_START.md)
2. Read: [5_DEPLOYMENT.md](5_DEPLOYMENT.md)
3. Reference: [7_USER_GUIDE.md](7_USER_GUIDE.md) (Admin section)

**For Backend Developers**
1. Read: [2_BACKEND_SETUP.md](2_BACKEND_SETUP.md)
2. Read: [3_DATABASE_SETUP.md](3_DATABASE_SETUP.md)
3. Reference: [4_API_DOCUMENTATION.md](4_API_DOCUMENTATION.md)

**For Mobile Developers**
1. Read: [6_MOBILE_APP.md](6_MOBILE_APP.md)
2. Reference: [4_API_DOCUMENTATION.md](4_API_DOCUMENTATION.md)

**For Clinical Users**
1. Read: [7_USER_GUIDE.md](7_USER_GUIDE.md) (your role section)
2. Reference: [1_QUICK_START.md](1_QUICK_START.md)

**For Project Managers/Stakeholders**
1. Read: [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
2. Skim: [1_QUICK_START.md](1_QUICK_START.md)
3. Reference: [7_USER_GUIDE.md](7_USER_GUIDE.md)

---

## Key Information Summary

### System Architecture

```
┌─────────────────────────────────────┐
│   Flutter Mobile App (iOS/Android)  │
│   - Patient, Doctor, Nurse, Admin   │
│   - Real-time Queue Updates         │
│   - Medical Records Access          │
└─────────────────┬───────────────────┘
                  │ JWT Tokens
                  │
┌─────────────────▼───────────────────┐
│   FastAPI Backend (Python)          │
│   - REST API (35+ endpoints)        │
│   - WebSocket for real-time data    │
│   - JWT Authentication & RBAC       │
│   - Blockchain record integrity     │
│   - ML anomaly detection (IsoForest)│
└─────────────────┬───────────────────┘
                  │ SQL
┌─────────────────▼───────────────────┐
│   PostgreSQL Database               │
│   - 7 core tables                   │
│   - Role-based access control       │
│   - Audit trail & logging           │
│   - Blockchain hash chain           │
│   - Anomaly alerts                  │
└─────────────────────────────────────┘
```

### User Roles

| Role | Permissions | Access |
|------|-------------|--------|
| **Patient** | Schedule appointments, view medical history | View own records only |
| **Doctor** | Create medical records, manage queue | All assigned patients |
| **Nurse** | Register walk-ins, manage queue | All clinic patients |
| **Admin** | User management, audit logs, security | Full system access |

### Core Features

✅ **Authentication** - JWT-based with role-based access control  
✅ **Real-time Queue** - WebSocket-driven live queue position  
✅ **Medical Records** - Version-controlled with full audit trail  
✅ **Blockchain Integrity** - SHA-256 hash chain for tamper detection  
✅ **Appointment System** - Scheduled and walk-in support  
✅ **Behavioural Anomaly Detection** - IsolationForest + SHAP real-time insider-threat alerts (see [4_API_DOCUMENTATION.md](4_API_DOCUMENTATION.md#anomaly-detection-endpoints----a-admin-only))  
✅ **Mobile-First** - Cross-platform Flutter app  
✅ **Production Ready** - Docker, Kubernetes, AWS deployment  

### Technology Stack

- **Backend**: FastAPI, Python 3.9+
- **Database**: PostgreSQL 13+
- **Mobile**: Flutter 3.0+ (iOS + Android)
- **Real-time**: WebSocket
- **Auth**: JWT + bcrypt
- **Infrastructure**: Docker, Terraform, AWS
- **Testing**: 85%+ code coverage

---

## Frequently Used Commands

### Backend Development

```bash
# Setup (from project root)
cd backend
pip install -r requirements.txt
cp ../.env.example ../.env       # then edit .env

# Database (first run)
python setup_tables.py           # create all tables
python load_test_data.py         # optional: load sample data

# Run (development)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use Docker dev compose (no local PostgreSQL needed)
cd ../deployment/docker
docker-compose -f docker-compose.dev.yml up --build

# Tests (SQLite in-memory — no PostgreSQL required)
cd backend
pytest
```

### Mobile Development

```bash
# Setup
cd mobile
flutter pub get

# Run
flutter run -d android          # Android emulator
flutter run -d ios              # iOS simulator

# Build
flutter build apk --release     # Android
flutter build ios --release     # iOS
```

### Deployment

```bash
# Docker production
cd deployment/docker
docker-compose -f docker-compose.production.yml up --build -d

# AWS Terraform
cd deployment/aws/terraform
terraform init && terraform apply
```

---

## Important Endpoints

All endpoints require `Authorization: Bearer <token>` header (except auth/register, auth/login, auth/refresh)

- **API Base**: `http://localhost:8000/api/v1`
- **API Docs**: `http://localhost:8000/api/docs`
- **Liveness probe**: `http://localhost:8000/health`
- **Readiness probe**: `http://localhost:8000/ready` (returns 503 if DB unavailable)

---

## File Structure

```
documentation/
├── 1_QUICK_START.md              # Quick start (Docker and bare Python)
├── 2_BACKEND_SETUP.md            # Full env-var reference, tests, dev workflow
├── 3_DATABASE_SETUP.md           # Database schema and migration details
├── 4_API_DOCUMENTATION.md        # Complete REST + WebSocket endpoint reference
├── 5_DEPLOYMENT.md               # Docker, Nginx, Terraform, SSL, backup/restore
├── 6_MOBILE_APP.md               # Flutter mobile app guide
├── 7_USER_GUIDE.md               # End-user guide for all four roles
├── 8_BLOCKCHAIN_AUDIT.md         # Audit chain design, API, and verification workflow
├── PROJECT_OVERVIEW.md           # Capstone project report
├── CAPSTONE_REPORT.md            # (same as PROJECT_OVERVIEW)
└── README.md                     # This file
```

---

## Support

For issues or questions:
1. Check relevant documentation file
2. Review "Troubleshooting" section in that file
3. Check API Docs at `http://localhost:8000/api/docs`
4. Review project repository for example code

---

**Last Updated**: April 2024  
**Version**: 1.0  
**Status**: Production Ready
