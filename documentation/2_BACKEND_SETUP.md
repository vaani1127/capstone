# Backend Setup Guide

Comprehensive setup and development reference for the HealthSaathi FastAPI backend.

## Prerequisites

- Python 3.9 or higher
- PostgreSQL 13 or higher (skip if using Docker)
- pip

## Installation

### 1. Install Dependencies

```bash
cd project/backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cd project          # project root (one level above backend/)
cp .env.example .env
```

Edit `.env`:

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Yes | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/healthsaathi` |
| `SECRET_KEY` | Yes | JWT signing key — **must be ≥ 32 characters** | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Access token lifetime (default: 60) | `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | Refresh token lifetime (default: 7) | `7` |
| `ALLOWED_ORIGINS` | No | Comma-separated CORS origins (default: `*`) | `https://app.example.com,https://admin.example.com` |
| `ENVIRONMENT` | No | Runtime environment (default: `development`) | `production` |
| `DEBUG` | No | Enable debug logging (default: `false`) | `false` |

**Important:** The server refuses to start if `SECRET_KEY` is shorter than 32 characters.
Use `openssl rand -hex 32` or the Python command above to generate a valid key.

In production, set `ALLOWED_ORIGINS` to the specific origins that should be allowed.
The wildcard `*` disables credential-bearing cross-origin requests.

### 3. Set Up Database Tables

```bash
cd project/backend
python setup_tables.py
```

### 4. Load Sample Data (optional)

```bash
python load_test_data.py
```

### 5. Start the Server

```bash
# Development — with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production — multiple workers via entrypoint
./entrypoint.sh
```

## Docker Dev Environment

The fastest way to get a working environment with no manual PostgreSQL setup:

```bash
cd project/deployment/docker
docker-compose -f docker-compose.dev.yml up --build
```

- Backend runs on http://localhost:8000 with source hot-reload
- PostgreSQL initialised automatically via `database/schema.sql`
- No Nginx, no SSL, no Redis — development only

## Verification

| URL | Expected |
|-----|---------|
| `GET /health` | `{"status": "healthy", "database": "connected", ...}` |
| `GET /ready` | `{"status": "ready"}` (503 with reason if DB unavailable) |
| `GET /api/docs` | Swagger UI |
| `GET /api/redoc` | ReDoc |

## Running the Test Suite

Tests use SQLite in-memory — no PostgreSQL required:

```bash
cd project/backend
pytest
```

Coverage by area:

| File | Tests |
|------|-------|
| `tests/test_auth.py` | Register, login, refresh, unauthenticated access |
| `tests/test_appointments.py` | Book, list, cancel, reschedule, status update, walk-in, audit trail |
| `tests/test_blockchain.py` | Hash generation, chain linkage, integrity verification, API endpoints |
| `tests/test_medical_records.py` | Create, RBAC, versioning, audit trail |
| `tests/test_anomaly.py` | Feature extraction, scoring, severity classification, NL explanation, REST API (18 tests) |

Run a specific test file:

```bash
pytest tests/test_blockchain.py -v
```

Run and show test output (useful when debugging):

```bash
pytest -s tests/test_auth.py
```

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app, middleware, exception handlers
│   ├── core/
│   │   ├── config.py        # Pydantic Settings (reads .env)
│   │   ├── security.py      # JWT creation/verification, password hashing
│   │   └── dependencies.py  # Dependency injection (get_current_user, role guards)
│   ├── api/v1/
│   │   ├── router.py        # Aggregates all endpoint routers
│   │   └── endpoints/       # One file per domain
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── appointments.py
│   │       ├── medical_records.py
│   │       ├── queue.py
│   │       ├── audit.py
│   │       ├── anomaly.py
│   │       └── websocket.py
│   ├── db/                  # Session factory, connection helpers
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request/response schemas
│   │   └── anomaly.py       # AnomalyAlert schemas and AnomalyFeatureVector
│   └── services/            # Business logic
│       ├── appointment_service.py
│       ├── blockchain_service.py
│       ├── anomaly_service.py   # IsolationForest scoring, SHAP explainability
│       └── websocket_manager.py # ConnectionManager incl. admin anomaly broadcast
├── tests/
│   ├── conftest.py          # SQLite test engine, fixtures
│   ├── test_auth.py
│   ├── test_appointments.py
│   ├── test_blockchain.py
│   ├── test_medical_records.py
│   └── test_anomaly.py
├── entrypoint.sh            # Production startup (migration → uvicorn)
├── pytest.ini
├── requirements.txt
└── setup_tables.py
```

## Middleware Stack (in order applied)

| Middleware | Purpose |
|-----------|---------|
| `CORSMiddleware` | Cross-origin request control via `ALLOWED_ORIGINS` |
| `limit_request_size` | Rejects bodies > 10 MB with HTTP 413 |
| `add_request_id` | Attaches `X-Request-ID` UUID to every request/response; logs path only (never query strings) |
| `add_security_headers` | Adds `X-Content-Type-Options`, `X-Frame-Options`, `HSTS`, etc. |

## Features

- FastAPI 0.109 with async support
- PostgreSQL + SQLAlchemy 2.0 ORM (SQLite for tests via StaticPool)
- JWT authentication — access tokens (60 min) + refresh tokens (7 days)
- Role-Based Access Control: Admin > Doctor > Nurse > Patient
- WebSocket real-time queue updates
- Blockchain-backed audit chain (SHA-256 hash linkage, tamper detection)
- All appointment mutations create audit entries automatically
- ML-based behavioural anomaly detection (scikit-learn IsolationForest per role, SHAP explainability) — model trains lazily on first use; no extra configuration required. Requires: `scikit-learn==1.4.2`, `shap==0.45.1`, `numpy==1.26.4`, `pandas==2.2.2`, `joblib==1.4.2` (all included in `requirements.txt`)
- Request tracing via `X-Request-ID` header
- Liveness (`/health`) and readiness (`/ready`) health endpoints

## Troubleshooting

**"SECRET_KEY must be at least 32 characters"**
Generate a valid key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

**"Connection refused" to database**
Ensure PostgreSQL is running: `pg_isready -h localhost`
Check `DATABASE_URL` in `.env`.

**JWT token errors in tests**
The test `SECRET_KEY` is set in `conftest.py` before app import. Do not override it.

**CORS errors from frontend**
Set `ALLOWED_ORIGINS=http://localhost:3000` (or your frontend origin) in `.env`.
Note: credential-bearing requests (cookies) require a specific origin, not `*`.

**Alembic not found during production startup**
`entrypoint.sh` falls back to `setup_tables.py` if `alembic.ini` is absent from the container.
Both are safe to run on an already-initialised schema.

---

See [4_API_DOCUMENTATION.md](4_API_DOCUMENTATION.md) for the complete endpoint reference.
