"""
Tests for blockchain integration with medical records
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.main import app
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.appointment import Appointment, AppointmentStatus, AppointmentType
from app.models.medical_record import MedicalRecord
from app.models.audit_chain import AuditChain
from app.core.security import create_access_token, get_password_hash


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def test_users(db_session: Session):
    """Create test users with different roles"""
    users = {}
    
    # Create doctor user
    doctor_user = User(
        name="Dr. Smith",
        email="doctor@test.com",
        password_hash=get_password_hash("password123"),
        role=UserRole.DOCTOR
    )
    db_session.add(doctor_user)
    db_session.flush()
    
    doctor = Doctor(
        user_id=doctor_user.id,
        specialization="General Medicine",
        license_number="DOC123",
        average_consultation_duration=15
    )
    db_session.add(doctor)
    users['doctor'] = {'user': doctor_user, 'doctor': doctor}
    
    # Create patient user
    patient_user = User(
        name="John Doe",
        email="patient@test.com",
        password_hash=get_password_hash("password123"),
        role=UserRole.PATIENT
    )
    db_session.add(patient_user)
    db_session.flush()
    
    patient = Patient(
        user_id=patient_user.id,
        date_of_birth=datetime(1990, 1, 1),
        gender="Male",
        phone="1234567890"
    )
    db_session.add(patient)
    users['patient'] = {'user': patient_user, 'patient': patient}
    
    db_session.commit()
    
    # Refresh to get IDs
    for key in users:
        if 'user' in users[key]:
            db_session.refresh(users[key]['user'])
        if 'doctor' in users[key]:
            db_session.refresh(users[key]['doctor'])
        if 'patient' in users[key]:
            db_session.refresh(users[key]['patient'])
    
    return users


@pytest.fixture
def test_appointment(db_session: Session, test_users):
    """Create a test appointment"""
    doctor = test_users['doctor']['doctor']
    patient = test_users['patient']['patient']
    
    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        scheduled_time=datetime.now() + timedelta(hours=1),
        status=AppointmentStatus.SCHEDULED,
        appointment_type=AppointmentType.SCHEDULED
    )
    db_session.add(appointment)
    db_session.commit()
    db_session.refresh(appointment)
    
    return appointment


def get_auth_header(user: User) -> dict:
    """Generate authorization header for a user"""
    token = create_access_token(data={
        "user_id": user.id,
        "email": user.email,
        "role": user.role.value
    })
    return {"Authorization": f"Bearer {token}"}


class TestBlockchainIntegrationConsultationNotes:
    """Tests for blockchain integration with consultation notes"""
    
    def test_create_consultation_note_creates_audit_entry(self, client, db_session: Session, test_users, test_appointment):
        """Test that creating a consultation note creates an audit chain entry"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Patient has fever and cough",
            "diagnosis": "Common cold"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 201
        record = response.json()
        
        # Verify audit entry was created
        audit_entry = db_session.query(AuditChain).filter(
            AuditChain.record_id == record["id"],
            AuditChain.record_type == "medical_record"
        ).first()
        
        assert audit_entry is not None
        assert audit_entry.user_id == doctor_user.id
        assert audit_entry.hash is not None
        assert len(audit_entry.hash) == 64  # SHA-256 produces 64 hex characters
        assert audit_entry.previous_hash is not None
        assert audit_entry.is_tampered is False
        
        # Verify record data is stored in audit entry
        assert audit_entry.record_data is not None
        assert audit_entry.record_data["consultation_notes"] == payload["consultation_notes"]
        assert audit_entry.record_data["diagnosis"] == payload["diagnosis"]
        assert audit_entry.record_data["patient_id"] == test_appointment.patient_id
        assert audit_entry.record_data["doctor_id"] == test_users['doctor']['doctor'].id
    
    def test_genesis_block_has_previous_hash_zero(self, client, db_session: Session, test_users, test_appointment):
        """Test that the first audit entry (genesis block) has previous_hash = '0'"""
        # Clear any existing audit entries
        db_session.query(AuditChain).delete()
        db_session.commit()
        
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "First record in the chain",
            "diagnosis": "Genesis block test"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 201
        record = response.json()
        
        # Verify genesis block has previous_hash = "0"
        audit_entry = db_session.query(AuditChain).filter(
            AuditChain.record_id == record["id"]
        ).first()
        
        assert audit_entry is not None
        assert audit_entry.previous_hash == "0"
    
    def test_update_consultation_note_creates_audit_entry(self, client, db_session: Session, test_users, test_appointment):
        """Test that updating a consultation note creates a new audit chain entry"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Create initial consultation note
        create_payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Initial notes",
            "diagnosis": "Initial diagnosis"
        }
        
        create_response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=create_payload,
            headers=headers
        )
        assert create_response.status_code == 201
        original_record = create_response.json()
        
        # Get the audit entry for the original record
        original_audit = db_session.query(AuditChain).filter(
            AuditChain.record_id == original_record["id"]
        ).first()
        assert original_audit is not None
        
        # Update the consultation note
        update_payload = {
            "consultation_notes": "Updated notes",
            "diagnosis": "Updated diagnosis"
        }
        
        response = client.put(
            f"/api/v1/medical-records/consultation-notes/{original_record['id']}",
            json=update_payload,
            headers=headers
        )
        
        assert response.status_code == 200
        updated_record = response.json()
        
        # Verify new audit entry was created for the updated record
        updated_audit = db_session.query(AuditChain).filter(
            AuditChain.record_id == updated_record["id"]
        ).first()
        
        assert updated_audit is not None
        assert updated_audit.id != original_audit.id  # Different audit entries
        assert updated_audit.user_id == doctor_user.id
        assert updated_audit.hash is not None
        assert len(updated_audit.hash) == 64
        
        # Verify the new audit entry links to the previous one
        assert updated_audit.previous_hash == original_audit.hash
        
        # Verify record data reflects the update
        assert updated_audit.record_data["consultation_notes"] == update_payload["consultation_notes"]
        assert updated_audit.record_data["diagnosis"] == update_payload["diagnosis"]
        assert updated_audit.record_data["version_number"] == 2


class TestBlockchainIntegrationPrescriptions:
    """Tests for blockchain integration with prescriptions"""
    
    def test_create_prescription_creates_audit_entry(self, client, db_session: Session, test_users, test_appointment):
        """Test that creating a prescription creates an audit chain entry"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        payload = {
            "appointment_id": test_appointment.id,
            "medication": "Amoxicillin",
            "dosage": "500mg",
            "frequency": "Three times daily",
            "duration": "7 days"
        }
        
        response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 201
        record = response.json()
        
        # Verify audit entry was created
        audit_entry = db_session.query(AuditChain).filter(
            AuditChain.record_id == record["id"],
            AuditChain.record_type == "medical_record"
        ).first()
        
        assert audit_entry is not None
        assert audit_entry.user_id == doctor_user.id
        assert audit_entry.hash is not None
        assert len(audit_entry.hash) == 64
        assert audit_entry.previous_hash is not None
        assert audit_entry.is_tampered is False
        
        # Verify prescription data is stored in audit entry
        assert audit_entry.record_data is not None
        assert "Amoxicillin" in audit_entry.record_data["prescription"]
        assert audit_entry.record_data["patient_id"] == test_appointment.patient_id
    
    def test_update_prescription_creates_audit_entry(self, client, db_session: Session, test_users, test_appointment):
        """Test that updating a prescription creates a new audit chain entry"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Create initial prescription
        create_payload = {
            "appointment_id": test_appointment.id,
            "medication": "Paracetamol",
            "dosage": "500mg",
            "frequency": "Twice daily",
            "duration": "5 days"
        }
        
        create_response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=create_payload,
            headers=headers
        )
        assert create_response.status_code == 201
        original_record = create_response.json()
        
        # Get the audit entry for the original record
        original_audit = db_session.query(AuditChain).filter(
            AuditChain.record_id == original_record["id"]
        ).first()
        assert original_audit is not None
        
        # Update the prescription
        update_payload = {
            "medication": "Ibuprofen",
            "dosage": "400mg",
            "frequency": "Three times daily",
            "duration": "7 days"
        }
        
        response = client.put(
            f"/api/v1/medical-records/prescriptions/{original_record['id']}",
            json=update_payload,
            headers=headers
        )
        
        assert response.status_code == 200
        updated_record = response.json()
        
        # Verify new audit entry was created
        updated_audit = db_session.query(AuditChain).filter(
            AuditChain.record_id == updated_record["id"]
        ).first()
        
        assert updated_audit is not None
        assert updated_audit.id != original_audit.id
        assert updated_audit.user_id == doctor_user.id
        assert updated_audit.hash is not None
        
        # Verify chain linkage
        assert updated_audit.previous_hash == original_audit.hash
        
        # Verify updated prescription data
        assert "Ibuprofen" in updated_audit.record_data["prescription"]
        assert updated_audit.record_data["version_number"] == 2


class TestBlockchainChainIntegrity:
    """Tests for blockchain chain integrity"""
    
    def test_multiple_records_form_valid_chain(self, client, db_session: Session, test_users):
        """Test that multiple records form a valid blockchain chain"""
        doctor_user = test_users['doctor']['user']
        patient = test_users['patient']['patient']
        doctor = test_users['doctor']['doctor']
        headers = get_auth_header(doctor_user)
        
        # Clear existing audit entries
        db_session.query(AuditChain).delete()
        db_session.commit()
        
        # Create multiple appointments and records
        records = []
        for i in range(3):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=datetime.now() + timedelta(hours=i+1),
                status=AppointmentStatus.SCHEDULED,
                appointment_type=AppointmentType.SCHEDULED
            )
            db_session.add(appointment)
            db_session.commit()
            db_session.refresh(appointment)
            
            payload = {
                "appointment_id": appointment.id,
                "consultation_notes": f"Consultation {i+1}",
                "diagnosis": f"Diagnosis {i+1}"
            }
            
            response = client.post(
                "/api/v1/medical-records/consultation-notes",
                json=payload,
                headers=headers
            )
            assert response.status_code == 201
            records.append(response.json())
        
        # Verify chain integrity
        audit_entries = db_session.query(AuditChain).order_by(AuditChain.id).all()
        assert len(audit_entries) == 3
        
        # First entry should have previous_hash = "0"
        assert audit_entries[0].previous_hash == "0"
        
        # Each subsequent entry should link to the previous one
        for i in range(1, len(audit_entries)):
            assert audit_entries[i].previous_hash == audit_entries[i-1].hash
    
    def test_transaction_rollback_on_audit_failure(self, client, db_session: Session, test_users, test_appointment, monkeypatch):
        """Test that if audit entry creation fails, the entire transaction is rolled back"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Count records before
        records_before = db_session.query(MedicalRecord).count()
        audit_before = db_session.query(AuditChain).count()
        
        # Mock the create_audit_entry to raise an exception
        # We need to patch it in the medical_records module where it's imported
        from app.api.v1.endpoints import medical_records
        
        original_create_audit_entry = medical_records.create_audit_entry
        
        def mock_create_audit_entry(*args, **kwargs):
            raise Exception("Simulated audit failure")
        
        monkeypatch.setattr(medical_records, "create_audit_entry", mock_create_audit_entry)
        
        payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "This should fail",
            "diagnosis": "Test"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        
        # Request should fail
        assert response.status_code == 500
        
        # Verify no records were created (transaction rolled back)
        records_after = db_session.query(MedicalRecord).count()
        audit_after = db_session.query(AuditChain).count()
        
        assert records_after == records_before
        assert audit_after == audit_before
        
        # Restore original function
        monkeypatch.setattr(medical_records, "create_audit_entry", original_create_audit_entry)
    
    def test_audit_entry_contains_all_required_fields(self, client, db_session: Session, test_users, test_appointment):
        """Test that audit entries contain all required fields"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Complete record",
            "diagnosis": "Test diagnosis"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 201
        record = response.json()
        
        # Verify audit entry has all required fields
        audit_entry = db_session.query(AuditChain).filter(
            AuditChain.record_id == record["id"]
        ).first()
        
        assert audit_entry is not None
        assert audit_entry.record_id == record["id"]
        assert audit_entry.record_type == "medical_record"
        assert audit_entry.record_data is not None
        assert audit_entry.hash is not None
        assert audit_entry.previous_hash is not None
        assert audit_entry.timestamp is not None
        assert audit_entry.user_id == doctor_user.id
        assert audit_entry.is_tampered is False
        
        # Verify record_data contains all medical record fields
        assert "consultation_notes" in audit_entry.record_data
        assert "diagnosis" in audit_entry.record_data
        assert "prescription" in audit_entry.record_data
        assert "patient_id" in audit_entry.record_data
        assert "doctor_id" in audit_entry.record_data
        assert "version_number" in audit_entry.record_data
