#!/usr/bin/env python3
"""
Test script to verify database migrations
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test database connection"""
    print("🔌 Testing database connection...")
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL not set in .env file")
        return False
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL")
            print(f"   Version: {version.split(',')[0]}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def test_tables():
    """Test that all tables exist"""
    print("\n📋 Checking database tables...")
    
    database_url = os.getenv("DATABASE_URL")
    engine = create_engine(database_url)
    
    expected_tables = [
        'users',
        'patients',
        'doctors',
        'appointments',
        'medical_records',
        'audit_chain',
        'alembic_version'
    ]
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            existing_tables = [row[0] for row in result]
            
            print(f"   Found {len(existing_tables)} tables:")
            for table in existing_tables:
                status = "✅" if table in expected_tables else "⚠️"
                print(f"   {status} {table}")
            
            missing_tables = set(expected_tables) - set(existing_tables)
            if missing_tables:
                print(f"\n❌ Missing tables: {', '.join(missing_tables)}")
                return False
            
            print("\n✅ All expected tables exist")
            return True
            
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False


def test_migration_version():
    """Check current migration version"""
    print("\n🔖 Checking migration version...")
    
    database_url = os.getenv("DATABASE_URL")
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.fetchone()
            
            if version:
                print(f"✅ Current migration version: {version[0]}")
                return True
            else:
                print("⚠️  No migration version found (migrations not applied)")
                return False
                
    except Exception as e:
        print(f"❌ Error checking version: {e}")
        return False


def test_seed_data():
    """Check if seed data exists"""
    print("\n🌱 Checking seed data...")
    
    database_url = os.getenv("DATABASE_URL")
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Check users
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.fetchone()[0]
            print(f"   Users: {user_count}")
            
            # Check doctors
            result = conn.execute(text("SELECT COUNT(*) FROM doctors"))
            doctor_count = result.fetchone()[0]
            print(f"   Doctors: {doctor_count}")
            
            # Check patients
            result = conn.execute(text("SELECT COUNT(*) FROM patients"))
            patient_count = result.fetchone()[0]
            print(f"   Patients: {patient_count}")
            
            # Check appointments
            result = conn.execute(text("SELECT COUNT(*) FROM appointments"))
            appointment_count = result.fetchone()[0]
            print(f"   Appointments: {appointment_count}")
            
            # Check medical records
            result = conn.execute(text("SELECT COUNT(*) FROM medical_records"))
            record_count = result.fetchone()[0]
            print(f"   Medical Records: {record_count}")
            
            # Check audit chain
            result = conn.execute(text("SELECT COUNT(*) FROM audit_chain"))
            audit_count = result.fetchone()[0]
            print(f"   Audit Chain Entries: {audit_count}")
            
            if user_count > 0:
                print("\n✅ Seed data is present")
                return True
            else:
                print("\n⚠️  No seed data found (run: python migrate.py seed)")
                return False
                
    except Exception as e:
        print(f"❌ Error checking seed data: {e}")
        return False


def test_constraints():
    """Test database constraints"""
    print("\n🔒 Testing constraints...")
    
    database_url = os.getenv("DATABASE_URL")
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Test role constraint
            try:
                conn.execute(text("""
                    INSERT INTO users (name, email, password_hash, role) 
                    VALUES ('Test', 'test@test.com', 'hash', 'InvalidRole')
                """))
                conn.commit()
                print("❌ Role constraint not working")
                return False
            except Exception:
                print("✅ Role constraint working")
                conn.rollback()
            
            # Test email uniqueness
            result = conn.execute(text("SELECT email FROM users LIMIT 1"))
            existing_email = result.fetchone()
            
            if existing_email:
                try:
                    conn.execute(text(f"""
                        INSERT INTO users (name, email, password_hash, role) 
                        VALUES ('Test', '{existing_email[0]}', 'hash', 'Patient')
                    """))
                    conn.commit()
                    print("❌ Email uniqueness constraint not working")
                    return False
                except Exception:
                    print("✅ Email uniqueness constraint working")
                    conn.rollback()
            
            return True
            
    except Exception as e:
        print(f"❌ Error testing constraints: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("HealthSaathi Database Migration Tests")
    print("=" * 60)
    
    tests = [
        ("Connection", test_connection),
        ("Tables", test_tables),
        ("Migration Version", test_migration_version),
        ("Seed Data", test_seed_data),
        ("Constraints", test_constraints),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
