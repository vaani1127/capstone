"""
Tests for medical records endpoints
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
    
    # Create another doctor user
    doctor2_user = User(
        name="Dr. Jones",
        email="doctor2@test.com",
        password_hash=get_password_hash("password123"),
        role=UserRole.DOCTOR
    )
    db_session.add(doctor2_user)
    db_session.flush()
    
    doctor2 = Doctor(
        user_id=doctor2_user.id,
        specialization="Cardiology",
        license_number="DOC456",
        average_consultation_duration=20
    )
    db_session.add(doctor2)
    users['doctor2'] = {'user': doctor2_user, 'doctor': doctor2}
    
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
    
    # Create nurse user
    nurse_user = User(
        name="Nurse Jane",
        email="nurse@test.com",
        password_hash=get_password_hash("password123"),
        role=UserRole.NURSE
    )
    db_session.add(nurse_user)
    users['nurse'] = {'user': nurse_user}
    
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


class TestConsultationNoteCreation:
    """Tests for consultation note creation endpoint"""
    
    def test_create_consultation_note_success(self, client, db_session: Session, test_users, test_appointment):
        """Test successful consultation note creation"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Patient presented with fever and cough. Prescribed antibiotics.",
            "diagnosis": "Upper respiratory tract infection"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["appointment_id"] == test_appointment.id
        assert data["consultation_notes"] == payload["consultation_notes"]
        assert data["diagnosis"] == payload["diagnosis"]
        assert data["version_number"] == 1
        assert data["parent_record_id"] is None
        assert data["patient_id"] == test_appointment.patient_id
        assert data["doctor_id"] == test_users['doctor']['doctor'].id
        
        # Verify record in database
        record = db_session.query(MedicalRecord).filter(MedicalRecord.id == data["id"]).first()
        assert record is not None
        assert record.version_number == 1
    
    def test_create_consultation_note_without_diagnosis(self, client, db_session: Session, test_users, test_appointment):
        """Test consultation note creation without diagnosis (optional field)"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Routine checkup. Patient is healthy."
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["consultation_notes"] == payload["consultation_notes"]
        assert data["diagnosis"] is None
    
    def test_create_consultation_note_unauthorized_doctor(self, client, db_session: Session, test_users, test_appointment):
        """Test that a doctor cannot create notes for another doctor's appointment"""
        # Use doctor2 who is not assigned to the appointment
        doctor2_user = test_users['doctor2']['user']
        headers = get_auth_header(doctor2_user)
        
        payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Trying to create note for another doctor's appointment"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 403
        assert "not authorized" in response.json()["detail"].lower()
    
    def test_create_consultation_note_non_doctor_role(self, client, db_session: Session, test_users, test_appointment):
        """Test that non-doctor roles cannot create consultation notes"""
        # Try with patient
        patient_user = test_users['patient']['user']
        headers = get_auth_header(patient_user)
        
        payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Patient trying to create note"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 403
        assert "doctor" in response.json()["detail"].lower()
        
        # Try with nurse
        nurse_user = test_users['nurse']['user']
        headers = get_auth_header(nurse_user)
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 403
    
    def test_create_consultation_note_invalid_appointment(self, client, db_session: Session, test_users):
        """Test consultation note creation with non-existent appointment"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        payload = {
            "appointment_id": 99999,  # Non-existent appointment
            "consultation_notes": "Test note"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 404
        assert "appointment not found" in response.json()["detail"].lower()
    
    def test_create_consultation_note_duplicate(self, client, db_session: Session, test_users, test_appointment):
        """Test that duplicate consultation notes for same appointment are rejected"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "First consultation note"
        }
        
        # Create first note
        response1 = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        assert response1.status_code == 201
        
        # Try to create second note for same appointment
        payload["consultation_notes"] = "Second consultation note"
        response2 = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()
    
    def test_create_consultation_note_missing_required_fields(self, client, db_session: Session, test_users):
        """Test validation of required fields"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Missing consultation_notes
        payload = {
            "appointment_id": 1
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 422  # Validation error
        
        # Missing appointment_id
        payload = {
            "consultation_notes": "Test note"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 422
    
    def test_create_consultation_note_empty_notes(self, client, db_session: Session, test_users, test_appointment):
        """Test that empty consultation notes are rejected"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": ""  # Empty string
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_create_consultation_note_without_authentication(self, client, test_appointment):
        """Test that unauthenticated requests are rejected"""
        payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Test note"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload
        )
        
        assert response.status_code == 401  # No authorization header
    
    def test_create_consultation_note_invalid_token(self, client, test_appointment):
        """Test that invalid tokens are rejected"""
        headers = {"Authorization": "Bearer invalid_token"}
        
        payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Test note"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 401



