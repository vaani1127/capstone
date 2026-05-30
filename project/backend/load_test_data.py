"""
Test data loader utility.

Reads DATABASE_URL from backend/.env (or environment) and loads the
database/sample_data.sql file into the database. Duplicate-key errors are
silently skipped so this is safe to re-run.

Usage:
    cd project/backend
    python load_test_data.py
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

print('📥 Loading test data...')
print(f'   Connecting to: {DATABASE_URL.split("@")[-1]}')
print()

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Read sample data relative to project root
    sample_data_path = Path(__file__).parent.parent / 'database' / 'sample_data.sql'
    with open(sample_data_path, 'r') as f:
        sample_data = f.read()

    statements = [s.strip() for s in sample_data.split(';') if s.strip()]
    print(f'Found {len(statements)} data statements')
    print()

    loaded = 0
    for i, stmt in enumerate(statements, 1):
        try:
            cur.execute(stmt)
            loaded += 1
            if i % 5 == 0:
                print(f'✓ Loaded {i} statements...')
        except Exception as e:
            error_msg = str(e)
            if 'duplicate' in error_msg.lower() or 'already exists' in error_msg.lower():
                conn.rollback()  # Reset transaction after error
            else:
                conn.rollback()
                print(f'⚠️  Statement {i}: {error_msg[:80]}')

    conn.commit()
    print()
    print(f'✅ Test data loaded successfully! ({loaded}/{len(statements)} statements executed)')

    # Verification summary
    print()
    print('📊 Data Summary:')
    queries = [
        ('Users', 'SELECT COUNT(*) FROM users'),
        ('Patients', 'SELECT COUNT(*) FROM patients'),
        ('Doctors', 'SELECT COUNT(*) FROM doctors'),
        ('Appointments', 'SELECT COUNT(*) FROM appointments'),
        ('Medical Records', 'SELECT COUNT(*) FROM medical_records'),
        ('Audit Chain entries', 'SELECT COUNT(*) FROM audit_chain'),
    ]
    for label, query in queries:
        cur.execute(query)
        count = cur.fetchone()[0]
        print(f'  {label}: {count}')

    cur.close()
    conn.close()

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
