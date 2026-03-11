# HealthSaathi Backend API

FastAPI-based backend for the HealthSaathi healthcare management system.

## Features

- **FastAPI Framework**: Modern, fast, and async-ready
- **PostgreSQL Database**: Robust relational database with SQLAlchemy ORM
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control**: Admin, Doctor, Nurse, Patient roles
- **WebSocket Support**: Real-time queue updates
- **Blockchain Integrity**: Hash-chained audit trail for medical records
- **CORS & Security Headers**: Production-ready security configuration

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py       # Main API router
│   │       └── endpoints/      # API endpoint modules
│   │           └── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Application configuration
│   │   └── security.py         # Security utilities (JWT, password hashing)
│   ├── db/
│   │   └── __init__.py         # Database connection and session management
│   ├── models/
│   │   └── __init__.py         # SQLAlchemy models
│   ├── schemas/
│   │   └── __init__.py         # Pydantic schemas
│   ├── services/
│   │   └── __init__.py         # Business logic services
│   └── middleware/
│       └── __init__.py         # Custom middleware
├── requirements.txt            # Python dependencies
├── .env.example               # Example environment variables
├── .gitignore
└── README.md
```

## Setup Instructions

### 1. Prerequisites

- Python 3.9 or higher
- PostgreSQL 13 or higher
- pip (Python package manager)

### 2. Installation

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your configuration
# IMPORTANT: Change SECRET_KEY in production!
```

### 4. Database Setup

Ensure PostgreSQL is running and the database is created:

```bash
# From project root, run migrations
python migrate.py upgrade head
```

### 5. Run the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 6. Access the API

- **API Documentation (Swagger)**: http://localhost:8000/api/docs
- **API Documentation (ReDoc)**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/health

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROJECT_NAME` | Application name | HealthSaathi API |
| `VERSION` | API version | 1.0.0 |
| `ENVIRONMENT` | Environment (development/production) | development |
| `DEBUG` | Debug mode | false |
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | JWT signing key (min 32 chars) | Required |
| `ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry | 60 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiry | 7 |
| `ALLOWED_ORIGINS` | CORS allowed origins (comma-separated) | * |

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

### Code Formatting

```bash
# Format code with black
black app/

# Check code style with flake8
flake8 app/

# Type checking with mypy
mypy app/
```

## API Endpoints (Planned)

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token

### Appointments
- `GET /api/v1/appointments` - List appointments
- `POST /api/v1/appointments` - Create appointment
- `PUT /api/v1/appointments/{id}` - Update appointment
- `DELETE /api/v1/appointments/{id}` - Cancel appointment

### Queue Management
- `GET /api/v1/queue/status` - Get queue status
- `GET /api/v1/queue/doctor/{id}` - Get doctor's queue

### Medical Records
- `GET /api/v1/medical-records/patient/{id}` - Get patient records
- `POST /api/v1/medical-records` - Create medical record
- `PUT /api/v1/medical-records/{id}` - Update medical record
- `GET /api/v1/medical-records/{id}/versions` - Get record versions

### Audit
- `GET /api/v1/audit/logs` - Get audit logs (Admin only)
- `GET /api/v1/audit/tampering-alerts` - Get tampering alerts (Admin only)

### Users
- `GET /api/v1/users` - List users (Admin only)
- `POST /api/v1/users` - Create user (Admin only)
- `PUT /api/v1/users/{id}` - Update user (Admin only)

## Security Features

- **Password Hashing**: bcrypt with cost factor 12
- **JWT Tokens**: Secure token-based authentication
- **CORS**: Configurable cross-origin resource sharing
- **Security Headers**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, HSTS
- **Role-Based Access Control**: Enforced at endpoint level
- **HTTPS**: Required in production

## License

Proprietary - HealthSaathi Project
