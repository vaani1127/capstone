import psycopg2

db_url = 'postgresql://neondb_owner:npg_Ub1gR6AYMCwQ@ep-gentle-sunset-ai6pp20h-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

print('🔧 Setting up HealthSaathi database...')
print()

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Read entire schema
    with open('database/schema.sql', 'r') as f:
        schema_content = f.read()
    
    print('Executing schema commands...')
    
    # Execute using cursor.execute() which should handle multiline properly
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
        created_tables = []
        for table in tables:
            name = table[0]
            created_tables.append(name)
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
