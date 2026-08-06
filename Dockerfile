# HealthSaathi Backend - Render Deployment
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client curl gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY project/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY project/backend/app ./app
COPY project/backend/init_db.py ./
COPY project/alembic ./alembic
COPY project/alembic.ini ./

# Set environment
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-10000}/health || exit 1

# Render sets PORT env var at runtime — bind to whatever it provides
# Initialize database and start server
CMD sh -c "python init_db.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"
