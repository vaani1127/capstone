import psycopg2

db_url = 'postgresql://neondb_owner:npg_Ub1gR6AYMCwQ@ep-gentle-sunset-ai6pp20h-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

print('📥 Loading test data...')
print()

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Read sample data file
    with open('database/sample_data.sql', 'r') as f:
        sample_data = f.read()
    
    # Execute sample data
    statements = [s.strip() for s in sample_data.split(';') if s.strip()]
    
    print(f'Found {len(statements)} data statements')
    print()
    
    for i, stmt in enumerate(statements, 1):
        try:
            cur.execute(stmt)
            if i % 5 == 0:
                print(f'✓ Loaded {i} statements...')
        except Exception as e:
            error_msg = str(e)
            if 'duplicate' in error_msg.lower() or 'already exists' in error_msg.lower():
                pass  # Skip duplicate key errors
            else:
                print(f'⚠️  Statement {i}: {error_msg[:60]}')
    
    conn.commit()
    print()
    print('✅ Test data loaded successfully!')
    
    # Verify
    print()
    print('📊 Data Summary:')
    
    queries = [
        ('Users', 'SELECT COUNT(*) FROM users'),
        ('Patients', 'SELECT COUNT(*) FROM patients'),
        ('Doctors', 'SELECT COUNT(*) FROM doctors'),
        ('Appointments', 'SELECT COUNT(*) FROM appointments'),
        ('Medical Records', 'SELECT COUNT(*) FROM medical_records'),
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
