"""
Unit tests for blockchain integrity service
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.blockchain_service import generate_hash
from app.models.user import User
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.core.security import get_password_hash


@pytest.fixture
def sample_user(db_session: Session):
    """Create a sample user for testing"""
    user = User(
        name="Dr. Test User",
        email="test.user@example.com",
        password_hash=get_password_hash("testpassword"),
        role="Doctor"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_patient(db_session: Session):
    """Create a sample patient for testing"""
    from datetime import date
    
    # Create patient user
    patient_user = User(
        name="Test Patient",
        email="patient@example.com",
        password_hash=get_password_hash("testpassword"),
        role="Patient"
    )
    db_session.add(patient_user)
    db_session.commit()
    db_session.refresh(patient_user)
    
    # Create patient
    patient = Patient(
        user_id=patient_user.id,
        date_of_birth=date(1990, 1, 1),
        gender="Male",
        phone="1234567890",
        address="123 Test St",
        blood_group="O+"
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)
    return patient


@pytest.fixture
def sample_doctor(db_session: Session):
    """Create a sample doctor for testing"""
    # Create doctor user
    doctor_user = User(
        name="Dr. Test Doctor",
        email="doctor@example.com",
        password_hash=get_password_hash("testpassword"),
        role="Doctor"
    )
    db_session.add(doctor_user)
    db_session.commit()
    db_session.refresh(doctor_user)
    
    # Create doctor
    doctor = Doctor(
        user_id=doctor_user.id,
        specialization="General Medicine",
        license_number="DOC123456",
        average_consultation_duration=15
    )
    db_session.add(doctor)
    db_session.commit()
    db_session.refresh(doctor)
    return doctor


class TestHashGeneration:
    """Test suite for hash generation function"""
    
    def test_hash_generation_basic(self):
        """Test basic hash generation with valid inputs"""
        record_data = {
            "diagnosis": "Common cold",
            "prescription": "Rest and fluids"
        }
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        user_id = 123
        previous_hash = "0"
        
        hash_result = generate_hash(record_data, timestamp, user_id, previous_hash)
        
        # Verify hash is 64 characters (SHA-256 hex digest)
        assert len(hash_result) == 64
        # Verify hash contains only hexadecimal characters
        assert all(c in '0123456789abcdef' for c in hash_result)
    
    def test_hash_consistency_same_input(self):
        """Test that same input produces same hash (deterministic)"""
        record_data = {"diagnosis": "Flu", "notes": "Patient recovering"}
        timestamp = datetime(2024, 2, 15, 10, 30, 0)
        user_id = 456
        previous_hash = "abc123"
        
        hash1 = generate_hash(record_data, timestamp, user_id, previous_hash)
        hash2 = generate_hash(record_data, timestamp, user_id, previous_hash)
        
        assert hash1 == hash2
    
    def test_hash_uniqueness_different_record_data(self):
        """Test that different record data produces different hash"""
        timestamp = datetime(2024, 3, 1, 14, 0, 0)
        user_id = 789
        previous_hash = "xyz789"
        
        record_data1 = {"diagnosis": "Diabetes"}
        record_data2 = {"diagnosis": "Hypertension"}
        
        hash1 = generate_hash(record_data1, timestamp, user_id, previous_hash)
        hash2 = generate_hash(record_data2, timestamp, user_id, previous_hash)
        
        assert hash1 != hash2
    
    def test_hash_uniqueness_different_timestamp(self):
        """Test that different timestamp produces different hash"""
        record_data = {"diagnosis": "Asthma"}
        user_id = 100
        previous_hash = "prev123"
        
        timestamp1 = datetime(2024, 4, 1, 9, 0, 0)
        timestamp2 = datetime(2024, 4, 1, 9, 0, 1)  # 1 second difference
        
        hash1 = generate_hash(record_data, timestamp1, user_id, previous_hash)
        hash2 = generate_hash(record_data, timestamp2, user_id, previous_hash)
        
        assert hash1 != hash2
    
    def test_hash_uniqueness_different_user_id(self):
        """Test that different user_id produces different hash"""
        record_data = {"diagnosis": "Migraine"}
        timestamp = datetime(2024, 5, 10, 11, 30, 0)
        previous_hash = "hash456"
        
        hash1 = generate_hash(record_data, timestamp, 111, previous_hash)
        hash2 = generate_hash(record_data, timestamp, 222, previous_hash)
        
        assert hash1 != hash2
    
    def test_hash_uniqueness_different_previous_hash(self):
        """Test that different previous_hash produces different hash"""
        record_data = {"diagnosis": "Allergy"}
        timestamp = datetime(2024, 6, 20, 16, 45, 0)
        user_id = 333
        
        hash1 = generate_hash(record_data, timestamp, user_id, "prev_a")
        hash2 = generate_hash(record_data, timestamp, user_id, "prev_b")
        
        assert hash1 != hash2
    
    def test_genesis_block_hash(self):
        """Test hash generation for genesis block (previous_hash = '0')"""
        record_data = {"type": "genesis", "message": "First block"}
        timestamp = datetime(2024, 1, 1, 0, 0, 0)
        user_id = 1
        previous_hash = "0"
        
        hash_result = generate_hash(record_data, timestamp, user_id, previous_hash)
        
        assert len(hash_result) == 64
        assert hash_result != "0"
    
    def test_empty_record_data(self):
        """Test hash generation with empty record data"""
        record_data = {}
        timestamp = datetime(2024, 7, 1, 8, 0, 0)
        user_id = 444
        previous_hash = "empty_test"
        
        hash_result = generate_hash(record_data, timestamp, user_id, previous_hash)
        
        assert len(hash_result) == 64
    
    def test_none_record_data(self):
        """Test hash generation handles None record data"""
        record_data = None
        timestamp = datetime(2024, 8, 1, 10, 0, 0)
        user_id = 555
        previous_hash = "none_test"
        
        hash_result = generate_hash(record_data, timestamp, user_id, previous_hash)
        
        assert len(hash_result) == 64
    
    def test_none_previous_hash(self):
        """Test hash generation handles None previous_hash"""
        record_data = {"diagnosis": "Test"}
        timestamp = datetime(2024, 9, 1, 12, 0, 0)
        user_id = 666
        previous_hash = None
        
        hash_result = generate_hash(record_data, timestamp, user_id, previous_hash)
        
        assert len(hash_result) == 64
    
    def test_complex_record_data(self):
        """Test hash generation with complex nested record data"""
        record_data = {
            "patient_id": 123,
            "diagnosis": "Complex condition",
            "symptoms": ["fever", "cough", "fatigue"],
            "prescription": {
                "medication": "Medicine A",
                "dosage": "500mg",
                "frequency": "twice daily",
                "duration": "7 days"
            },
            "notes": "Patient shows improvement"
        }
        timestamp = datetime(2024, 10, 15, 14, 30, 0)
        user_id = 777
        previous_hash = "complex_prev"
        
        hash_result = generate_hash(record_data, timestamp, user_id, previous_hash)
        
        assert len(hash_result) == 64
    
    def test_special_characters_in_data(self):
        """Test hash generation with special characters"""
        record_data = {
            "diagnosis": "Test with special chars: @#$%^&*()",
            "notes": "Unicode: \u00e9\u00e8\u00ea",
            "prescription": "Medication with 'quotes' and \"double quotes\""
        }
        timestamp = datetime(2024, 11, 1, 9, 15, 0)
        user_id = 888
        previous_hash = "special_chars"
        
        hash_result = generate_hash(record_data, timestamp, user_id, previous_hash)
        
        assert len(hash_result) == 64
    
    def test_key_order_independence(self):
        """Test that dictionary key order doesn't affect hash (sorted keys)"""
        timestamp = datetime(2024, 12, 1, 10, 0, 0)
        user_id = 999
        previous_hash = "order_test"
        
        # Same data, different key order
        record_data1 = {"a": 1, "b": 2, "c": 3}
        record_data2 = {"c": 3, "a": 1, "b": 2}
        
        hash1 = generate_hash(record_data1, timestamp, user_id, previous_hash)
        hash2 = generate_hash(record_data2, timestamp, user_id, previous_hash)
        
        # Should produce same hash due to sorted keys
        assert hash1 == hash2
    
    def test_large_record_data(self):
        """Test hash generation with large record data"""
        record_data = {
            "diagnosis": "A" * 1000,
            "notes": "B" * 1000,
            "prescription": "C" * 1000
        }
        timestamp = datetime(2024, 12, 15, 11, 0, 0)
        user_id = 1000
        previous_hash = "large_data"
        
        hash_result = generate_hash(record_data, timestamp, user_id, previous_hash)
        
        # Hash should still be 64 characters regardless of input size
        assert len(hash_result) == 64
    
    def test_numeric_values_in_record(self):
        """Test hash generation with numeric values"""
        record_data = {
            "patient_id": 12345,
            "temperature": 98.6,
            "blood_pressure": {"systolic": 120, "diastolic": 80},
            "heart_rate": 72
        }
        timestamp = datetime(2024, 12, 20, 15, 30, 0)
        user_id = 1111
        previous_hash = "numeric_test"
        
        hash_result = generate_hash(record_data, timestamp, user_id, previous_hash)
        
        assert len(hash_result) == 64
    
    def test_boolean_values_in_record(self):
        """Test hash generation with boolean values"""
        record_data = {
            "is_critical": True,
            "requires_followup": False,
            "allergies_present": True
        }
        timestamp = datetime(2024, 12, 25, 16, 0, 0)
        user_id = 1212
        previous_hash = "boolean_test"
        
        hash_result = generate_hash(record_data, timestamp, user_id, previous_hash)
        
        assert len(hash_result) == 64



