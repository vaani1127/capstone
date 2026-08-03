"""
Initialize database: create all tables from scratch.
Run this before starting the app if database is empty.
"""

import os
import sys
from sqlalchemy import create_engine, inspect

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.db.base import Base, import_models

# Import models to register them
import_models()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:devpassword@localhost:5432/healthsaathi_dev")

def init_db():
    """Create all tables from SQLAlchemy models."""
    print(f"Connecting to database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")

    engine = create_engine(DATABASE_URL, echo=False)

    # Check if tables already exist
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if existing_tables:
        print(f"✓ Database already initialized. Found {len(existing_tables)} tables.")
        return True

    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ All tables created successfully!")
        return True
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        return False

if __name__ == "__main__":
    success = init_db()
    sys.exit(0 if success else 1)
