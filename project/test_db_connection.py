"""Test database connection"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

# Set the .env file path explicitly
os.environ.setdefault('ENV_FILE', str(backend_dir / '.env'))

try:
    from app.core.config import settings
    print(f"DATABASE_URL from config: {settings.DATABASE_URL}")
    print("\nTrying to connect...")
    
    from sqlalchemy import create_engine, text
    engine = create_engine(str(settings.DATABASE_URL))
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"\n✓ Connection successful!")
        print(f"PostgreSQL version: {version}")
        
except Exception as e:
    print(f"\n✗ Connection failed!")
    print(f"Error: {e}")
    print("\nPlease check:")
    print("1. PostgreSQL is running")
    print("2. Database 'healthsaathi_db' exists")
    print("3. User 'healthsaathi_user' exists with correct password")
    print("4. backend/.env file has correct DATABASE_URL")
