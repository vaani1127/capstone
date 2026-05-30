#!/bin/sh
# HealthSaathi backend startup entrypoint.
# Runs schema setup / Alembic migrations before starting uvicorn.
set -e

echo "=== HealthSaathi Backend Startup ==="

# Run Alembic migrations if alembic.ini is present (mounted or bundled).
if [ -f "alembic.ini" ]; then
    echo "Running Alembic migrations..."
    alembic upgrade head && echo "Migrations complete." || echo "Migration failed (may be OK if schema is already current)."
elif [ -f "setup_tables.py" ]; then
    # Fallback: run setup_tables.py if schema.sql is accessible.
    echo "Running setup_tables.py..."
    python setup_tables.py || echo "setup_tables.py failed (schema may already be present)."
else
    echo "No migration tool found — assuming schema is already up to date."
fi

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WORKERS:-4}
