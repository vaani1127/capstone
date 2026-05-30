# HealthSaathi — Quick Start

Get HealthSaathi running locally in two ways: Docker (recommended) or bare Python.

## Option A — Docker (recommended, no local PostgreSQL needed)

```bash
cd project/deployment/docker
docker-compose -f docker-compose.dev.yml up --build
```

This starts PostgreSQL and the FastAPI backend with hot-reload on port 8000.
The schema is applied automatically on first run.

## Option B — Bare Python

### Prerequisites

- Python 3.9+
- PostgreSQL 13+ running locally
- pip

### Steps (all from the `project/backend/` directory)

**1. Install dependencies**

```bash
pip install -r requirements.txt
```

**2. Configure environment**

```bash
cd project          # project root (contains .env.example)
cp .env.example .env
```

Edit `.env` — minimum required values:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/healthsaathi
SECRET_KEY=<at-least-32-chars — generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
```

**3. Set up database tables**

```bash
cd backend
python setup_tables.py
```

**4. Load sample data (optional)**

```bash
python load_test_data.py
```

**5. Start the server**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Verify it's working

| URL | Purpose |
|-----|---------|
| http://localhost:8000/health | Liveness probe (DB status) |
| http://localhost:8000/ready | Readiness probe (503 if DB down) |
| http://localhost:8000/api/docs | Interactive Swagger UI |
| http://localhost:8000/api/redoc | ReDoc API reference |

## Test Credentials (sample data only)

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@healthsaathi.com | password123 |
| Doctor | rajesh.kumar@healthsaathi.com | password123 |
| Nurse | sunita@healthsaathi.com | password123 |
| Patient | rahul.verma@example.com | password123 |

## Run the Test Suite

```bash
cd project/backend
pytest
```

Tests use an in-memory SQLite database — no external PostgreSQL required.

## What's Included

- JWT authentication with access + refresh tokens (roles: Admin, Doctor, Nurse, Patient)
- 25+ REST API endpoints
- WebSocket real-time queue updates (`ws://localhost:8000/api/v1/ws/{doctor_id}`)
- Blockchain-backed audit chain (SHA-256 hash linkage, tamper detection)
- All appointment mutations create audit entries automatically
- Request tracing via `X-Request-ID` header on every response

## Next Steps

- [2_BACKEND_SETUP.md](2_BACKEND_SETUP.md) — full environment variable reference and test setup
- [3_DATABASE_SETUP.md](3_DATABASE_SETUP.md) — schema and migration details
- [4_API_DOCUMENTATION.md](4_API_DOCUMENTATION.md) — complete endpoint reference
- [5_DEPLOYMENT.md](5_DEPLOYMENT.md) — production deployment with Docker, Nginx, and Terraform
