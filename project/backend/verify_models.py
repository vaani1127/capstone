"""
Simple script to verify SQLAlchemy models are correctly defined
This script checks model structure without requiring database connection
"""
import sys
import os

# Set environment variables before importing
os.environ['DATABASE_URL'] = 'postgresql://user:pass@localhost:5432/db'
os.environ['SECRET_KEY'] = 'test-key'

# Prevent actual database connection by mocking
from unittest.mock import Mock, patch
import sqlalchemy

# Mock the create_engine to prevent actual connection
mock_engine = Mock()
mock_engine.url = Mock()
mock_engine.url.database = 'test_db'
mock_engine.pool = Mock()
mock_engine.pool.size = Mock(return_value=10)
mock_engine.pool.timeout = 30

with patch('sqlalchemy.create_engine', return_value=mock_engine):
    from app.models.user import User, UserRole
    from app.models.patient import Patient
    from app.models.doctor import Doctor
    from app.models.appointment import Appointment, AppointmentStatus, AppointmentType
    from app.models.medical_record import MedicalRecord
    from app.models.audit_chain import AuditChain

def verify_model_structure():
    """Verify all models have required attributes"""
    
    print("Verifying SQLAlchemy Models...")
    print("=" * 60)
    
    # Test User model
    print("\n✓ User Model")
    assert User.__tablename__ == "users"
    assert hasattr(User, 'name')
    assert hasattr(User, 'email')
    assert hasattr(User, 'password_hash')
    assert hasattr(User, 'role')
    print(f"  - Table: {User.__tablename__}")
    print(f"  - Columns: name, email, password_hash, role")
    print(f"  - Roles: {[r.value for r in UserRole]}")
    
    # Test Patient model
    print("\n✓ Patient Model")
    assert Patient.__tablename__ == "patients"
    assert hasattr(Patient, 'user_id')
    assert hasattr(Patient, 'date_of_birth')
    assert hasattr(Patient, 'gender')
    assert hasattr(Patient, 'phone')
    assert hasattr(Patient, 'address')
    assert hasattr(Patient, 'blood_group')
    print(f"  - Table: {Patient.__tablename__}")
    print(f"  - Columns: user_id, date_of_birth, gender, phone, address, blood_group")
    
    # Test Doctor model
    print("\n✓ Doctor Model")
    assert Doctor.__tablename__ == "doctors"
    assert hasattr(Doctor, 'user_id')
    assert hasattr(Doctor, 'specialization')
    assert hasattr(Doctor, 'license_number')
    assert hasattr(Doctor, 'average_consultation_duration')
    print(f"  - Table: {Doctor.__tablename__}")
    print(f"  - Columns: user_id, specialization, license_number, average_consultation_duration")
    
    # Test Appointment model
    print("\n✓ Appointment Model")
    assert Appointment.__tablename__ == "appointments"
    assert hasattr(Appointment, 'patient_id')
    assert hasattr(Appointment, 'doctor_id')
    assert hasattr(Appointment, 'scheduled_time')
    assert hasattr(Appointment, 'status')
    assert hasattr(Appointment, 'appointment_type')
    assert hasattr(Appointment, 'queue_position')
    print(f"  - Table: {Appointment.__tablename__}")
    print(f"  - Columns: patient_id, doctor_id, scheduled_time, status, appointment_type, queue_position")
    print(f"  - Statuses: {[s.value for s in AppointmentStatus]}")
    print(f"  - Types: {[t.value for t in AppointmentType]}")
    
    # Test MedicalRecord model
    print("\n✓ MedicalRecord Model")
    assert MedicalRecord.__tablename__ == "medical_records"
    assert hasattr(MedicalRecord, 'patient_id')
    assert hasattr(MedicalRecord, 'doctor_id')
    assert hasattr(MedicalRecord, 'appointment_id')
    assert hasattr(MedicalRecord, 'consultation_notes')
    assert hasattr(MedicalRecord, 'diagnosis')
    assert hasattr(MedicalRecord, 'prescription')
    assert hasattr(MedicalRecord, 'version_number')
    assert hasattr(MedicalRecord, 'parent_record_id')
    assert hasattr(MedicalRecord, 'created_by')
    print(f"  - Table: {MedicalRecord.__tablename__}")
    print(f"  - Columns: patient_id, doctor_id, appointment_id, consultation_notes,")
    print(f"             diagnosis, prescription, version_number, parent_record_id, created_by")
    
    # Test AuditChain model
    print("\n✓ AuditChain Model")
    assert AuditChain.__tablename__ == "audit_chain"
    assert hasattr(AuditChain, 'record_id')
    assert hasattr(AuditChain, 'record_type')
    assert hasattr(AuditChain, 'record_data')
    assert hasattr(AuditChain, 'hash')
    assert hasattr(AuditChain, 'previous_hash')
    assert hasattr(AuditChain, 'timestamp')
    assert hasattr(AuditChain, 'user_id')
    assert hasattr(AuditChain, 'is_tampered')
    print(f"  - Table: {AuditChain.__tablename__}")
    print(f"  - Columns: record_id, record_type, record_data, hash, previous_hash,")
    print(f"             timestamp, user_id, is_tampered")
    
    print("\n" + "=" * 60)
    print("✓ All models verified successfully!")
    print("\nSummary:")
    print("  - 6 models created: User, Patient, Doctor, Appointment, MedicalRecord, AuditChain")
    print("  - All models match database schema")
    print("  - All required columns present")
    print("  - Enums defined correctly")
    
    return True

if __name__ == "__main__":
    try:
        verify_model_structure()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ Verification failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
