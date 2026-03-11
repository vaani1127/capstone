# Backend Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and update these critical values:
# - DATABASE_URL: Your PostgreSQL connection string
# - SECRET_KEY: Generate a secure random key (min 32 characters)
```

**Generate a secure SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Setup Database

The database schema should already be created. If not, run migrations from the project root:

```bash
cd ..
python migrate.py upgrade head
```

### 4. Run the Server

```bash
cd backend
python run.py
```

Or using uvicorn directly:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Verify Installation

Open your browser and visit:
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/api/docs
- **Root**: http://localhost:8000/

You should see the API documentation and be able to test endpoints.

## Project Structure Overview

```
backend/
├── app/
│   ├── main.py              # FastAPI app with CORS & security headers
│   ├── core/
│   │   ├── config.py        # Environment configuration
│   │   └── security.py      # JWT & password hashing utilities
│   ├── api/v1/
│   │   ├── router.py        # Main API router
│   │   └── endpoints/       # API endpoints (to be implemented)
│   ├── db/                  # Database connection (to be implemented)
│   ├── models/              # SQLAlchemy models (to be implemented)
│   ├── schemas/             # Pydantic schemas (to be implemented)
│   ├── services/            # Business logic (to be implemented)
│   └── middleware/          # Custom middleware (to be implemented)
├── requirements.txt         # Python dependencies
├── .env.example            # Example environment variables
├── run.py                  # Development server runner
└── README.md               # Full documentation
```

## Next Steps

The backend foundation is ready. Next tasks:
1. **Task 2.2**: Implement database connection layer
2. **Task 2.3**: Create data models
3. **Task 3.1-3.3**: Implement authentication endpoints
4. **Task 4.1-4.2**: Implement RBAC middleware

## Configuration Details

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | Yes | JWT signing key (min 32 chars) |
| `ALLOWED_ORIGINS` | No | CORS origins (comma-separated) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Token expiry (default: 60) |
| `DEBUG` | No | Debug mode (default: false) |

### Security Features Configured

✅ **CORS Middleware**: Configurable allowed origins  
✅ **Security Headers**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, HSTS  
✅ **JWT Authentication**: Token generation and validation utilities  
✅ **Password Hashing**: bcrypt with secure defaults  
✅ **Environment-based Config**: Pydantic settings management  

## Troubleshooting

### Import Errors
Make sure you're in the backend directory and have activated your virtual environment.

### Database Connection Errors
Verify your DATABASE_URL in .env matches your PostgreSQL configuration.

### Port Already in Use
Change the port in run.py or use: `uvicorn app.main:app --reload --port 8001`
