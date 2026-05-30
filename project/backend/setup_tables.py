"""
Database table setup utility.

Reads DATABASE_URL from backend/.env (or environment) and executes the
schema.sql file to create all tables. Safe to run multiple times — errors
from tables that already exist are caught and reported.

Usage:
    cd project/backend
    python setup_tables.py
"""
import os
import sys
from pathlib import Path

try:
    import psycopg as psycopg2  # psycopg v3 (installed)
except ImportError:
    import psycopg2              # psycopg v2 fallback
from dotenv import load_dotenv

# Load .env from the backend directory
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print('❌ DATABASE_URL environment variable is not set.')
    print('   Copy project/.env.example to project/backend/.env and configure it.')
    sys.exit(1)

print('🔧 Setting up HealthSaathi database...')
print(f'   Connecting to: {DATABASE_URL.split("@")[-1]}')  # Log host only, not credentials
print()

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Read schema relative to project root (one level up from backend/)
    schema_path = Path(__file__).parent.parent / 'database' / 'schema.sql'
    with open(schema_path, 'r') as f:
        schema_content = f.read()

    print('Executing schema commands...')

    try:
        cur.execute(schema_content)
        conn.commit()
        print('✅ Schema executed successfully!')
    except Exception as e:
        conn.rollback()
        print(f'⚠️  Error in schema: {str(e)[:100]}')
        print('   (This may be normal if tables already exist)')
        conn.commit()

    # Verify tables
    print()
    print('📊 Checking database tables...')
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    tables = cur.fetchall()

    expected_tables = ['users', 'patients', 'doctors', 'appointments', 'medical_records', 'audit_chain']

    if tables:
        print(f'✅ Found {len(tables)} tables:')
        created_tables = [t[0] for t in tables]
        for name in created_tables:
            status = '✅' if name in expected_tables else '📋'
            print(f'   {status} {name}')

        print()
        missing = [t for t in expected_tables if t not in created_tables]
        if missing:
            print(f'⚠️  Missing tables: {missing}')
        else:
            print('✅ All required tables exist!')
    else:
        print('❌ No tables found!')

    cur.close()
    conn.close()

except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
