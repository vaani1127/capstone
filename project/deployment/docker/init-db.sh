#!/bin/bash
# Database initialization script for Docker deployment

set -e

echo "Running database initialization..."

# Wait for PostgreSQL to be ready
until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done

echo "PostgreSQL is ready!"

# Run migrations (if using Alembic)
# Note: This would typically be run from the backend container
# cd /app && python migrate.py upgrade head

echo "Database initialization complete!"