class TestAuditChainCreation:
    """Test suite for audit chain entry creation"""
    
    def test_create_audit_entry_genesis_block(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test audit chain creation for first entry (genesis block)"""
        from app.services.blockchain_service import create_audit_entry
        from app.models.medical_record import MedicalRecord
        from app.models.audit_chain import AuditChain
        
        # Create a medical record
        medical_record = MedicalRecord(
            patient_id=sample_patient.id,
            doctor_id=sample_doctor.id,
            consultation_notes="Patient presents with fever and cough",
            diagnosis="Common cold",
            prescription="Rest and fluids, Paracetamol 500mg twice daily",
            version_number=1,
            created_by=sample_user.id
        )
        db_session.add(medical_record)
        db_session.commit()
        db_session.refresh(medical_record)
        
        # Create audit entry (should be genesis block)
        audit_entry = create_audit_entry(db_session, medical_record, sample_user.id)
        
        # Verify audit entry was created
        assert audit_entry is not None
        assert audit_entry.id is not None
        
        # Verify it's a genesis block (previous_hash = "0")
        assert audit_entry.previous_hash == "0"
        
        # Verify record linkage
        assert audit_entry.record_id == medical_record.id
        assert audit_entry.record_type == "medical_record"
        
        # Verify hash was generated
        assert len(audit_entry.hash) == 64
        assert audit_entry.hash != "0"
        
        # Verify user linkage
        assert audit_entry.user_id == sample_user.id
        
        # Verify not tampered
        assert audit_entry.is_tampered is False
        
        # Verify record data was stored
        assert audit_entry.record_data is not None
        assert audit_entry.record_data["consultation_notes"] == medical_record.consultation_notes
        assert audit_entry.record_data["diagnosis"] == medical_record.diagnosis
        assert audit_entry.record_data["prescription"] == medical_record.prescription
        assert audit_entry.record_data["patient_id"] == medical_record.patient_id
        assert audit_entry.record_data["doctor_id"] == medical_record.doctor_id
        assert audit_entry.record_data["version_number"] == medical_record.version_number
    
    def test_create_audit_entry_subsequent_entries(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test audit chain creation for subsequent entries (proper linking)"""
        from app.services.blockchain_service import create_audit_entry
        from app.models.medical_record import MedicalRecord
        from app.models.audit_chain import AuditChain
        
        # Create first medical record and audit entry
        medical_record1 = MedicalRecord(
            patient_id=sample_patient.id,
            doctor_id=sample_doctor.id,
            consultation_notes="First consultation",
            diagnosis="Diagnosis 1",
            prescription="Prescription 1",
            version_number=1,
            created_by=sample_user.id
        )
        db_session.add(medical_record1)
        db_session.commit()
        db_session.refresh(medical_record1)
        
        audit_entry1 = create_audit_entry(db_session, medical_record1, sample_user.id)
        
        # Create second medical record and audit entry
        medical_record2 = MedicalRecord(
            patient_id=sample_patient.id,
            doctor_id=sample_doctor.id,
            consultation_notes="Second consultation",
            diagnosis="Diagnosis 2",
            prescription="Prescription 2",
            version_number=1,
            created_by=sample_user.id
        )
        db_session.add(medical_record2)
        db_session.commit()
        db_session.refresh(medical_record2)
        
        audit_entry2 = create_audit_entry(db_session, medical_record2, sample_user.id)
        
        # Verify second entry links to first entry
        assert audit_entry2.previous_hash == audit_entry1.hash
        assert audit_entry2.previous_hash != "0"
        
        # Verify both entries have different hashes
        assert audit_entry1.hash != audit_entry2.hash
        
        # Verify record linkage
        assert audit_entry2.record_id == medical_record2.id
        assert audit_entry2.record_type == "medical_record"
        
        # Create third entry to verify chain continues
        medical_record3 = MedicalRecord(
            patient_id=sample_patient.id,
            doctor_id=sample_doctor.id,
            consultation_notes="Third consultation",
            diagnosis="Diagnosis 3",
            prescription="Prescription 3",
            version_number=1,
            created_by=sample_user.id
        )
        db_session.add(medical_record3)
        db_session.commit()
        db_session.refresh(medical_record3)
        
        audit_entry3 = create_audit_entry(db_session, medical_record3, sample_user.id)
        
        # Verify third entry links to second entry
        assert audit_entry3.previous_hash == audit_entry2.hash
        
        # Verify chain integrity: entry1 -> entry2 -> entry3
        assert audit_entry1.previous_hash == "0"
        assert audit_entry2.previous_hash == audit_entry1.hash
        assert audit_entry3.previous_hash == audit_entry2.hash
    
    def test_create_audit_entry_with_empty_fields(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test audit chain creation with empty/null medical record fields"""
        from app.services.blockchain_service import create_audit_entry
        from app.models.medical_record import MedicalRecord
        
        # Create medical record with empty fields
        medical_record = MedicalRecord(
            patient_id=sample_patient.id,
            doctor_id=sample_doctor.id,
            consultation_notes=None,
            diagnosis=None,
            prescription=None,
            version_number=1,
            created_by=sample_user.id
        )
        db_session.add(medical_record)
        db_session.commit()
        db_session.refresh(medical_record)
        
        # Create audit entry
        audit_entry = create_audit_entry(db_session, medical_record, sample_user.id)
        
        # Verify audit entry was created successfully
        assert audit_entry is not None
        assert len(audit_entry.hash) == 64
        
        # Verify record data handles None values
        assert audit_entry.record_data["consultation_notes"] is None
        assert audit_entry.record_data["diagnosis"] is None
        assert audit_entry.record_data["prescription"] is None
    
    def test_create_audit_entry_timestamp(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test that audit entry has proper timestamp"""
        from app.services.blockchain_service import create_audit_entry
        from app.models.medical_record import MedicalRecord
        from datetime import datetime, timedelta
        
        # Create medical record
        medical_record = MedicalRecord(
            patient_id=sample_patient.id,
            doctor_id=sample_doctor.id,
            consultation_notes="Test consultation",
            diagnosis="Test diagnosis",
            prescription="Test prescription",
            version_number=1,
            created_by=sample_user.id
        )
        db_session.add(medical_record)
        db_session.commit()
        db_session.refresh(medical_record)
        
        # Record time before creating audit entry
        before_time = datetime.utcnow()
        
        # Create audit entry
        audit_entry = create_audit_entry(db_session, medical_record, sample_user.id)
        
        # Record time after creating audit entry
        after_time = datetime.utcnow()
        
        # Verify timestamp is within expected range
        assert audit_entry.timestamp is not None
        assert before_time <= audit_entry.timestamp <= after_time
    
    def test_create_audit_entry_persists_to_database(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test that audit entry is properly persisted to database"""
        from app.services.blockchain_service import create_audit_entry
        from app.models.medical_record import MedicalRecord
        from app.models.audit_chain import AuditChain
        
        # Create medical record
        medical_record = MedicalRecord(
            patient_id=sample_patient.id,
            doctor_id=sample_doctor.id,
            consultation_notes="Persistence test",
            diagnosis="Test diagnosis",
            prescription="Test prescription",
            version_number=1,
            created_by=sample_user.id
        )
        db_session.add(medical_record)
        db_session.commit()
        db_session.refresh(medical_record)
        
        # Create audit entry
        audit_entry = create_audit_entry(db_session, medical_record, sample_user.id)
        audit_entry_id = audit_entry.id
        
        # Clear session to force database read
        db_session.expire_all()
        
        # Retrieve audit entry from database
        retrieved_entry = db_session.query(AuditChain).filter(AuditChain.id == audit_entry_id).first()
        
        # Verify entry was persisted
        assert retrieved_entry is not None
        assert retrieved_entry.id == audit_entry_id
        assert retrieved_entry.hash == audit_entry.hash
        assert retrieved_entry.previous_hash == audit_entry.previous_hash
        assert retrieved_entry.record_id == medical_record.id
    
    def test_create_audit_entry_version_tracking(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test audit chain tracks version numbers correctly"""
        from app.services.blockchain_service import create_audit_entry
        from app.models.medical_record import MedicalRecord
        
        # Create original medical record (version 1)
        medical_record_v1 = MedicalRecord(
            patient_id=sample_patient.id,
            doctor_id=sample_doctor.id,
            consultation_notes="Original notes",
            diagnosis="Original diagnosis",
            prescription="Original prescription",
            version_number=1,
            created_by=sample_user.id
        )
        db_session.add(medical_record_v1)
        db_session.commit()
        db_session.refresh(medical_record_v1)
        
        audit_entry_v1 = create_audit_entry(db_session, medical_record_v1, sample_user.id)
        
        # Create updated medical record (version 2)
        medical_record_v2 = MedicalRecord(
            patient_id=sample_patient.id,
            doctor_id=sample_doctor.id,
            consultation_notes="Updated notes",
            diagnosis="Updated diagnosis",
            prescription="Updated prescription",
            version_number=2,
            parent_record_id=medical_record_v1.id,
            created_by=sample_user.id
        )
        db_session.add(medical_record_v2)
        db_session.commit()
        db_session.refresh(medical_record_v2)
        
        audit_entry_v2 = create_audit_entry(db_session, medical_record_v2, sample_user.id)
        
        # Verify version numbers are tracked in audit data
        assert audit_entry_v1.record_data["version_number"] == 1
        assert audit_entry_v2.record_data["version_number"] == 2
        
        # Verify different versions produce different hashes
        assert audit_entry_v1.hash != audit_entry_v2.hash



class TestIntegrityVerification:
    """Test suite for integrity verification function"""
    
    def test_verify_record_integrity_success(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test successful integrity verification when hash matches"""
        from app.services.blockchain_service import create_audit_entry, verify_record_integrity
        from app.models.medical_record import MedicalRecord
        
        # Create a medical record
        medical_record = MedicalRecord(
            patient_id=sample_patient.id,
            doctor_id=sample_doctor.id,
            consultation_notes="Patient presents with fever",
            diagnosis="Viral infection",
            prescription="Rest and fluids",
            version_number=1,
            created_by=sample_user.id
        )
        db_session.add(medical_record)
        db_session.commit()
        db_session.refresh(medical_record)
        
        # Create audit entry
        audit_entry = create_audit_entry(db_session, medical_record, sample_user.id)
        db_session.commit()
        
        # Verify integrity - should return True (no tampering)
        is_valid = verify_record_integrity(db_session, medical_record.id)
        
        assert is_valid is True
    
    def test_verify_record_integrity_tampered_data(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test failed verification when record data is tampered"""
        from app.services.blockchain_service import create_audit_entry, verify_record_integrity
        from app.models.medical_record import MedicalRecord
        
        # Create a medical record
        medical_record = MedicalRecord(
            patient_id=sample_patient.id,
            doctor_id=sample_doctor.id,
            consultation_notes="Original notes",
            diagnosis="Original diagnosis",
            prescription="Original prescription",
            version_number=1,
            created_by=sample_user.id
        )
        db_session.add(medical_record)
        db_session.commit()
        db_session.refresh(medical_record)
        
        # Create audit entry
        audit_entry = create_audit_entry(db_session, medical_record, sample_user.id)
        db_session.commit()
        
        # Tamper with the medical record (simulate unauthorized modification)
        medical_record.diagnosis = "Tampered diagnosis"
        db_session.commit()
        
        # Verify integrity - should return False (tampering detected)
        is_valid = verify_record_integrity(db_session, medical_record.id)
        
        assert is_valid is False
    
    def test_verify_record_integrity_missing_audit_entry(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test verification fails gracefully when audit entry is missing"""
        from app.services.blockchain_service import verify_record_integrity
        from app.models.medical_record import MedicalRecord
        
        # Create a medical record WITHOUT creating audit entry
        medical_record = MedicalRecord(
            patient_id=sample_patient.id,
            doctor_id=sample_doctor.id,
            consultation_notes="Test notes",
            diagnosis="Test diagnosis",
            prescription="Test prescription",
            version_number=1,
            created_by=sample_user.id
        )
        db_session.add(medical_record)
        db_session.commit()
        db_session.refresh(medical_record)
        
        # Verify integrity - should raise ValueError
        with pytest.raises(ValueError, match="No audit entry found"):
            verify_record_integrity(db_session, medical_record.id)
    
    def test_verify_record_integrity_missing_medical_record(self, db_session):
        """Test verification fails gracefully when medical record is missing"""
        from app.services.blockchain_service import verify_record_integrity
        
        # Try to verify a non-existent medical record
        non_existent_id = 99999
        
        # Should raise ValueError (audit entry check happens first)
        with pytest.raises(ValueError, match="No audit entry found"):
            verify_record_integrity(db_session, non_existent_id)
    
    def test_verify_record_integrity_tampered_consultation_notes(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test verification detects tampering in consultation notes"""
        from app.services.blockchain_service import create_audit_entry, verify_record_integrity
        from app.models.medical_record import MedicalRecord
        
        # Create medical record
        medical_record = MedicalRecord(
            patient_id=sample_patient.id,
            doctor_id=sample_doctor.id,
            consultation_notes="Original consultation notes",
            diagnosis="Diagnosis",
            prescription="Prescription",
            version_number=1,
            created_by=sample_user.id
        )
        db_session.add(medical_record)
        db_session.commit()
        db_session.refresh(medical_record)
        
        # Create audit entry
        create_audit_entry(db_session, medical_record, sample_user.id)
        db_session.commit()
        
        # Tamper with consultation notes
        medical_record.consultation_notes = "Tampered notes"
        db_session.commit()
        
        # Verify - should detect tampering
        is_valid = verify_record_integrity(db_session, medical_record.id)
        assert is_valid is False
    
    def test_verify_record_integrity_tampered_prescription(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test verification detects tampering in prescription"""
        from app.services.blockchain_service import create_audit_entry, verify_record_integrity
        from app.models.medical_record import MedicalRecord
        
        # Create medical record
        medical_record = MedicalRecord(
            patient_id=sample_patient.id,
            doctor_id=sample_doctor.id,
            consultation_notes="Notes",
            diagnosis="Diagnosis",
            prescription="Paracetamol 500mg",
            version_number=1,
            created_by=sample_user.id
        )
        db_session.add(medical_record)
        db_session.commit()
        db_session.refresh(medical_record)
        
        # Create audit entry
        create_audit_entry(db_session, medical_record, sample_user.id)
        db_session.commit()
        
        # Tamper with prescription
        medical_record.prescription = "Morphine 100mg"  # Unauthorized change
        db_session.commit()
        
        # Verify - should detect tampering
        is_valid = verify_record_integrity(db_session, medical_record.id)
        assert is_valid is False
    
    def test_verify_record_integrity_multiple_records(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test verification works correctly with multiple records"""
        from app.services.blockchain_service import create_audit_entry, verify_record_integrity
        from app.models.medical_record import MedicalRecord
        
        # Create multiple medical records
        records = []
        for i in range(3):
            medical_record = MedicalRecord(
                patient_id=sample_patient.id,
                doctor_id=sample_doctor.id,
                consultation_notes=f"Notes {i}",
                diagnosis=f"Diagnosis {i}",
                prescription=f"Prescription {i}",
                version_number=1,
                created_by=sample_user.id
            )
            db_session.add(medical_record)
            db_session.commit()
            db_session.refresh(medical_record)
            
            create_audit_entry(db_session, medical_record, sample_user.id)
            db_session.commit()
            
            records.append(medical_record)
        
        # Verify all records are valid
        for record in records:
            is_valid = verify_record_integrity(db_session, record.id)
            assert is_valid is True
        
        # Tamper with middle record
        records[1].diagnosis = "Tampered"
        db_session.commit()
        
        # Verify first and third are still valid
        assert verify_record_integrity(db_session, records[0].id) is True
        assert verify_record_integrity(db_session, records[2].id) is True
        
        # Verify second is invalid
        assert verify_record_integrity(db_session, records[1].id) is False
    
    def test_verify_record_integrity_with_null_fields(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test verification works with null/empty fields"""
        from app.services.blockchain_service import create_audit_entry, verify_record_integrity
        from app.models.medical_record import MedicalRecord
        
        # Create medical record with null fields
        medical_record = MedicalRecord(
            patient_id=sample_patient.id,
            doctor_id=sample_doctor.id,
            consultation_notes=None,
            diagnosis=None,
            prescription=None,
            version_number=1,
            created_by=sample_user.id
        )
        db_session.add(medical_record)
        db_session.commit()
        db_session.refresh(medical_record)
        
        # Create audit entry
        create_audit_entry(db_session, medical_record, sample_user.id)
        db_session.commit()
        
        # Verify - should be valid
        is_valid = verify_record_integrity(db_session, medical_record.id)
        assert is_valid is True
        
        # Tamper by adding data to null field
        medical_record.diagnosis = "Added diagnosis"
        db_session.commit()
        
        # Verify - should detect tampering
        is_valid = verify_record_integrity(db_session, medical_record.id)
        assert is_valid is False
    
    def test_verify_record_integrity_version_tracking(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test verification works correctly with versioned records"""
        from app.services.blockchain_service import create_audit_entry, verify_record_integrity
        from app.models.medical_record import MedicalRecord
        
        # Create version 1
        record_v1 = MedicalRecord(
            patient_id=sample_patient.id,
            doctor_id=sample_doctor.id,
            consultation_notes="Version 1 notes",
            diagnosis="Version 1 diagnosis",
            prescription="Version 1 prescription",
            version_number=1,
            created_by=sample_user.id
        )
        db_session.add(record_v1)
        db_session.commit()
        db_session.refresh(record_v1)
        
        create_audit_entry(db_session, record_v1, sample_user.id)
        db_session.commit()
        
        # Create version 2
        record_v2 = MedicalRecord(
            patient_id=sample_patient.id,
            doctor_id=sample_doctor.id,
            consultation_notes="Version 2 notes",
            diagnosis="Version 2 diagnosis",
            prescription="Version 2 prescription",
            version_number=2,
            parent_record_id=record_v1.id,
            created_by=sample_user.id
        )
        db_session.add(record_v2)
        db_session.commit()
        db_session.refresh(record_v2)
        
        create_audit_entry(db_session, record_v2, sample_user.id)
        db_session.commit()
        
        # Both versions should verify successfully
        assert verify_record_integrity(db_session, record_v1.id) is True
        assert verify_record_integrity(db_session, record_v2.id) is True
        
        # Tamper with version 1
        record_v1.diagnosis = "Tampered v1"
        db_session.commit()
        
        # Version 1 should fail, version 2 should still pass
        assert verify_record_integrity(db_session, record_v1.id) is False
        assert verify_record_integrity(db_session, record_v2.id) is True
    
    def test_verify_record_integrity_uses_latest_audit_entry(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test that verification uses the most recent audit entry"""
        from app.services.blockchain_service import create_audit_entry, verify_record_integrity
        from app.models.medical_record import MedicalRecord
        
        # Create medical record
        medical_record = MedicalRecord(
            patient_id=sample_patient.id,
            doctor_id=sample_doctor.id,
            consultation_notes="Original notes",
            diagnosis="Original diagnosis",
            prescription="Original prescription",
            version_number=1,
            created_by=sample_user.id
        )
        db_session.add(medical_record)
        db_session.commit()
        db_session.refresh(medical_record)
        
        # Create first audit entry
        audit_entry1 = create_audit_entry(db_session, medical_record, sample_user.id)
        db_session.commit()
        
        # Verify - should be valid
        assert verify_record_integrity(db_session, medical_record.id) is True
        
        # Update the record
        medical_record.diagnosis = "Updated diagnosis"
        db_session.commit()
        
        # Create second audit entry for the updated record
        audit_entry2 = create_audit_entry(db_session, medical_record, sample_user.id)
        db_session.commit()
        
        # Verify - should use latest audit entry and be valid
        assert verify_record_integrity(db_session, medical_record.id) is True
        
        # Tamper with the record
        medical_record.diagnosis = "Tampered diagnosis"
        db_session.commit()
        
        # Verify - should detect tampering against latest audit entry
        assert verify_record_integrity(db_session, medical_record.id) is False



class TestChainVerification:
    """Test suite for chain verification function"""
    
    def test_verify_empty_chain(self, db_session):
        """Test verification of empty chain returns valid"""
        from app.services.blockchain_service import verify_chain_integrity
        
        result = verify_chain_integrity(db_session)
        
        assert result['is_valid'] is True
        assert result['total_blocks'] == 0
        assert result['verified_blocks'] == 0
        assert len(result['inconsistencies']) == 0
    
    def test_verify_single_block_chain(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test verification of chain with single genesis block"""
        from app.services.blockchain_service import create_audit_entry, verify_chain_integrity
        from app.models.medical_record import MedicalRecord
        
        # Create single medical record
        medical_record = MedicalRecord(
            patient_id=sample_patient.id,
            doctor_id=sample_doctor.id,
            consultation_notes="Genesis block test",
            diagnosis="Test diagnosis",
            prescription="Test prescription",
            version_number=1,
            created_by=sample_user.id
        )
        db_session.add(medical_record)
        db_session.commit()
        db_session.refresh(medical_record)
        
        # Create audit entry (genesis block)
        create_audit_entry(db_session, medical_record, sample_user.id)
        db_session.commit()
        
        # Verify chain
        result = verify_chain_integrity(db_session)
        
        assert result['is_valid'] is True
        assert result['total_blocks'] == 1
        assert result['verified_blocks'] == 1
        assert len(result['inconsistencies']) == 0
    
    def test_verify_valid_chain_multiple_blocks(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test verification of valid chain with multiple blocks"""
        from app.services.blockchain_service import create_audit_entry, verify_chain_integrity
        from app.models.medical_record import MedicalRecord
        
        # Create multiple medical records
        for i in range(5):
            medical_record = MedicalRecord(
                patient_id=sample_patient.id,
                doctor_id=sample_doctor.id,
                consultation_notes=f"Consultation {i}",
                diagnosis=f"Diagnosis {i}",
                prescription=f"Prescription {i}",
                version_number=1,
                created_by=sample_user.id
            )
            db_session.add(medical_record)
            db_session.commit()
            db_session.refresh(medical_record)
            
            create_audit_entry(db_session, medical_record, sample_user.id)
            db_session.commit()
        
        # Verify chain
        result = verify_chain_integrity(db_session)
        
        assert result['is_valid'] is True
        assert result['total_blocks'] == 5
        assert result['verified_blocks'] == 5
        assert len(result['inconsistencies']) == 0
    
    def test_verify_chain_detects_broken_link(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test that chain verification detects broken previous_hash links"""
        from app.services.blockchain_service import create_audit_entry, verify_chain_integrity
        from app.models.medical_record import MedicalRecord
        from app.models.audit_chain import AuditChain
        
        # Create three medical records
        for i in range(3):
            medical_record = MedicalRecord(
                patient_id=sample_patient.id,
                doctor_id=sample_doctor.id,
                consultation_notes=f"Consultation {i}",
                diagnosis=f"Diagnosis {i}",
                prescription=f"Prescription {i}",
                version_number=1,
                created_by=sample_user.id
            )
            db_session.add(medical_record)
            db_session.commit()
            db_session.refresh(medical_record)
            
            create_audit_entry(db_session, medical_record, sample_user.id)
            db_session.commit()
        
        # Break the chain by modifying the second block's previous_hash
        second_block = db_session.query(AuditChain).order_by(AuditChain.id.asc()).offset(1).first()
        second_block.previous_hash = "broken_link_hash"
        db_session.commit()
        
        # Verify chain
        result = verify_chain_integrity(db_session)
        
        assert result['is_valid'] is False
        assert result['total_blocks'] == 3
        assert len(result['inconsistencies']) > 0
        
        # Check that the error is about broken chain link
        broken_link_error = next(
            (err for err in result['inconsistencies'] if 'Chain link broken' in err['error']),
            None
        )
        assert broken_link_error is not None
        assert broken_link_error['block_index'] == 1
    
    def test_verify_chain_detects_corrupted_hash(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test that chain verification detects corrupted block hashes"""
        from app.services.blockchain_service import create_audit_entry, verify_chain_integrity
        from app.models.medical_record import MedicalRecord
        from app.models.audit_chain import AuditChain
        
        # Create three medical records
        for i in range(3):
            medical_record = MedicalRecord(
                patient_id=sample_patient.id,
                doctor_id=sample_doctor.id,
                consultation_notes=f"Consultation {i}",
                diagnosis=f"Diagnosis {i}",
                prescription=f"Prescription {i}",
                version_number=1,
                created_by=sample_user.id
            )
            db_session.add(medical_record)
            db_session.commit()
            db_session.refresh(medical_record)
            
            create_audit_entry(db_session, medical_record, sample_user.id)
            db_session.commit()
        
        # Corrupt the hash of the second block
        second_block = db_session.query(AuditChain).order_by(AuditChain.id.asc()).offset(1).first()
        second_block.hash = "corrupted_hash_value_1234567890abcdef1234567890abcdef12345678"
        db_session.commit()
        
        # Verify chain
        result = verify_chain_integrity(db_session)
        
        assert result['is_valid'] is False
        assert result['total_blocks'] == 3
        assert len(result['inconsistencies']) >= 2  # Corrupted hash + broken link to next block
        
        # Check that there's an error about hash mismatch
        hash_mismatch_error = next(
            (err for err in result['inconsistencies'] if 'hash mismatch' in err['error']),
            None
        )
        assert hash_mismatch_error is not None
    
    def test_verify_chain_detects_invalid_genesis_block(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test that chain verification detects invalid genesis block"""
        from app.services.blockchain_service import create_audit_entry, verify_chain_integrity
        from app.models.medical_record import MedicalRecord
        from app.models.audit_chain import AuditChain
        
        # Create medical record
        medical_record = MedicalRecord(
            patient_id=sample_patient.id,
            doctor_id=sample_doctor.id,
            consultation_notes="Genesis test",
            diagnosis="Test",
            prescription="Test",
            version_number=1,
            created_by=sample_user.id
        )
        db_session.add(medical_record)
        db_session.commit()
        db_session.refresh(medical_record)
        
        create_audit_entry(db_session, medical_record, sample_user.id)
        db_session.commit()
        
        # Corrupt genesis block by changing previous_hash from "0"
        genesis_block = db_session.query(AuditChain).order_by(AuditChain.id.asc()).first()
        genesis_block.previous_hash = "not_zero"
        db_session.commit()
        
        # Verify chain
        result = verify_chain_integrity(db_session)
        
        assert result['is_valid'] is False
        assert len(result['inconsistencies']) > 0
        
        # Check for genesis block error
        genesis_error = next(
            (err for err in result['inconsistencies'] if 'Genesis block' in err['error']),
            None
        )
        assert genesis_error is not None
        assert genesis_error['block_index'] == 0
        assert genesis_error['expected'] == "0"
    
    def test_verify_chain_detects_tampered_record_data(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test that chain verification detects tampering in record data"""
        from app.services.blockchain_service import create_audit_entry, verify_chain_integrity
        from app.models.medical_record import MedicalRecord
        from app.models.audit_chain import AuditChain
        from sqlalchemy.orm.attributes import flag_modified
        
        # Create medical record
        medical_record = MedicalRecord(
            patient_id=sample_patient.id,
            doctor_id=sample_doctor.id,
            consultation_notes="Original notes",
            diagnosis="Original diagnosis",
            prescription="Original prescription",
            version_number=1,
            created_by=sample_user.id
        )
        db_session.add(medical_record)
        db_session.commit()
        db_session.refresh(medical_record)
        
        create_audit_entry(db_session, medical_record, sample_user.id)
        db_session.commit()
        
        # Tamper with the audit chain's record_data
        audit_block = db_session.query(AuditChain).first()
        audit_block.record_data['diagnosis'] = "Tampered diagnosis"
        flag_modified(audit_block, 'record_data')  # Mark JSONB field as modified
        db_session.commit()
        
        # Verify chain
        result = verify_chain_integrity(db_session)
        
        assert result['is_valid'] is False
        assert len(result['inconsistencies']) > 0
        
        # Check for hash mismatch error
        hash_error = next(
            (err for err in result['inconsistencies'] if 'hash mismatch' in err['error']),
            None
        )
        assert hash_error is not None
    
    def test_verify_chain_with_multiple_inconsistencies(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test chain verification reports all inconsistencies"""
        from app.services.blockchain_service import create_audit_entry, verify_chain_integrity
        from app.models.medical_record import MedicalRecord
        from app.models.audit_chain import AuditChain
        
        # Create five medical records
        for i in range(5):
            medical_record = MedicalRecord(
                patient_id=sample_patient.id,
                doctor_id=sample_doctor.id,
                consultation_notes=f"Consultation {i}",
                diagnosis=f"Diagnosis {i}",
                prescription=f"Prescription {i}",
                version_number=1,
                created_by=sample_user.id
            )
            db_session.add(medical_record)
            db_session.commit()
            db_session.refresh(medical_record)
            
            create_audit_entry(db_session, medical_record, sample_user.id)
            db_session.commit()
        
        # Introduce multiple errors
        blocks = db_session.query(AuditChain).order_by(AuditChain.id.asc()).all()
        
        # Corrupt genesis block
        blocks[0].previous_hash = "invalid"
        
        # Corrupt hash of second block
        blocks[1].hash = "corrupted_hash_1234567890abcdef1234567890abcdef12345678"
        
        # Break link in fourth block
        blocks[3].previous_hash = "broken_link"
        
        db_session.commit()
        
        # Verify chain
        result = verify_chain_integrity(db_session)
        
        assert result['is_valid'] is False
        assert result['total_blocks'] == 5
        assert len(result['inconsistencies']) >= 3  # At least 3 errors introduced
    
    def test_verify_chain_result_structure(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test that chain verification returns correct result structure"""
        from app.services.blockchain_service import create_audit_entry, verify_chain_integrity
        from app.models.medical_record import MedicalRecord
        
        # Create medical record
        medical_record = MedicalRecord(
            patient_id=sample_patient.id,
            doctor_id=sample_doctor.id,
            consultation_notes="Structure test",
            diagnosis="Test",
            prescription="Test",
            version_number=1,
            created_by=sample_user.id
        )
        db_session.add(medical_record)
        db_session.commit()
        db_session.refresh(medical_record)
        
        create_audit_entry(db_session, medical_record, sample_user.id)
        db_session.commit()
        
        # Verify chain
        result = verify_chain_integrity(db_session)
        
        # Check result structure
        assert 'is_valid' in result
        assert 'total_blocks' in result
        assert 'verified_blocks' in result
        assert 'inconsistencies' in result
        
        assert isinstance(result['is_valid'], bool)
        assert isinstance(result['total_blocks'], int)
        assert isinstance(result['verified_blocks'], int)
        assert isinstance(result['inconsistencies'], list)
    
    def test_verify_chain_inconsistency_details(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test that inconsistencies contain detailed information"""
        from app.services.blockchain_service import create_audit_entry, verify_chain_integrity
        from app.models.medical_record import MedicalRecord
        from app.models.audit_chain import AuditChain
        
        # Create two medical records
        for i in range(2):
            medical_record = MedicalRecord(
                patient_id=sample_patient.id,
                doctor_id=sample_doctor.id,
                consultation_notes=f"Consultation {i}",
                diagnosis=f"Diagnosis {i}",
                prescription=f"Prescription {i}",
                version_number=1,
                created_by=sample_user.id
            )
            db_session.add(medical_record)
            db_session.commit()
            db_session.refresh(medical_record)
            
            create_audit_entry(db_session, medical_record, sample_user.id)
            db_session.commit()
        
        # Break the chain
        second_block = db_session.query(AuditChain).order_by(AuditChain.id.asc()).offset(1).first()
        second_block.previous_hash = "broken"
        db_session.commit()
        
        # Verify chain
        result = verify_chain_integrity(db_session)
        
        # Check inconsistency details
        assert len(result['inconsistencies']) > 0
        
        inconsistency = result['inconsistencies'][0]
        assert 'block_id' in inconsistency
        assert 'block_index' in inconsistency
        assert 'error' in inconsistency
        assert 'expected' in inconsistency
        assert 'actual' in inconsistency
    
    def test_verify_chain_counts_verified_blocks_correctly(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test that verified_blocks count is accurate"""
        from app.services.blockchain_service import create_audit_entry, verify_chain_integrity
        from app.models.medical_record import MedicalRecord
        from app.models.audit_chain import AuditChain
        
        # Create four medical records
        for i in range(4):
            medical_record = MedicalRecord(
                patient_id=sample_patient.id,
                doctor_id=sample_doctor.id,
                consultation_notes=f"Consultation {i}",
                diagnosis=f"Diagnosis {i}",
                prescription=f"Prescription {i}",
                version_number=1,
                created_by=sample_user.id
            )
            db_session.add(medical_record)
            db_session.commit()
            db_session.refresh(medical_record)
            
            create_audit_entry(db_session, medical_record, sample_user.id)
            db_session.commit()
        
        # Corrupt only the third block's hash
        blocks = db_session.query(AuditChain).order_by(AuditChain.id.asc()).all()
        blocks[2].hash = "corrupted_hash_1234567890abcdef1234567890abcdef12345678"
        db_session.commit()
        
        # Verify chain
        result = verify_chain_integrity(db_session)
        
        assert result['is_valid'] is False
        assert result['total_blocks'] == 4
        # Blocks 0, 1, and 3 should verify successfully (3 blocks)
        # Block 2 has corrupted hash, so it won't be counted
        assert result['verified_blocks'] == 3
    
    def test_verify_chain_large_chain(self, db_session, sample_patient, sample_doctor, sample_user):
        """Test chain verification with larger chain (performance test)"""
        from app.services.blockchain_service import create_audit_entry, verify_chain_integrity
        from app.models.medical_record import MedicalRecord
        
        # Create 20 medical records
        for i in range(20):
            medical_record = MedicalRecord(
                patient_id=sample_patient.id,
                doctor_id=sample_doctor.id,
                consultation_notes=f"Consultation {i}",
                diagnosis=f"Diagnosis {i}",
                prescription=f"Prescription {i}",
                version_number=1,
                created_by=sample_user.id
            )
            db_session.add(medical_record)
            db_session.commit()
            db_session.refresh(medical_record)
            
            create_audit_entry(db_session, medical_record, sample_user.id)
            db_session.commit()
        
        # Verify chain
        result = verify_chain_integrity(db_session)
        
        assert result['is_valid'] is True
        assert result['total_blocks'] == 20
        assert result['verified_blocks'] == 20
        assert len(result['inconsistencies']) == 0
