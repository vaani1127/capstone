# HealthSaathi Backend Dockerfile - Production
# Build context: project/ (parent directory)

FROM python:3.9-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc postgresql-client && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.9-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client curl && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code (backend)
COPY backend/app ./app
COPY backend/entrypoint.sh ./entrypoint.sh
COPY backend/setup_tables.py ./
COPY backend/run.py ./

# Copy alembic (for migrations)
COPY alembic ./alembic
COPY alembic.ini ./

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /var/log/healthsaathi && \
    chown -R appuser:appuser /app /var/log/healthsaathi && \
    chmod +x entrypoint.sh

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["./entrypoint.sh"]
