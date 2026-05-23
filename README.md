3# HealthSaathi

A mobile-based secure healthcare management system for clinics and hospitals. HealthSaathi provides role-based access for patients, doctors, nurses, and administrators, with appointment booking, real-time queue management, medical record handling, audit logging, and blockchain-style integrity verification for sensitive healthcare records.

> **Repository status:** This repository contains the backend API, PostgreSQL database schema, deployment files, Flutter mobile project scaffold, project documentation, and research/proposal documents.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Repository Structure](#repository-structure)
- [Core System Modules](#core-system-modules)
- [Documentation Map](#documentation-map)
- [Prerequisites](#prerequisites)
- [Local Setup](#local-setup)
- [Backend API](#backend-api)
- [Database Setup](#database-setup)
- [Mobile App](#mobile-app)
- [Deployment](#deployment)
- [Test Credentials](#test-credentials)
- [Environment Variables](#environment-variables)
- [Research and Proposal Documents](#research-and-proposal-documents)
- [Future Scope](#future-scope)
- [License](#license)

---

## Project Overview

HealthSaathi is designed to solve common clinic and hospital workflow problems such as:

- Manual appointment handling
- Long and unclear patient queues
- Fragmented patient records
- Limited auditability of medical data changes
- Weak role-based access separation
- Lack of real-time queue visibility for patients and staff

The system uses a **FastAPI backend**, **PostgreSQL database**, and **Flutter mobile app scaffold** to support healthcare workflows across four user roles:

| Role | Main Responsibilities |
|---|---|
| Patient | Register/login, book appointments, view queue status, access medical history |
| Doctor | Manage consultation queue, create medical records, add diagnosis and prescriptions |
| Nurse | Register walk-in patients, check in patients, assist with queue management |
| Admin | Manage users, monitor audit logs, verify record integrity, oversee the system |

---

## Key Features

- JWT-based authentication
- Role-Based Access Control (RBAC)
- Patient profile management
- Doctor profile and specialization management
- Appointment booking and queue tracking
- Real-time queue updates using WebSocket
- Medical record creation and versioning
- Prescription and diagnosis storage
- Audit chain for tamper detection
- PostgreSQL schema with migration support
- Docker-based production deployment setup
- AWS Terraform deployment files
- Detailed setup, API, deployment, and user documentation

---

## Technology Stack

### Backend

- Python 3.9+
- FastAPI
- Uvicorn
- SQLAlchemy
- Alembic
- PostgreSQL
- Pydantic
- JWT using `python-jose`
- Password hashing using `passlib`
- WebSocket support
- Pytest

### Database

- PostgreSQL 13+
- SQL schema scripts
- Alembic migrations
- Sample data scripts
- Audit chain table for integrity verification

### Mobile

- Flutter
- Dart
- Provider
- HTTP package
- WebSocket channel
- Shared Preferences
- Android project scaffold

### Deployment

- Docker
- Docker Compose
- Nginx
- Redis for optional WebSocket scaling
- AWS Terraform files
- Backup and restore shell scripts

---

## Repository Structure

```text
capstone-main/
│
├── README.md
│
├── docs/
│
├── project/
│
└── research/
```

---

## Core System Modules

### 1. Authentication and Authorization

Located in:

```text
project/backend/app/api/v1/endpoints/auth.py
project/backend/app/core/security.py
```

Includes:

- User registration
- User login
- JWT access tokens
- Refresh tokens
- Password hashing
- Role-based access validation

### 2. User Management

Located in:

```text
project/backend/app/api/v1/endpoints/users.py
project/backend/app/models/user.py
project/backend/app/schemas/user.py
```

Supports user profiles for Admin, Doctor, Nurse, and Patient roles.

### 3. Appointment Management

Located in:

```text
project/backend/app/api/v1/endpoints/appointments.py
project/backend/app/models/appointment.py
project/backend/app/services/appointment_service.py
```

Handles:

- Appointment booking
- Appointment status updates
- Doctor-wise appointment lists
- Patient appointment history

### 4. Queue Management

Located in:

```text
project/backend/app/api/v1/endpoints/queue.py
project/backend/app/api/v1/endpoints/websocket.py
project/backend/app/services/websocket_manager.py
```

Supports:

- Live queue updates
- Patient queue position tracking
- Estimated wait time calculation
- WebSocket-based real-time communication

### 5. Medical Records

Located in:

```text
project/backend/app/api/v1/endpoints/medical_records.py
project/backend/app/models/medical_record.py
project/backend/app/schemas/medical_record.py
```

Supports:

- Diagnosis storage
- Prescription storage
- Consultation notes
- Medical record versioning
- Patient medical history

### 6. Audit Chain and Integrity Verification

Located in:

```text
project/backend/app/api/v1/endpoints/audit.py
project/backend/app/models/audit_chain.py
project/backend/app/services/blockchain_service.py
```

Includes:

- SHA-256 based hash chain
- Previous-hash linking
- Tamper detection
- Medical record integrity verification
- Admin audit monitoring

---

## Documentation Map

The repository already includes detailed documentation inside `project/documentation/`.

| Document | Purpose |
|---|---|
| `1_QUICK_START.md` | Fast local setup guide |
| `2_BACKEND_SETUP.md` | Backend installation and configuration |
| `3_DATABASE_SETUP.md` | Database schema, setup scripts, and SQL details |
| `4_API_DOCUMENTATION.md` | API endpoints, request bodies, responses, and auth flow |
| `5_DEPLOYMENT.md` | Docker, AWS, SSL, backup, and monitoring setup |
| `6_MOBILE_APP.md` | Flutter mobile app guide |
| `7_USER_GUIDE.md` | Role-wise usage guide for patients, doctors, nurses, and admins |
| `PROJECT_OVERVIEW.md` | Full capstone project overview |
| `CAPSTONE_REPORT.md` | Capstone report version |
| `TESTING_DEPLOYMENT.md` | Testing and deployment notes |

---

## Prerequisites

Before running the project locally, install:

- Python 3.9 or higher
- PostgreSQL 13 or higher
- pip
- Git
- Flutter SDK, only if working on the mobile app
- Docker and Docker Compose, only if using containerized deployment

---

## Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/vaani1127/capstone.git
cd capstone
```

If your extracted folder is named `capstone-main`, move into it:

```bash
cd capstone-main
```

### 2. Move into the Project Folder

```bash
cd project
```

### 3. Create Environment File

```bash
cp .env.example .env
```

Edit `.env` and set your PostgreSQL connection string and secret key.

Example for local PostgreSQL:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/healthsaathi
SECRET_KEY=change-this-to-a-secure-random-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
HOST=0.0.0.0
PORT=8000
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

### 4. Install Backend Dependencies

From the `project/` folder:

```bash
pip install -r requirements.txt
```

Or from the backend folder:

```bash
cd backend
pip install -r requirements.txt
```

---

## Backend API

### Run the Backend Locally

From:

```text
project/backend/
```

Run:

```bash
python setup_tables.py
python load_test_data.py
python run.py
```

The API will be available at:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/api/docs
```

ReDoc documentation:

```text
http://localhost:8000/api/redoc
```

Health check endpoint:

```text
http://localhost:8000/health
```

---

## Database Setup

The database files are located in:

```text
project/database/
```

Important files:

| File | Purpose |
|---|---|
| `schema.sql` | Creates all main PostgreSQL tables |
| `sample_data.sql` | Inserts sample users, patients, doctors, appointments, and records |
| `verify_schema.sql` | Verifies database structure |
| `validate_schema.sh` | Shell script for schema validation |

### Main Tables

| Table | Purpose |
|---|---|
| `users` | Stores authentication and role information |
| `patients` | Stores patient demographic details |
| `doctors` | Stores doctor profile and specialization information |
| `appointments` | Stores appointment and queue data |
| `medical_records` | Stores diagnosis, prescription, and consultation information |
| `audit_chain` | Stores integrity hashes and audit trail records |

### Setup Using Scripts

From:

```text
project/backend/
```

Run:

```bash
python setup_tables.py
python load_test_data.py
```

---

## Mobile App

The Flutter mobile project is located in:

```text
project/mobile/
```

Install dependencies:

```bash
cd project/mobile
flutter pub get
```

Run on Android:

```bash
flutter run -d android
```

The current ZIP contains the Flutter configuration and Android project scaffold. The mobile documentation describes the planned role-based screens and API integration flow.

---

## Deployment

### Docker Deployment

Docker files are located in:

```text
project/deployment/docker/
```

Run production Docker Compose:

```bash
cd project/deployment/docker
docker-compose -f docker-compose.production.yml up -d
```

This setup includes:

- PostgreSQL database container
- FastAPI backend container
- Nginx reverse proxy
- Redis container for optional WebSocket scaling

### AWS Deployment

Terraform files are located in:

```text
project/deployment/aws/terraform/
```

Basic flow:

```bash
cd project/deployment/aws/terraform
terraform init
terraform plan
terraform apply
```

### Utility Scripts

Deployment scripts are available in:

```text
project/deployment/scripts/
```

| Script | Purpose |
|---|---|
| `deploy.sh` | Deployment helper |
| `backup-database.sh` | Database backup |
| `restore-database.sh` | Database restore |
| `health-check.sh` | Production health check |
| `setup-ssl.sh` | SSL setup helper |

---

## Environment Variables

Main environment file:

```text
project/.env.example
```

Common variables:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL database connection URL |
| `SECRET_KEY` | JWT signing key |
| `ALGORITHM` | JWT algorithm, usually `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry time |
| `HOST` | Backend host |
| `PORT` | Backend port |
| `DEBUG` | Development debug mode |
| `ALLOWED_ORIGINS` | CORS allowed origins |

---

## Research and Proposal Documents

The repository includes capstone research and proposal material in two places:
### `docs/`

Contains final proposal and consolidated MediFlow research documents.

### `research/`

Contains SMART on FHIR security and healthcare interoperability research:

- SMART on FHIR overview
- Privacy and security issues
- Data integrity challenges
- Problem analysis
- Solution framework
- Research references
- Existing solutions and novelty analysis

These documents support the research background of the project.

---

## Future Scope

Possible improvements:

- Complete Flutter UI implementation
- Add full mobile screens for all user roles
- Add automated test coverage reports
- Add CI/CD pipeline using GitHub Actions
- Improve audit dashboard visualizations
- Add notification support for appointments and queue updates
- Add cloud database setup guide for Neon, AWS RDS, or Supabase
- Add FHIR-compatible export for medical records
- Add patient consent management
- Add analytics dashboard for administrators

---

## License

This project is created for academic and capstone project purposes. Add a formal license file before public or production use.
