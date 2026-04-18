# Backend Setup Guide

Comprehensive setup instructions for the HealthSaathi FastAPI backend.

## Prerequisites

- Python 3.9 or higher
- PostgreSQL 13 or higher
- pip (Python package manager)

## Installation

### 1. Install Dependencies

From project root:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

From project root:

```bash
cp .env.example .env
```

Edit `.env` and set:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection (Neon or local) | Neon: `postgresql://user:pass@host/db?sslmode=require` Local: `postgresql://user:pass@localhost:5432/healthsaathi` |
| `SECRET_KEY` | JWT signing key (min 32 chars) | Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry (optional) | 30 |
| `DEBUG` | Debug mode (optional) | false |

### 3. Setup Database

From `backend/` directory:

```bash
cd backend
python setup_tables.py
```

This creates all required tables from the schema file.

### 4. Load Test Data (Optional)

From `backend/` directory:

```bash
python load_test_data.py
```

### 5. Run the Backend

From `backend/` directory:

```bash
# Development mode with auto-reload
python run.py
```

Or using uvicorn directly:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Verification

Visit in your browser:

- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/api/docs  
- **ReDoc**: http://localhost:8000/api/redoc

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── core/
│   │   ├── config.py        # Configuration
│   │   └── security.py      # JWT & password hashing
│   ├── api/v1/
│   │   ├── router.py        # Main API router
│   │   └── endpoints/       # API endpoints
│   ├── db/                  # Database connection
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   └── middleware/          # Custom middleware
├── requirements.txt         # Python dependencies
└── run.py                   # Development server runner
```

## Features

- ✅ FastAPI framework with async support
- ✅ PostgreSQL with SQLAlchemy ORM
- ✅ JWT authentication with token refresh
- ✅ Role-Based Access Control (RBAC)
- ✅ WebSocket support for real-time updates
- ✅ Blockchain-backed medical records
- ✅ CORS & security headers configured
- ✅ 20+ API endpoints

## Troubleshooting

**Connection refused to database**
- Ensure PostgreSQL is running: `pg_isready`
- Check DATABASE_URL is correct

**JWT token errors**
- Regenerate SECRET_KEY
- Ensure token is in Authorization header format: `Bearer <token>`

**CORS errors**
- Update ALLOWED_ORIGINS in .env file

---

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete endpoint documentation.