class TestConsultationNoteUpdate:
    """Tests for consultation note update endpoint"""
    
    def test_update_consultation_note_success(self, client, db_session: Session, test_users, test_appointment):
        """Test successful consultation note update"""
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
        
        # Update the consultation note
        update_payload = {
            "consultation_notes": "Updated notes with more details",
            "diagnosis": "Updated diagnosis after further examination"
        }
        
        response = client.put(
            f"/api/v1/medical-records/consultation-notes/{original_record['id']}",
            json=update_payload,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify new version created
        assert data["id"] != original_record["id"]  # New record ID
        assert data["version_number"] == 2
        assert data["parent_record_id"] == original_record["id"]
        assert data["consultation_notes"] == update_payload["consultation_notes"]
        assert data["diagnosis"] == update_payload["diagnosis"]
        
        # Verify patient, doctor, appointment IDs are preserved
        assert data["patient_id"] == original_record["patient_id"]
        assert data["doctor_id"] == original_record["doctor_id"]
        assert data["appointment_id"] == original_record["appointment_id"]
        
        # Verify original record still exists in database
        original_in_db = db_session.query(MedicalRecord).filter(
            MedicalRecord.id == original_record["id"]
        ).first()
        assert original_in_db is not None
        assert original_in_db.version_number == 1
        assert original_in_db.consultation_notes == create_payload["consultation_notes"]
    
    def test_update_consultation_note_partial_update(self, client, db_session: Session, test_users, test_appointment):
        """Test updating only consultation notes, preserving diagnosis"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Create initial consultation note
        create_payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Initial notes",
            "diagnosis": "Original diagnosis"
        }
        
        create_response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=create_payload,
            headers=headers
        )
        assert create_response.status_code == 201
        original_record = create_response.json()
        
        # Update only consultation notes
        update_payload = {
            "consultation_notes": "Updated notes only"
        }
        
        response = client.put(
            f"/api/v1/medical-records/consultation-notes/{original_record['id']}",
            json=update_payload,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify only notes updated, diagnosis preserved
        assert data["consultation_notes"] == update_payload["consultation_notes"]
        assert data["diagnosis"] == create_payload["diagnosis"]  # Preserved
        assert data["version_number"] == 2
    
    def test_update_consultation_note_unauthorized_doctor(self, client, db_session: Session, test_users, test_appointment):
        """Test that a doctor cannot update another doctor's consultation note"""
        # Create note with doctor1
        doctor1_user = test_users['doctor']['user']
        headers1 = get_auth_header(doctor1_user)
        
        create_payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Doctor 1's notes"
        }
        
        create_response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=create_payload,
            headers=headers1
        )
        assert create_response.status_code == 201
        record = create_response.json()
        
        # Try to update with doctor2
        doctor2_user = test_users['doctor2']['user']
        headers2 = get_auth_header(doctor2_user)
        
        update_payload = {
            "consultation_notes": "Doctor 2 trying to update"
        }
        
        response = client.put(
            f"/api/v1/medical-records/consultation-notes/{record['id']}",
            json=update_payload,
            headers=headers2
        )
        
        assert response.status_code == 403
        assert "not authorized" in response.json()["detail"].lower()
    
    def test_update_consultation_note_non_doctor_role(self, client, db_session: Session, test_users, test_appointment):
        """Test that non-doctor roles cannot update consultation notes"""
        # Create note with doctor
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        create_payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Doctor's notes"
        }
        
        create_response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=create_payload,
            headers=headers
        )
        assert create_response.status_code == 201
        record = create_response.json()
        
        # Try to update with patient
        patient_user = test_users['patient']['user']
        patient_headers = get_auth_header(patient_user)
        
        update_payload = {
            "consultation_notes": "Patient trying to update"
        }
        
        response = client.put(
            f"/api/v1/medical-records/consultation-notes/{record['id']}",
            json=update_payload,
            headers=patient_headers
        )
        
        assert response.status_code == 403
        assert "doctor" in response.json()["detail"].lower()
    
    def test_update_consultation_note_nonexistent_record(self, client, db_session: Session, test_users):
        """Test updating a non-existent record"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        update_payload = {
            "consultation_notes": "Trying to update non-existent record"
        }
        
        response = client.put(
            "/api/v1/medical-records/consultation-notes/99999",
            json=update_payload,
            headers=headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_consultation_note_no_fields_provided(self, client, db_session: Session, test_users, test_appointment):
        """Test that update with no fields is rejected"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Create initial consultation note
        create_payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Initial notes"
        }
        
        create_response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=create_payload,
            headers=headers
        )
        assert create_response.status_code == 201
        record = create_response.json()
        
        # Try to update with empty payload
        update_payload = {}
        
        response = client.put(
            f"/api/v1/medical-records/consultation-notes/{record['id']}",
            json=update_payload,
            headers=headers
        )
        
        assert response.status_code == 400
        assert "at least one field" in response.json()["detail"].lower()
    
    def test_update_consultation_note_multiple_versions(self, client, db_session: Session, test_users, test_appointment):
        """Test creating multiple versions of a consultation note"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Create initial consultation note
        create_payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Version 1"
        }
        
        create_response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=create_payload,
            headers=headers
        )
        assert create_response.status_code == 201
        v1 = create_response.json()
        
        # Create version 2
        update_payload = {
            "consultation_notes": "Version 2"
        }
        
        response2 = client.put(
            f"/api/v1/medical-records/consultation-notes/{v1['id']}",
            json=update_payload,
            headers=headers
        )
        assert response2.status_code == 200
        v2 = response2.json()
        assert v2["version_number"] == 2
        assert v2["parent_record_id"] == v1["id"]
        
        # Create version 3 (updating v2, not v1)
        update_payload = {
            "consultation_notes": "Version 3"
        }
        
        response3 = client.put(
            f"/api/v1/medical-records/consultation-notes/{v2['id']}",
            json=update_payload,
            headers=headers
        )
        assert response3.status_code == 200
        v3 = response3.json()
        assert v3["version_number"] == 3
        assert v3["parent_record_id"] == v2["id"]
        
        # Verify all versions exist in database
        all_versions = db_session.query(MedicalRecord).filter(
            MedicalRecord.appointment_id == test_appointment.id
        ).order_by(MedicalRecord.version_number).all()
        
        assert len(all_versions) == 3
        assert all_versions[0].version_number == 1
        assert all_versions[1].version_number == 2
        assert all_versions[2].version_number == 3
    
    def test_update_consultation_note_preserves_prescription(self, client, db_session: Session, test_users, test_appointment):
        """Test that updating notes preserves prescription field"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Create initial consultation note with prescription
        create_payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Initial notes",
            "diagnosis": "Flu"
        }
        
        create_response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=create_payload,
            headers=headers
        )
        assert create_response.status_code == 201
        record = create_response.json()
        
        # Manually add prescription to the record (simulating prescription creation)
        db_record = db_session.query(MedicalRecord).filter(
            MedicalRecord.id == record["id"]
        ).first()
        db_record.prescription = "Paracetamol 500mg, twice daily"
        db_session.commit()
        
        # Update consultation notes
        update_payload = {
            "consultation_notes": "Updated notes"
        }
        
        response = client.put(
            f"/api/v1/medical-records/consultation-notes/{record['id']}",
            json=update_payload,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify prescription is preserved
        assert data["prescription"] == "Paracetamol 500mg, twice daily"
        assert data["consultation_notes"] == update_payload["consultation_notes"]
    
    def test_update_consultation_note_without_authentication(self, client, db_session: Session, test_users, test_appointment):
        """Test that unauthenticated requests are rejected"""
        # Create a record first
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        create_payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Initial notes"
        }
        
        create_response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=create_payload,
            headers=headers
        )
        assert create_response.status_code == 201
        record = create_response.json()
        
        # Try to update without authentication
        update_payload = {
            "consultation_notes": "Trying to update without auth"
        }
        
        response = client.put(
            f"/api/v1/medical-records/consultation-notes/{record['id']}",
            json=update_payload
        )
        
        assert response.status_code == 401
    
    def test_update_consultation_note_empty_string_validation(self, client, db_session: Session, test_users, test_appointment):
        """Test that empty strings are rejected for consultation notes"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Create initial consultation note
        create_payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Initial notes"
        }
        
        create_response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=create_payload,
            headers=headers
        )
        assert create_response.status_code == 201
        record = create_response.json()
        
        # Try to update with empty string
        update_payload = {
            "consultation_notes": ""
        }
        
        response = client.put(
            f"/api/v1/medical-records/consultation-notes/{record['id']}",
            json=update_payload,
            headers=headers
        )
        
        assert response.status_code == 422  # Validation error



class TestPrescriptionCreation:
    """Tests for prescription creation endpoint"""
    
    def test_create_prescription_success(self, client, db_session: Session, test_users, test_appointment):
        """Test successful prescription creation"""
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
        data = response.json()
        assert data["appointment_id"] == test_appointment.id
        assert data["prescription"] is not None
        assert "Amoxicillin" in data["prescription"]
        assert "500mg" in data["prescription"]
        assert "Three times daily" in data["prescription"]
        assert "7 days" in data["prescription"]
        assert data["version_number"] == 1
        assert data["parent_record_id"] is None
        assert data["patient_id"] == test_appointment.patient_id
        assert data["doctor_id"] == test_users['doctor']['doctor'].id
        
        # Verify record in database
        record = db_session.query(MedicalRecord).filter(MedicalRecord.id == data["id"]).first()
        assert record is not None
        assert record.version_number == 1
        assert record.prescription is not None
    
    def test_create_prescription_unauthorized_doctor(self, client, db_session: Session, test_users, test_appointment):
        """Test that a doctor cannot create prescriptions for another doctor's appointment"""
        # Use doctor2 who is not assigned to the appointment
        doctor2_user = test_users['doctor2']['user']
        headers = get_auth_header(doctor2_user)
        
        payload = {
            "appointment_id": test_appointment.id,
            "medication": "Paracetamol",
            "dosage": "500mg",
            "frequency": "Twice daily",
            "duration": "3 days"
        }
        
        response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 403
        assert "not authorized" in response.json()["detail"].lower()
    
    def test_create_prescription_non_doctor_role(self, client, db_session: Session, test_users, test_appointment):
        """Test that non-doctor roles cannot create prescriptions"""
        # Try with patient
        patient_user = test_users['patient']['user']
        headers = get_auth_header(patient_user)
        
        payload = {
            "appointment_id": test_appointment.id,
            "medication": "Aspirin",
            "dosage": "100mg",
            "frequency": "Once daily",
            "duration": "30 days"
        }
        
        response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 403
        assert "doctor" in response.json()["detail"].lower()
        
        # Try with nurse
        nurse_user = test_users['nurse']['user']
        headers = get_auth_header(nurse_user)
        
        response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 403
    
    def test_create_prescription_invalid_appointment(self, client, db_session: Session, test_users):
        """Test prescription creation with non-existent appointment"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        payload = {
            "appointment_id": 99999,  # Non-existent appointment
            "medication": "Ibuprofen",
            "dosage": "400mg",
            "frequency": "As needed",
            "duration": "5 days"
        }
        
        response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 404
        assert "appointment not found" in response.json()["detail"].lower()
    
    def test_create_prescription_duplicate(self, client, db_session: Session, test_users, test_appointment):
        """Test that duplicate prescriptions for same appointment are rejected"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        payload = {
            "appointment_id": test_appointment.id,
            "medication": "Metformin",
            "dosage": "500mg",
            "frequency": "Twice daily",
            "duration": "30 days"
        }
        
        # Create first prescription
        response1 = client.post(
            "/api/v1/medical-records/prescriptions",
            json=payload,
            headers=headers
        )
        assert response1.status_code == 201
        
        # Try to create second prescription for same appointment
        payload["medication"] = "Insulin"
        response2 = client.post(
            "/api/v1/medical-records/prescriptions",
            json=payload,
            headers=headers
        )
        
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()
    
    def test_create_prescription_missing_required_fields(self, client, db_session: Session, test_users):
        """Test validation of required fields"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Missing medication
        payload = {
            "appointment_id": 1,
            "dosage": "500mg",
            "frequency": "Twice daily",
            "duration": "7 days"
        }
        
        response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 422  # Validation error
        
        # Missing dosage
        payload = {
            "appointment_id": 1,
            "medication": "Amoxicillin",
            "frequency": "Twice daily",
            "duration": "7 days"
        }
        
        response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 422
        
        # Missing frequency
        payload = {
            "appointment_id": 1,
            "medication": "Amoxicillin",
            "dosage": "500mg",
            "duration": "7 days"
        }
        
        response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 422
        
        # Missing duration
        payload = {
            "appointment_id": 1,
            "medication": "Amoxicillin",
            "dosage": "500mg",
            "frequency": "Twice daily"
        }
        
        response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 422
    
    def test_create_prescription_empty_fields(self, client, db_session: Session, test_users, test_appointment):
        """Test that empty strings are rejected for required fields"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Empty medication
        payload = {
            "appointment_id": test_appointment.id,
            "medication": "",
            "dosage": "500mg",
            "frequency": "Twice daily",
            "duration": "7 days"
        }
        
        response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_create_prescription_without_authentication(self, client, test_appointment):
        """Test that unauthenticated requests are rejected"""
        payload = {
            "appointment_id": test_appointment.id,
            "medication": "Aspirin",
            "dosage": "100mg",
            "frequency": "Once daily",
            "duration": "30 days"
        }
        
        response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=payload
        )
        
        assert response.status_code == 401  # No authorization header
    
    def test_create_prescription_invalid_token(self, client, test_appointment):
        """Test that invalid tokens are rejected"""
        headers = {"Authorization": "Bearer invalid_token"}
        
        payload = {
            "appointment_id": test_appointment.id,
            "medication": "Aspirin",
            "dosage": "100mg",
            "frequency": "Once daily",
            "duration": "30 days"
        }
        
        response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 401
    
    def test_create_prescription_with_special_characters(self, client, db_session: Session, test_users, test_appointment):
        """Test prescription creation with special characters in fields"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        payload = {
            "appointment_id": test_appointment.id,
            "medication": "Co-amoxiclav (Augmentin)",
            "dosage": "875mg/125mg",
            "frequency": "Twice daily (morning & evening)",
            "duration": "10-14 days"
        }
        
        response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "Co-amoxiclav" in data["prescription"]
        assert "875mg/125mg" in data["prescription"]
    
    def test_create_prescription_links_to_appointment(self, client, db_session: Session, test_users, test_appointment):
        """Test that prescription is correctly linked to appointment"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        payload = {
            "appointment_id": test_appointment.id,
            "medication": "Lisinopril",
            "dosage": "10mg",
            "frequency": "Once daily",
            "duration": "Ongoing"
        }
        
        response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify appointment link
        assert data["appointment_id"] == test_appointment.id
        
        # Verify patient and doctor IDs match appointment
        assert data["patient_id"] == test_appointment.patient_id
        assert data["doctor_id"] == test_appointment.doctor_id
        
        # Verify in database
        record = db_session.query(MedicalRecord).filter(MedicalRecord.id == data["id"]).first()
        assert record.appointment_id == test_appointment.id
        assert record.patient_id == test_appointment.patient_id
        assert record.doctor_id == test_appointment.doctor_id
    
    def test_create_prescription_sets_version_number(self, client, db_session: Session, test_users, test_appointment):
        """Test that initial prescription has version_number=1"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        payload = {
            "appointment_id": test_appointment.id,
            "medication": "Atorvastatin",
            "dosage": "20mg",
            "frequency": "Once daily at bedtime",
            "duration": "Ongoing"
        }
        
        response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify version number
        assert data["version_number"] == 1
        assert data["parent_record_id"] is None
        
        # Verify created_by is set
        assert data["created_by"] == doctor_user.id



class TestPrescriptionUpdate:
    """Tests for prescription update endpoint"""
    
    def test_update_prescription_success(self, client, db_session: Session, test_users, test_appointment):
        """Test successful prescription update"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Create initial prescription
        create_payload = {
            "appointment_id": test_appointment.id,
            "medication": "Amoxicillin",
            "dosage": "500mg",
            "frequency": "Three times daily",
            "duration": "7 days"
        }
        
        create_response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=create_payload,
            headers=headers
        )
        assert create_response.status_code == 201
        original_record = create_response.json()
        
        # Update the prescription
        update_payload = {
            "medication": "Amoxicillin",
            "dosage": "875mg",
            "frequency": "Twice daily",
            "duration": "10 days"
        }
        
        response = client.put(
            f"/api/v1/medical-records/prescriptions/{original_record['id']}",
            json=update_payload,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify new version created
        assert data["id"] != original_record["id"]  # New record ID
        assert data["version_number"] == 2
        assert data["parent_record_id"] == original_record["id"]
        
        # Verify prescription updated
        assert "875mg" in data["prescription"]
        assert "Twice daily" in data["prescription"]
        assert "10 days" in data["prescription"]
        
        # Verify patient, doctor, appointment IDs are preserved
        assert data["patient_id"] == original_record["patient_id"]
        assert data["doctor_id"] == original_record["doctor_id"]
        assert data["appointment_id"] == original_record["appointment_id"]
        
        # Verify original record still exists in database
        original_in_db = db_session.query(MedicalRecord).filter(
            MedicalRecord.id == original_record["id"]
        ).first()
        assert original_in_db is not None
        assert original_in_db.version_number == 1
        assert "500mg" in original_in_db.prescription
        assert "Three times daily" in original_in_db.prescription
    
    def test_update_prescription_change_medication(self, client, db_session: Session, test_users, test_appointment):
        """Test updating prescription with different medication"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Create initial prescription
        create_payload = {
            "appointment_id": test_appointment.id,
            "medication": "Ibuprofen",
            "dosage": "400mg",
            "frequency": "As needed",
            "duration": "5 days"
        }
        
        create_response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=create_payload,
            headers=headers
        )
        assert create_response.status_code == 201
        original_record = create_response.json()
        
        # Update with different medication
        update_payload = {
            "medication": "Naproxen",
            "dosage": "500mg",
            "frequency": "Twice daily",
            "duration": "7 days"
        }
        
        response = client.put(
            f"/api/v1/medical-records/prescriptions/{original_record['id']}",
            json=update_payload,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify medication changed
        assert "Naproxen" in data["prescription"]
        assert "500mg" in data["prescription"]
        assert data["version_number"] == 2
    
    def test_update_prescription_unauthorized_doctor(self, client, db_session: Session, test_users, test_appointment):
        """Test that a doctor cannot update another doctor's prescription"""
        # Create prescription with doctor1
        doctor1_user = test_users['doctor']['user']
        headers1 = get_auth_header(doctor1_user)
        
        create_payload = {
            "appointment_id": test_appointment.id,
            "medication": "Metformin",
            "dosage": "500mg",
            "frequency": "Twice daily",
            "duration": "30 days"
        }
        
        create_response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=create_payload,
            headers=headers1
        )
        assert create_response.status_code == 201
        record = create_response.json()
        
        # Try to update with doctor2
        doctor2_user = test_users['doctor2']['user']
        headers2 = get_auth_header(doctor2_user)
        
        update_payload = {
            "medication": "Metformin",
            "dosage": "1000mg",
            "frequency": "Twice daily",
            "duration": "30 days"
        }
        
        response = client.put(
            f"/api/v1/medical-records/prescriptions/{record['id']}",
            json=update_payload,
            headers=headers2
        )
        
        assert response.status_code == 403
        assert "not authorized" in response.json()["detail"].lower()
    
    def test_update_prescription_non_doctor_role(self, client, db_session: Session, test_users, test_appointment):
        """Test that non-doctor roles cannot update prescriptions"""
        # Create prescription with doctor
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        create_payload = {
            "appointment_id": test_appointment.id,
            "medication": "Lisinopril",
            "dosage": "10mg",
            "frequency": "Once daily",
            "duration": "Ongoing"
        }
        
        create_response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=create_payload,
            headers=headers
        )
        assert create_response.status_code == 201
        record = create_response.json()
        
        # Try to update with patient
        patient_user = test_users['patient']['user']
        patient_headers = get_auth_header(patient_user)
        
        update_payload = {
            "medication": "Lisinopril",
            "dosage": "20mg",
            "frequency": "Once daily",
            "duration": "Ongoing"
        }
        
        response = client.put(
            f"/api/v1/medical-records/prescriptions/{record['id']}",
            json=update_payload,
            headers=patient_headers
        )
        
        assert response.status_code == 403
        assert "doctor" in response.json()["detail"].lower()
    
    def test_update_prescription_nonexistent_record(self, client, db_session: Session, test_users):
        """Test updating a non-existent prescription"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        update_payload = {
            "medication": "Aspirin",
            "dosage": "100mg",
            "frequency": "Once daily",
            "duration": "30 days"
        }
        
        response = client.put(
            "/api/v1/medical-records/prescriptions/99999",
            json=update_payload,
            headers=headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_prescription_missing_required_fields(self, client, db_session: Session, test_users, test_appointment):
        """Test that all required fields must be provided"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Create initial prescription
        create_payload = {
            "appointment_id": test_appointment.id,
            "medication": "Atorvastatin",
            "dosage": "20mg",
            "frequency": "Once daily",
            "duration": "Ongoing"
        }
        
        create_response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=create_payload,
            headers=headers
        )
        assert create_response.status_code == 201
        record = create_response.json()
        
        # Try to update with missing medication
        update_payload = {
            "dosage": "40mg",
            "frequency": "Once daily",
            "duration": "Ongoing"
        }
        
        response = client.put(
            f"/api/v1/medical-records/prescriptions/{record['id']}",
            json=update_payload,
            headers=headers
        )
        
        assert response.status_code == 422  # Validation error
        
        # Try to update with missing dosage
        update_payload = {
            "medication": "Atorvastatin",
            "frequency": "Once daily",
            "duration": "Ongoing"
        }
        
        response = client.put(
            f"/api/v1/medical-records/prescriptions/{record['id']}",
            json=update_payload,
            headers=headers
        )
        
        assert response.status_code == 422
    
    def test_update_prescription_empty_fields(self, client, db_session: Session, test_users, test_appointment):
        """Test that empty strings are rejected"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Create initial prescription
        create_payload = {
            "appointment_id": test_appointment.id,
            "medication": "Metoprolol",
            "dosage": "50mg",
            "frequency": "Twice daily",
            "duration": "Ongoing"
        }
        
        create_response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=create_payload,
            headers=headers
        )
        assert create_response.status_code == 201
        record = create_response.json()
        
        # Try to update with empty medication
        update_payload = {
            "medication": "",
            "dosage": "100mg",
            "frequency": "Twice daily",
            "duration": "Ongoing"
        }
        
        response = client.put(
            f"/api/v1/medical-records/prescriptions/{record['id']}",
            json=update_payload,
            headers=headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_update_prescription_multiple_versions(self, client, db_session: Session, test_users, test_appointment):
        """Test creating multiple versions of a prescription"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Create initial prescription
        create_payload = {
            "appointment_id": test_appointment.id,
            "medication": "Insulin",
            "dosage": "10 units",
            "frequency": "Before meals",
            "duration": "Ongoing"
        }
        
        create_response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=create_payload,
            headers=headers
        )
        assert create_response.status_code == 201
        v1 = create_response.json()
        
        # Create version 2
        update_payload = {
            "medication": "Insulin",
            "dosage": "15 units",
            "frequency": "Before meals",
            "duration": "Ongoing"
        }
        
        response2 = client.put(
            f"/api/v1/medical-records/prescriptions/{v1['id']}",
            json=update_payload,
            headers=headers
        )
        assert response2.status_code == 200
        v2 = response2.json()
        assert v2["version_number"] == 2
        assert v2["parent_record_id"] == v1["id"]
        assert "15 units" in v2["prescription"]
        
        # Create version 3 (updating v2, not v1)
        update_payload = {
            "medication": "Insulin",
            "dosage": "20 units",
            "frequency": "Before meals",
            "duration": "Ongoing"
        }
        
        response3 = client.put(
            f"/api/v1/medical-records/prescriptions/{v2['id']}",
            json=update_payload,
            headers=headers
        )
        assert response3.status_code == 200
        v3 = response3.json()
        assert v3["version_number"] == 3
        assert v3["parent_record_id"] == v2["id"]
        assert "20 units" in v3["prescription"]
        
        # Verify all versions exist in database
        all_versions = db_session.query(MedicalRecord).filter(
            MedicalRecord.appointment_id == test_appointment.id
        ).order_by(MedicalRecord.version_number).all()
        
        assert len(all_versions) == 3
        assert all_versions[0].version_number == 1
        assert all_versions[1].version_number == 2
        assert all_versions[2].version_number == 3
    
    def test_update_prescription_preserves_consultation_notes(self, client, db_session: Session, test_users, test_appointment):
        """Test that updating prescription preserves consultation notes"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Create initial prescription
        create_payload = {
            "appointment_id": test_appointment.id,
            "medication": "Warfarin",
            "dosage": "5mg",
            "frequency": "Once daily",
            "duration": "Ongoing"
        }
        
        create_response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=create_payload,
            headers=headers
        )
        assert create_response.status_code == 201
        record = create_response.json()
        
        # Manually add consultation notes to the record
        db_record = db_session.query(MedicalRecord).filter(
            MedicalRecord.id == record["id"]
        ).first()
        db_record.consultation_notes = "Patient has atrial fibrillation"
        db_record.diagnosis = "Atrial fibrillation"
        db_session.commit()
        
        # Update prescription
        update_payload = {
            "medication": "Warfarin",
            "dosage": "7.5mg",
            "frequency": "Once daily",
            "duration": "Ongoing"
        }
        
        response = client.put(
            f"/api/v1/medical-records/prescriptions/{record['id']}",
            json=update_payload,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify consultation notes and diagnosis are preserved
        assert data["consultation_notes"] == "Patient has atrial fibrillation"
        assert data["diagnosis"] == "Atrial fibrillation"
        assert "7.5mg" in data["prescription"]
    
    def test_update_prescription_without_authentication(self, client, db_session: Session, test_users, test_appointment):
        """Test that unauthenticated requests are rejected"""
        # Create a prescription first
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        create_payload = {
            "appointment_id": test_appointment.id,
            "medication": "Levothyroxine",
            "dosage": "50mcg",
            "frequency": "Once daily",
            "duration": "Ongoing"
        }
        
        create_response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=create_payload,
            headers=headers
        )
        assert create_response.status_code == 201
        record = create_response.json()
        
        # Try to update without authentication
        update_payload = {
            "medication": "Levothyroxine",
            "dosage": "75mcg",
            "frequency": "Once daily",
            "duration": "Ongoing"
        }
        
        response = client.put(
            f"/api/v1/medical-records/prescriptions/{record['id']}",
            json=update_payload
        )
        
        assert response.status_code == 401
    
    def test_update_prescription_invalid_token(self, client, db_session: Session, test_users, test_appointment):
        """Test that invalid tokens are rejected"""
        # Create a prescription first
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        create_payload = {
            "appointment_id": test_appointment.id,
            "medication": "Omeprazole",
            "dosage": "20mg",
            "frequency": "Once daily",
            "duration": "30 days"
        }
        
        create_response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=create_payload,
            headers=headers
        )
        assert create_response.status_code == 201
        record = create_response.json()
        
        # Try to update with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        
        update_payload = {
            "medication": "Omeprazole",
            "dosage": "40mg",
            "frequency": "Once daily",
            "duration": "30 days"
        }
        
        response = client.put(
            f"/api/v1/medical-records/prescriptions/{record['id']}",
            json=update_payload,
            headers=invalid_headers
        )
        
        assert response.status_code == 401
    
    def test_update_prescription_with_special_characters(self, client, db_session: Session, test_users, test_appointment):
        """Test prescription update with special characters"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Create initial prescription
        create_payload = {
            "appointment_id": test_appointment.id,
            "medication": "Amoxicillin",
            "dosage": "500mg",
            "frequency": "Three times daily",
            "duration": "7 days"
        }
        
        create_response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=create_payload,
            headers=headers
        )
        assert create_response.status_code == 201
        record = create_response.json()
        
        # Update with special characters
        update_payload = {
            "medication": "Co-amoxiclav (Augmentin)",
            "dosage": "875mg/125mg",
            "frequency": "Twice daily (morning & evening)",
            "duration": "10-14 days"
        }
        
        response = client.put(
            f"/api/v1/medical-records/prescriptions/{record['id']}",
            json=update_payload,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Co-amoxiclav" in data["prescription"]
        assert "875mg/125mg" in data["prescription"]
        assert "morning & evening" in data["prescription"]
    
    def test_update_prescription_sets_created_by(self, client, db_session: Session, test_users, test_appointment):
        """Test that updated prescription has correct created_by field"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Create initial prescription
        create_payload = {
            "appointment_id": test_appointment.id,
            "medication": "Simvastatin",
            "dosage": "20mg",
            "frequency": "Once daily at bedtime",
            "duration": "Ongoing"
        }
        
        create_response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=create_payload,
            headers=headers
        )
        assert create_response.status_code == 201
        record = create_response.json()
        
        # Update prescription
        update_payload = {
            "medication": "Simvastatin",
            "dosage": "40mg",
            "frequency": "Once daily at bedtime",
            "duration": "Ongoing"
        }
        
        response = client.put(
            f"/api/v1/medical-records/prescriptions/{record['id']}",
            json=update_payload,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify created_by is set to current user
        assert data["created_by"] == doctor_user.id
        
        # Verify in database
        new_record = db_session.query(MedicalRecord).filter(
            MedicalRecord.id == data["id"]
        ).first()
        assert new_record.created_by == doctor_user.id



class TestPatientMedicalHistoryRetrieval:
    """Tests for patient medical history retrieval endpoint"""
    
    def test_patient_view_own_records_success(self, client, db_session: Session, test_users, test_appointment):
        """Test that a patient can view their own medical records"""
        # Create some medical records for the patient
        doctor_user = test_users['doctor']['user']
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        
        # Create consultation note
        record1 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="Patient has fever and cough",
            diagnosis="Upper respiratory infection",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record1)
        
        # Create prescription
        record2 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=None,
            prescription="Amoxicillin 500mg, three times daily, 7 days",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record2)
        db_session.commit()
        
        # Patient requests their own records
        patient_user = test_users['patient']['user']
        headers = get_auth_header(patient_user)
        
        response = client.get(
            f"/api/v1/medical-records/patient/{patient.id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Verify records are sorted by date (newest first)
        assert data[0]["created_at"] >= data[1]["created_at"]
        
        # Verify patient and doctor names are included
        assert data[0]["patient_name"] == patient_user.name
        assert data[0]["doctor_name"] == doctor_user.name
    
    def test_patient_cannot_view_other_patient_records(self, client, db_session: Session, test_users):
        """Test that a patient cannot view another patient's records"""
        # Create another patient
        other_patient_user = User(
            name="Jane Doe",
            email="other_patient@test.com",
            password_hash=get_password_hash("password123"),
            role=UserRole.PATIENT
        )
        db_session.add(other_patient_user)
        db_session.flush()
        
        other_patient = Patient(
            user_id=other_patient_user.id,
            date_of_birth=datetime(1985, 5, 15),
            gender="Female",
            phone="9876543210"
        )
        db_session.add(other_patient)
        db_session.commit()
        db_session.refresh(other_patient)
        
        # Try to access other patient's records
        patient_user = test_users['patient']['user']
        headers = get_auth_header(patient_user)
        
        response = client.get(
            f"/api/v1/medical-records/patient/{other_patient.id}",
            headers=headers
        )
        
        assert response.status_code == 403
        assert "your own" in response.json()["detail"].lower()
    
    def test_doctor_view_treated_patient_records(self, client, db_session: Session, test_users, test_appointment):
        """Test that a doctor can view records of patients they have treated"""
        doctor_user = test_users['doctor']['user']
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        
        # Create medical record (doctor has treated this patient)
        record = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="Follow-up consultation",
            diagnosis="Recovering well",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record)
        db_session.commit()
        
        # Doctor requests patient's records
        headers = get_auth_header(doctor_user)
        
        response = client.get(
            f"/api/v1/medical-records/patient/{patient.id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["patient_id"] == patient.id
    
    def test_doctor_cannot_view_untreated_patient_records(self, client, db_session: Session, test_users):
        """Test that a doctor cannot view records of patients they have not treated"""
        # Create another patient
        other_patient_user = User(
            name="Bob Smith",
            email="bob@test.com",
            password_hash=get_password_hash("password123"),
            role=UserRole.PATIENT
        )
        db_session.add(other_patient_user)
        db_session.flush()
        
        other_patient = Patient(
            user_id=other_patient_user.id,
            date_of_birth=datetime(1980, 3, 20),
            gender="Male",
            phone="5555555555"
        )
        db_session.add(other_patient)
        db_session.commit()
        db_session.refresh(other_patient)
        
        # Doctor tries to access records of patient they haven't treated
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        response = client.get(
            f"/api/v1/medical-records/patient/{other_patient.id}",
            headers=headers
        )
        
        assert response.status_code == 403
        assert "treated" in response.json()["detail"].lower()
    
    def test_admin_view_any_patient_records(self, client, db_session: Session, test_users, test_appointment):
        """Test that an admin can view any patient's records"""
        # Create admin user
        admin_user = User(
            name="Admin User",
            email="admin@test.com",
            password_hash=get_password_hash("password123"),
            role=UserRole.ADMIN
        )
        db_session.add(admin_user)
        db_session.commit()
        db_session.refresh(admin_user)
        
        # Create medical record for patient
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        
        record = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="Admin viewing this",
            version_number=1,
            created_by=test_users['doctor']['user'].id
        )
        db_session.add(record)
        db_session.commit()
        
        # Admin requests patient's records
        headers = get_auth_header(admin_user)
        
        response = client.get(
            f"/api/v1/medical-records/patient/{patient.id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    def test_nurse_cannot_view_medical_records(self, client, db_session: Session, test_users):
        """Test that nurses cannot view medical records"""
        nurse_user = test_users['nurse']['user']
        patient = test_users['patient']['patient']
        
        headers = get_auth_header(nurse_user)
        
        response = client.get(
            f"/api/v1/medical-records/patient/{patient.id}",
            headers=headers
        )
        
        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()
    
    def test_records_sorted_by_date_newest_first(self, client, db_session: Session, test_users):
        """Test that records are sorted by created_at date (newest first)"""
        doctor_user = test_users['doctor']['user']
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        
        # Create multiple records with different timestamps
        from datetime import timedelta
        
        record1 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            consultation_notes="First visit",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record1)
        db_session.flush()
        
        # Manually set created_at to simulate different times
        record1.created_at = datetime.now() - timedelta(days=3)
        
        record2 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            consultation_notes="Second visit",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record2)
        db_session.flush()
        
        record2.created_at = datetime.now() - timedelta(days=1)
        
        record3 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            consultation_notes="Third visit",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record3)
        db_session.flush()
        
        record3.created_at = datetime.now()
        
        db_session.commit()
        
        # Patient requests their records
        patient_user = test_users['patient']['user']
        headers = get_auth_header(patient_user)
        
        response = client.get(
            f"/api/v1/medical-records/patient/{patient.id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        # Verify sorting (newest first)
        assert "Third visit" in data[0]["consultation_notes"]
        assert "Second visit" in data[1]["consultation_notes"]
        assert "First visit" in data[2]["consultation_notes"]
    
    def test_only_latest_version_returned(self, client, db_session: Session, test_users, test_appointment):
        """Test that only the latest version of each record is returned"""
        doctor_user = test_users['doctor']['user']
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        
        # Create original record
        record_v1 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="Version 1",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record_v1)
        db_session.commit()
        db_session.refresh(record_v1)
        
        # Create version 2
        record_v2 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="Version 2",
            version_number=2,
            parent_record_id=record_v1.id,
            created_by=doctor_user.id
        )
        db_session.add(record_v2)
        db_session.commit()
        
        # Create version 3
        record_v3 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="Version 3",
            version_number=3,
            parent_record_id=record_v2.id,
            created_by=doctor_user.id
        )
        db_session.add(record_v3)
        db_session.commit()
        
        # Patient requests their records
        patient_user = test_users['patient']['user']
        headers = get_auth_header(patient_user)
        
        response = client.get(
            f"/api/v1/medical-records/patient/{patient.id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only return 1 record (latest version)
        assert len(data) == 1
        assert data[0]["version_number"] == 3
        assert "Version 3" in data[0]["consultation_notes"]
    
    def test_multiple_appointments_latest_versions(self, client, db_session: Session, test_users):
        """Test that latest versions are returned for multiple appointments"""
        doctor_user = test_users['doctor']['user']
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        
        # Create two appointments
        appointment1 = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=datetime.now() + timedelta(hours=1),
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED
        )
        db_session.add(appointment1)
        
        appointment2 = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=datetime.now() + timedelta(hours=2),
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED
        )
        db_session.add(appointment2)
        db_session.commit()
        db_session.refresh(appointment1)
        db_session.refresh(appointment2)
        
        # Create records for appointment 1 (v1 and v2)
        record1_v1 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=appointment1.id,
            consultation_notes="Appointment 1 - Version 1",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record1_v1)
        db_session.commit()
        db_session.refresh(record1_v1)
        
        record1_v2 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=appointment1.id,
            consultation_notes="Appointment 1 - Version 2",
            version_number=2,
            parent_record_id=record1_v1.id,
            created_by=doctor_user.id
        )
        db_session.add(record1_v2)
        
        # Create records for appointment 2 (v1, v2, v3)
        record2_v1 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=appointment2.id,
            consultation_notes="Appointment 2 - Version 1",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record2_v1)
        db_session.commit()
        db_session.refresh(record2_v1)
        
        record2_v2 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=appointment2.id,
            consultation_notes="Appointment 2 - Version 2",
            version_number=2,
            parent_record_id=record2_v1.id,
            created_by=doctor_user.id
        )
        db_session.add(record2_v2)
        db_session.commit()
        db_session.refresh(record2_v2)
        
        record2_v3 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=appointment2.id,
            consultation_notes="Appointment 2 - Version 3",
            version_number=3,
            parent_record_id=record2_v2.id,
            created_by=doctor_user.id
        )
        db_session.add(record2_v3)
        db_session.commit()
        
        # Patient requests their records
        patient_user = test_users['patient']['user']
        headers = get_auth_header(patient_user)
        
        response = client.get(
            f"/api/v1/medical-records/patient/{patient.id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return 2 records (latest version of each appointment)
        assert len(data) == 2
        
        # Find records by appointment
        appt1_record = next((r for r in data if r["appointment_id"] == appointment1.id), None)
        appt2_record = next((r for r in data if r["appointment_id"] == appointment2.id), None)
        
        assert appt1_record is not None
        assert appt1_record["version_number"] == 2
        assert "Version 2" in appt1_record["consultation_notes"]
        
        assert appt2_record is not None
        assert appt2_record["version_number"] == 3
        assert "Version 3" in appt2_record["consultation_notes"]
    
    def test_nonexistent_patient(self, client, db_session: Session, test_users):
        """Test requesting records for a non-existent patient"""
        patient_user = test_users['patient']['user']
        headers = get_auth_header(patient_user)
        
        response = client.get(
            "/api/v1/medical-records/patient/99999",
            headers=headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_patient_with_no_records(self, client, db_session: Session, test_users):
        """Test requesting records for a patient with no medical records"""
        patient_user = test_users['patient']['user']
        patient = test_users['patient']['patient']
        
        headers = get_auth_header(patient_user)
        
        response = client.get(
            f"/api/v1/medical-records/patient/{patient.id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0
    
    def test_unauthenticated_request(self, client, test_users):
        """Test that unauthenticated requests are rejected"""
        patient = test_users['patient']['patient']
        
        response = client.get(
            f"/api/v1/medical-records/patient/{patient.id}"
        )
        
        assert response.status_code == 401
    
    def test_invalid_token(self, client, test_users):
        """Test that invalid tokens are rejected"""
        patient = test_users['patient']['patient']
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get(
            f"/api/v1/medical-records/patient/{patient.id}",
            headers=headers
        )
        
        assert response.status_code == 401
    
    def test_response_includes_all_fields(self, client, db_session: Session, test_users, test_appointment):
        """Test that response includes all required fields"""
        doctor_user = test_users['doctor']['user']
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        patient_user = test_users['patient']['user']
        
        # Create a complete medical record
        record = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="Complete consultation notes",
            diagnosis="Test diagnosis",
            prescription="Test prescription",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record)
        db_session.commit()
        
        # Patient requests their records
        headers = get_auth_header(patient_user)
        
        response = client.get(
            f"/api/v1/medical-records/patient/{patient.id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        
        record_data = data[0]
        
        # Verify all fields are present
        assert "id" in record_data
        assert "patient_id" in record_data
        assert "patient_name" in record_data
        assert record_data["patient_name"] == patient_user.name
        assert "doctor_id" in record_data
        assert "doctor_name" in record_data
        assert record_data["doctor_name"] == doctor_user.name
        assert "appointment_id" in record_data
        assert "consultation_notes" in record_data
        assert "diagnosis" in record_data
        assert "prescription" in record_data
        assert "version_number" in record_data
        assert "parent_record_id" in record_data
        assert "created_by" in record_data
        assert "created_at" in record_data
    
    def test_standalone_records_without_appointment(self, client, db_session: Session, test_users):
        """Test that records without appointment_id are also returned"""
        doctor_user = test_users['doctor']['user']
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        
        # Create standalone record (no appointment)
        record = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=None,
            consultation_notes="Standalone consultation",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record)
        db_session.commit()
        
        # Patient requests their records
        patient_user = test_users['patient']['user']
        headers = get_auth_header(patient_user)
        
        response = client.get(
            f"/api/v1/medical-records/patient/{patient.id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["appointment_id"] is None
        assert "Standalone consultation" in data[0]["consultation_notes"]



class TestVersionHistoryRetrieval:
    """Tests for version history retrieval endpoint"""
    
    def test_get_version_history_success(self, client, db_session: Session, test_users, test_appointment):
        """Test successful retrieval of version history"""
        doctor_user = test_users['doctor']['user']
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        
        # Create version 1
        record_v1 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="Version 1 notes",
            diagnosis="Initial diagnosis",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record_v1)
        db_session.commit()
        db_session.refresh(record_v1)
        
        # Create version 2
        record_v2 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="Version 2 notes",
            diagnosis="Updated diagnosis",
            version_number=2,
            parent_record_id=record_v1.id,
            created_by=doctor_user.id
        )
        db_session.add(record_v2)
        db_session.commit()
        db_session.refresh(record_v2)
        
        # Create version 3
        record_v3 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="Version 3 notes",
            diagnosis="Final diagnosis",
            version_number=3,
            parent_record_id=record_v2.id,
            created_by=doctor_user.id
        )
        db_session.add(record_v3)
        db_session.commit()
        db_session.refresh(record_v3)
        
        # Patient requests version history
        patient_user = test_users['patient']['user']
        headers = get_auth_header(patient_user)
        
        response = client.get(
            f"/api/v1/medical-records/{record_v1.id}/versions",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return all 3 versions
        assert len(data) == 3
        
        # Verify sorting (oldest first - ascending by version_number)
        assert data[0]["version_number"] == 1
        assert data[1]["version_number"] == 2
        assert data[2]["version_number"] == 3
        
        # Verify content
        assert "Version 1 notes" in data[0]["consultation_notes"]
        assert "Version 2 notes" in data[1]["consultation_notes"]
        assert "Version 3 notes" in data[2]["consultation_notes"]
        
        # Verify created_by_name is included
        assert data[0]["created_by_name"] == doctor_user.name
        assert data[1]["created_by_name"] == doctor_user.name
        assert data[2]["created_by_name"] == doctor_user.name
        
        # Verify patient and doctor names
        assert data[0]["patient_name"] == patient_user.name
        assert data[0]["doctor_name"] == doctor_user.name
    
    def test_get_version_history_from_any_version(self, client, db_session: Session, test_users, test_appointment):
        """Test that version history can be retrieved using any version ID"""
        doctor_user = test_users['doctor']['user']
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        
        # Create 3 versions
        record_v1 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="V1",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record_v1)
        db_session.commit()
        db_session.refresh(record_v1)
        
        record_v2 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="V2",
            version_number=2,
            parent_record_id=record_v1.id,
            created_by=doctor_user.id
        )
        db_session.add(record_v2)
        db_session.commit()
        db_session.refresh(record_v2)
        
        record_v3 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="V3",
            version_number=3,
            parent_record_id=record_v2.id,
            created_by=doctor_user.id
        )
        db_session.add(record_v3)
        db_session.commit()
        db_session.refresh(record_v3)
        
        patient_user = test_users['patient']['user']
        headers = get_auth_header(patient_user)
        
        # Request using v1 ID
        response1 = client.get(
            f"/api/v1/medical-records/{record_v1.id}/versions",
            headers=headers
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1) == 3
        
        # Request using v2 ID
        response2 = client.get(
            f"/api/v1/medical-records/{record_v2.id}/versions",
            headers=headers
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2) == 3
        
        # Request using v3 ID
        response3 = client.get(
            f"/api/v1/medical-records/{record_v3.id}/versions",
            headers=headers
        )
        assert response3.status_code == 200
        data3 = response3.json()
        assert len(data3) == 3
        
        # All should return the same versions
        assert data1 == data2 == data3
    
    def test_patient_can_view_own_version_history(self, client, db_session: Session, test_users, test_appointment):
        """Test that patients can view version history of their own records"""
        doctor_user = test_users['doctor']['user']
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        
        # Create record with versions
        record = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="Patient's record",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)
        
        # Patient requests version history
        patient_user = test_users['patient']['user']
        headers = get_auth_header(patient_user)
        
        response = client.get(
            f"/api/v1/medical-records/{record.id}/versions",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    def test_patient_cannot_view_other_patient_version_history(self, client, db_session: Session, test_users, test_appointment):
        """Test that patients cannot view version history of other patients' records"""
        doctor_user = test_users['doctor']['user']
        doctor = test_users['doctor']['doctor']
        
        # Create another patient
        other_patient_user = User(
            name="Other Patient",
            email="other@test.com",
            password_hash=get_password_hash("password123"),
            role=UserRole.PATIENT
        )
        db_session.add(other_patient_user)
        db_session.flush()
        
        other_patient = Patient(
            user_id=other_patient_user.id,
            date_of_birth=datetime(1990, 1, 1),
            gender="Male",
            phone="9999999999"
        )
        db_session.add(other_patient)
        db_session.commit()
        db_session.refresh(other_patient)
        
        # Create record for other patient
        record = MedicalRecord(
            patient_id=other_patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="Other patient's record",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)
        
        # Original patient tries to access other patient's version history
        patient_user = test_users['patient']['user']
        headers = get_auth_header(patient_user)
        
        response = client.get(
            f"/api/v1/medical-records/{record.id}/versions",
            headers=headers
        )
        
        assert response.status_code == 403
        assert "your own" in response.json()["detail"].lower()
    
    def test_doctor_can_view_treated_patient_version_history(self, client, db_session: Session, test_users, test_appointment):
        """Test that doctors can view version history of patients they've treated"""
        doctor_user = test_users['doctor']['user']
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        
        # Create record (doctor has treated this patient)
        record = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="Doctor's patient record",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)
        
        # Doctor requests version history
        headers = get_auth_header(doctor_user)
        
        response = client.get(
            f"/api/v1/medical-records/{record.id}/versions",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    def test_doctor_cannot_view_untreated_patient_version_history(self, client, db_session: Session, test_users, test_appointment):
        """Test that doctors cannot view version history of patients they haven't treated"""
        doctor1_user = test_users['doctor']['user']
        doctor1 = test_users['doctor']['doctor']
        doctor2_user = test_users['doctor2']['user']
        patient = test_users['patient']['patient']
        
        # Create record with doctor1
        record = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor1.id,
            appointment_id=test_appointment.id,
            consultation_notes="Doctor 1's record",
            version_number=1,
            created_by=doctor1_user.id
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)
        
        # Doctor2 tries to access version history
        headers = get_auth_header(doctor2_user)
        
        response = client.get(
            f"/api/v1/medical-records/{record.id}/versions",
            headers=headers
        )
        
        assert response.status_code == 403
        assert "treated" in response.json()["detail"].lower()
    
    def test_admin_can_view_any_version_history(self, client, db_session: Session, test_users, test_appointment):
        """Test that admins can view any patient's version history"""
        # Create admin user
        admin_user = User(
            name="Admin User",
            email="admin@test.com",
            password_hash=get_password_hash("password123"),
            role=UserRole.ADMIN
        )
        db_session.add(admin_user)
        db_session.commit()
        db_session.refresh(admin_user)
        
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        
        # Create record
        record = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="Admin viewing this",
            version_number=1,
            created_by=test_users['doctor']['user'].id
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)
        
        # Admin requests version history
        headers = get_auth_header(admin_user)
        
        response = client.get(
            f"/api/v1/medical-records/{record.id}/versions",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    def test_nurse_cannot_view_version_history(self, client, db_session: Session, test_users, test_appointment):
        """Test that nurses cannot view version history"""
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        
        # Create record
        record = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="Nurse trying to view",
            version_number=1,
            created_by=test_users['doctor']['user'].id
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)
        
        # Nurse tries to access version history
        nurse_user = test_users['nurse']['user']
        headers = get_auth_header(nurse_user)
        
        response = client.get(
            f"/api/v1/medical-records/{record.id}/versions",
            headers=headers
        )
        
        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()
    
    def test_version_history_includes_all_fields(self, client, db_session: Session, test_users, test_appointment):
        """Test that version history includes all record fields"""
        doctor_user = test_users['doctor']['user']
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        
        # Create record with all fields
        record = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="Complete consultation notes",
            diagnosis="Complete diagnosis",
            prescription="Complete prescription",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)
        
        # Patient requests version history
        patient_user = test_users['patient']['user']
        headers = get_auth_header(patient_user)
        
        response = client.get(
            f"/api/v1/medical-records/{record.id}/versions",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        
        version = data[0]
        assert version["id"] == record.id
        assert version["patient_id"] == patient.id
        assert version["patient_name"] == patient_user.name
        assert version["doctor_id"] == doctor.id
        assert version["doctor_name"] == doctor_user.name
        assert version["appointment_id"] == test_appointment.id
        assert version["consultation_notes"] == "Complete consultation notes"
        assert version["diagnosis"] == "Complete diagnosis"
        assert version["prescription"] == "Complete prescription"
        assert version["version_number"] == 1
        assert version["parent_record_id"] is None
        assert version["created_by"] == doctor_user.id
        assert version["created_by_name"] == doctor_user.name
        assert version["created_at"] is not None
    
    def test_version_history_sorted_ascending(self, client, db_session: Session, test_users, test_appointment):
        """Test that versions are sorted by version_number in ascending order (oldest first)"""
        doctor_user = test_users['doctor']['user']
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        
        # Create versions in reverse order to test sorting
        record_v3 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="V3",
            version_number=3,
            created_by=doctor_user.id
        )
        db_session.add(record_v3)
        db_session.commit()
        db_session.refresh(record_v3)
        
        record_v1 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="V1",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record_v1)
        db_session.commit()
        db_session.refresh(record_v1)
        
        record_v2 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="V2",
            version_number=2,
            parent_record_id=record_v1.id,
            created_by=doctor_user.id
        )
        db_session.add(record_v2)
        db_session.commit()
        
        # Update v3 to link to v2
        record_v3.parent_record_id = record_v2.id
        db_session.commit()
        
        # Patient requests version history
        patient_user = test_users['patient']['user']
        headers = get_auth_header(patient_user)
        
        response = client.get(
            f"/api/v1/medical-records/{record_v2.id}/versions",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        # Verify ascending order
        assert data[0]["version_number"] == 1
        assert data[1]["version_number"] == 2
        assert data[2]["version_number"] == 3
    
    def test_version_history_nonexistent_record(self, client, db_session: Session, test_users):
        """Test requesting version history for non-existent record"""
        patient_user = test_users['patient']['user']
        headers = get_auth_header(patient_user)
        
        response = client.get(
            "/api/v1/medical-records/99999/versions",
            headers=headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_version_history_single_version(self, client, db_session: Session, test_users, test_appointment):
        """Test version history for a record with only one version"""
        doctor_user = test_users['doctor']['user']
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        
        # Create single version
        record = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="Only version",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)
        
        # Patient requests version history
        patient_user = test_users['patient']['user']
        headers = get_auth_header(patient_user)
        
        response = client.get(
            f"/api/v1/medical-records/{record.id}/versions",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["version_number"] == 1
    
    def test_version_history_without_authentication(self, client, db_session: Session, test_users, test_appointment):
        """Test that unauthenticated requests are rejected"""
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        
        # Create record
        record = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="Test",
            version_number=1,
            created_by=test_users['doctor']['user'].id
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)
        
        # Request without authentication
        response = client.get(
            f"/api/v1/medical-records/{record.id}/versions"
        )
        
        assert response.status_code == 401
    
    def test_version_history_invalid_token(self, client, db_session: Session, test_users, test_appointment):
        """Test that invalid tokens are rejected"""
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        
        # Create record
        record = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="Test",
            version_number=1,
            created_by=test_users['doctor']['user'].id
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)
        
        # Request with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get(
            f"/api/v1/medical-records/{record.id}/versions",
            headers=headers
        )
        
        assert response.status_code == 401
    
    def test_version_history_shows_who_made_changes(self, client, db_session: Session, test_users, test_appointment):
        """Test that version history displays who made each change"""
        doctor_user = test_users['doctor']['user']
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        
        # Create version 1
        record_v1 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="V1",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record_v1)
        db_session.commit()
        db_session.refresh(record_v1)
        
        # Create version 2 (same doctor)
        record_v2 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="V2",
            version_number=2,
            parent_record_id=record_v1.id,
            created_by=doctor_user.id
        )
        db_session.add(record_v2)
        db_session.commit()
        
        # Patient requests version history
        patient_user = test_users['patient']['user']
        headers = get_auth_header(patient_user)
        
        response = client.get(
            f"/api/v1/medical-records/{record_v1.id}/versions",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Verify created_by_name is present
        assert data[0]["created_by"] == doctor_user.id
        assert data[0]["created_by_name"] == doctor_user.name
        assert data[1]["created_by"] == doctor_user.id
        assert data[1]["created_by_name"] == doctor_user.name
    
    def test_version_history_shows_timestamps(self, client, db_session: Session, test_users, test_appointment):
        """Test that version history includes timestamps for each version"""
        doctor_user = test_users['doctor']['user']
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        
        # Create versions
        record_v1 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="V1",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record_v1)
        db_session.commit()
        db_session.refresh(record_v1)
        
        record_v2 = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="V2",
            version_number=2,
            parent_record_id=record_v1.id,
            created_by=doctor_user.id
        )
        db_session.add(record_v2)
        db_session.commit()
        
        # Patient requests version history
        patient_user = test_users['patient']['user']
        headers = get_auth_header(patient_user)
        
        response = client.get(
            f"/api/v1/medical-records/{record_v1.id}/versions",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Verify timestamps are present
        assert data[0]["created_at"] is not None
        assert data[1]["created_at"] is not None
        
        # Verify v2 timestamp is after v1 timestamp
        from datetime import datetime
        v1_time = datetime.fromisoformat(data[0]["created_at"].replace('Z', '+00:00'))
        v2_time = datetime.fromisoformat(data[1]["created_at"].replace('Z', '+00:00'))
        assert v2_time >= v1_time
