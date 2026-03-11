"""Verify database tables were created"""
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

try:
    from app.core.config import settings
    from sqlalchemy import create_engine, text
    
    engine = create_engine(str(settings.DATABASE_URL))
    
    with engine.connect() as conn:
        # Get list of tables
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        
        tables = [row[0] for row in result]
        
        print("✓ Database tables created successfully!\n")
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")
        
        # Check for expected tables
        expected = ['users', 'patients', 'doctors', 'appointments', 'medical_records', 'audit_chain']
        missing = [t for t in expected if t not in tables]
        
        if missing:
            print(f"\n⚠ Warning: Missing expected tables: {', '.join(missing)}")
        else:
            print("\n✓ All expected tables are present!")
            
except Exception as e:
    print(f"\n✗ Verification failed!")
    print(f"Error: {e}")
