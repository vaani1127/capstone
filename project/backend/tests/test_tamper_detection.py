"""
Tests for tamper detection functionality
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
from app.services.blockchain_service import create_audit_entry, verify_record_integrity


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
    
    # Create admin user
    admin_user = User(
        name="Admin User",
        email="admin@test.com",
        password_hash=get_password_hash("password123"),
        role=UserRole.ADMIN
    )
    db_session.add(admin_user)
    users['admin'] = {'user': admin_user}
    
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


class TestTamperDetection:
    """Tests for tamper detection in medical records"""
    
    def test_untampered_record_shows_not_tampered(self, client, db_session: Session, test_users, test_appointment):
        """Test that a valid, untampered record shows is_tampered=False"""
        doctor_user = test_users['doctor']['user']
        patient_user = test_users['patient']['user']
        headers = get_auth_header(doctor_user)
        
        # Create a consultation note
        payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Patient has mild fever and cough",
            "diagnosis": "Common cold"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        assert response.status_code == 201
        
        # Retrieve patient records
        patient_headers = get_auth_header(patient_user)
        response = client.get(
            f"/api/v1/medical-records/patient/{test_users['patient']['patient'].id}",
            headers=patient_headers
        )
        
        assert response.status_code == 200
        records = response.json()
        assert len(records) == 1
        assert records[0]["is_tampered"] is False
    
    def test_tampered_record_detected_and_flagged(self, client, db_session: Session, test_users, test_appointment):
        """Test that tampering is detected and the record is flagged"""
        doctor_user = test_users['doctor']['user']
        patient_user = test_users['patient']['user']
        headers = get_auth_header(doctor_user)
        
        # Create a consultation note
        payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Original consultation notes",
            "diagnosis": "Original diagnosis"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        assert response.status_code == 201
        record_id = response.json()["id"]
        
        # Tamper with the record directly in the database (simulate tampering)
        medical_record = db_session.query(MedicalRecord).filter(
            MedicalRecord.id == record_id
        ).first()
        medical_record.consultation_notes = "TAMPERED NOTES - This was changed maliciously"
        db_session.commit()
        
        # Retrieve patient records - this should detect tampering
        patient_headers = get_auth_header(patient_user)
        response = client.get(
            f"/api/v1/medical-records/patient/{test_users['patient']['patient'].id}",
            headers=patient_headers
        )
        
        assert response.status_code == 200
        records = response.json()
        assert len(records) == 1
        assert records[0]["is_tampered"] is True
        
        # Verify that the audit_chain entry was flagged
        audit_entry = db_session.query(AuditChain).filter(
            AuditChain.record_id == record_id,
            AuditChain.record_type == "medical_record"
        ).first()
        assert audit_entry is not None
        assert audit_entry.is_tampered is True
    
    def test_tampered_diagnosis_detected(self, client, db_session: Session, test_users, test_appointment):
        """Test that tampering with diagnosis field is detected"""
        doctor_user = test_users['doctor']['user']
        patient_user = test_users['patient']['user']
        headers = get_auth_header(doctor_user)
        
        # Create a consultation note
        payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Patient examination complete",
            "diagnosis": "Hypertension"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        assert response.status_code == 201
        record_id = response.json()["id"]
        
        # Tamper with diagnosis
        medical_record = db_session.query(MedicalRecord).filter(
            MedicalRecord.id == record_id
        ).first()
        medical_record.diagnosis = "Diabetes"  # Changed diagnosis
        db_session.commit()
        
        # Retrieve and verify tampering detected
        patient_headers = get_auth_header(patient_user)
        response = client.get(
            f"/api/v1/medical-records/patient/{test_users['patient']['patient'].id}",
            headers=patient_headers
        )
        
        assert response.status_code == 200
        records = response.json()
        assert records[0]["is_tampered"] is True
    
    def test_tampered_prescription_detected(self, client, db_session: Session, test_users, test_appointment):
        """Test that tampering with prescription is detected"""
        doctor_user = test_users['doctor']['user']
        patient_user = test_users['patient']['user']
        headers = get_auth_header(doctor_user)
        
        # Create a prescription
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
        record_id = response.json()["id"]
        
        # Tamper with prescription
        medical_record = db_session.query(MedicalRecord).filter(
            MedicalRecord.id == record_id
        ).first()
        medical_record.prescription = "Medication: Morphine\nDosage: 100mg"  # Malicious change
        db_session.commit()
        
        # Retrieve and verify tampering detected
        patient_headers = get_auth_header(patient_user)
        response = client.get(
            f"/api/v1/medical-records/patient/{test_users['patient']['patient'].id}",
            headers=patient_headers
        )
        
        assert response.status_code == 200
        records = response.json()
        assert records[0]["is_tampered"] is True
    
    def test_version_history_shows_tampering_status(self, client, db_session: Session, test_users, test_appointment):
        """Test that version history endpoint includes tampering status"""
        doctor_user = test_users['doctor']['user']
        patient_user = test_users['patient']['user']
        headers = get_auth_header(doctor_user)
        
        # Create initial consultation note
        payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Version 1 notes",
            "diagnosis": "Initial diagnosis"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        assert response.status_code == 201
        v1_id = response.json()["id"]
        
        # Create version 2
        update_payload = {
            "consultation_notes": "Version 2 notes - updated"
        }
        
        response = client.put(
            f"/api/v1/medical-records/consultation-notes/{v1_id}",
            json=update_payload,
            headers=headers
        )
        assert response.status_code == 200
        v2_id = response.json()["id"]
        
        # Tamper with version 1
        medical_record = db_session.query(MedicalRecord).filter(
            MedicalRecord.id == v1_id
        ).first()
        medical_record.consultation_notes = "TAMPERED VERSION 1"
        db_session.commit()
        
        # Get version history
        patient_headers = get_auth_header(patient_user)
        response = client.get(
            f"/api/v1/medical-records/{v1_id}/versions",
            headers=patient_headers
        )
        
        assert response.status_code == 200
        versions = response.json()
        assert len(versions) == 2
        
        # Version 1 should be tampered
        v1_data = next(v for v in versions if v["id"] == v1_id)
        assert v1_data["is_tampered"] is True
        
        # Version 2 should not be tampered
        v2_data = next(v for v in versions if v["id"] == v2_id)
        assert v2_data["is_tampered"] is False
    
    def test_multiple_records_mixed_tampering(self, client, db_session: Session, test_users):
        """Test detection when some records are tampered and others are not"""
        doctor_user = test_users['doctor']['user']
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        patient_user = test_users['patient']['user']
        headers = get_auth_header(doctor_user)
        
        # Create multiple appointments and records
        appointments = []
        for i in range(3):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=datetime.now() + timedelta(hours=i+1),
                status=AppointmentStatus.SCHEDULED,
                appointment_type=AppointmentType.SCHEDULED
            )
            db_session.add(appointment)
            db_session.flush()
            appointments.append(appointment)
        
        db_session.commit()
        
        # Create consultation notes for each appointment
        record_ids = []
        for i, appointment in enumerate(appointments):
            payload = {
                "appointment_id": appointment.id,
                "consultation_notes": f"Consultation notes for appointment {i+1}",
                "diagnosis": f"Diagnosis {i+1}"
            }
            
            response = client.post(
                "/api/v1/medical-records/consultation-notes",
                json=payload,
                headers=headers
            )
            assert response.status_code == 201
            record_ids.append(response.json()["id"])
        
        # Tamper with the second record only
        medical_record = db_session.query(MedicalRecord).filter(
            MedicalRecord.id == record_ids[1]
        ).first()
        medical_record.consultation_notes = "TAMPERED RECORD"
        db_session.commit()
        
        # Retrieve all patient records
        patient_headers = get_auth_header(patient_user)
        response = client.get(
            f"/api/v1/medical-records/patient/{patient.id}",
            headers=patient_headers
        )
        
        assert response.status_code == 200
        records = response.json()
        assert len(records) == 3
        
        # Check tampering status for each record
        for record in records:
            if record["id"] == record_ids[1]:
                assert record["is_tampered"] is True
            else:
                assert record["is_tampered"] is False
    
    def test_tampering_logged_with_details(self, client, db_session: Session, test_users, test_appointment, caplog):
        """Test that tampering detection is logged with appropriate details"""
        import logging
        
        doctor_user = test_users['doctor']['user']
        patient_user = test_users['patient']['user']
        headers = get_auth_header(doctor_user)
        
        # Create a consultation note
        payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Original notes",
            "diagnosis": "Original diagnosis"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        assert response.status_code == 201
        record_id = response.json()["id"]
        
        # Tamper with the record
        medical_record = db_session.query(MedicalRecord).filter(
            MedicalRecord.id == record_id
        ).first()
        medical_record.consultation_notes = "TAMPERED"
        db_session.commit()
        
        # Retrieve records with logging enabled
        with caplog.at_level(logging.WARNING):
            patient_headers = get_auth_header(patient_user)
            response = client.get(
                f"/api/v1/medical-records/patient/{test_users['patient']['patient'].id}",
                headers=patient_headers
            )
        
        assert response.status_code == 200
        
        # Check that tampering was logged
        assert any("TAMPERING DETECTED" in record.message for record in caplog.records)
        assert any(f"Medical record {record_id}" in record.message for record in caplog.records)
    
    def test_verify_record_integrity_function(self, db_session: Session, test_users, test_appointment):
        """Test the verify_record_integrity function directly"""
        doctor_user = test_users['doctor']['user']
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        
        # Create a medical record
        medical_record = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="Test consultation notes",
            diagnosis="Test diagnosis",
            version_number=1,
            created_by=doctor_user.id
        )
        
        db_session.add(medical_record)
        db_session.flush()
        
        # Create audit entry
        create_audit_entry(db_session, medical_record, doctor_user.id)
        db_session.commit()
        
        # Verify integrity - should pass
        is_valid = verify_record_integrity(db_session, medical_record.id)
        assert is_valid is True
        
        # Tamper with the record
        medical_record.consultation_notes = "TAMPERED NOTES"
        db_session.commit()
        
        # Verify integrity - should fail
        is_valid = verify_record_integrity(db_session, medical_record.id)
        assert is_valid is False
    
    def test_missing_audit_entry_handled_gracefully(self, client, db_session: Session, test_users, test_appointment):
        """Test that missing audit entries don't cause crashes"""
        doctor_user = test_users['doctor']['user']
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        patient_user = test_users['patient']['user']
        
        # Create a medical record WITHOUT audit entry (simulate data corruption)
        medical_record = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=test_appointment.id,
            consultation_notes="Record without audit entry",
            diagnosis="Test",
            version_number=1,
            created_by=doctor_user.id
        )
        
        db_session.add(medical_record)
        db_session.commit()
        
        # Try to retrieve records - should not crash
        patient_headers = get_auth_header(patient_user)
        response = client.get(
            f"/api/v1/medical-records/patient/{patient.id}",
            headers=patient_headers
        )
        
        assert response.status_code == 200
        records = response.json()
        # Should return the record with is_tampered=False (graceful handling)
        assert len(records) == 1
        assert records[0]["is_tampered"] is False
    
    def test_doctor_can_see_tampering_in_their_records(self, client, db_session: Session, test_users, test_appointment):
        """Test that doctors can see tampering status when viewing patient records"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Create a consultation note
        payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Doctor's notes",
            "diagnosis": "Doctor's diagnosis"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        assert response.status_code == 201
        record_id = response.json()["id"]
        
        # Tamper with the record
        medical_record = db_session.query(MedicalRecord).filter(
            MedicalRecord.id == record_id
        ).first()
        medical_record.consultation_notes = "TAMPERED"
        db_session.commit()
        
        # Doctor retrieves patient records
        response = client.get(
            f"/api/v1/medical-records/patient/{test_users['patient']['patient'].id}",
            headers=headers
        )
        
        assert response.status_code == 200
        records = response.json()
        assert len(records) == 1
        assert records[0]["is_tampered"] is True
    
    def test_admin_can_see_tampering_in_all_records(self, client, db_session: Session, test_users, test_appointment):
        """Test that admins can see tampering status for all records"""
        doctor_user = test_users['doctor']['user']
        admin_user = test_users['admin']['user']
        doctor_headers = get_auth_header(doctor_user)
        
        # Create a consultation note
        payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Medical notes",
            "diagnosis": "Medical diagnosis"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=doctor_headers
        )
        assert response.status_code == 201
        record_id = response.json()["id"]
        
        # Tamper with the record
        medical_record = db_session.query(MedicalRecord).filter(
            MedicalRecord.id == record_id
        ).first()
        medical_record.consultation_notes = "TAMPERED BY ATTACKER"
        db_session.commit()
        
        # Admin retrieves patient records
        admin_headers = get_auth_header(admin_user)
        response = client.get(
            f"/api/v1/medical-records/patient/{test_users['patient']['patient'].id}",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        records = response.json()
        assert len(records) == 1
        assert records[0]["is_tampered"] is True


class TestTamperDetectionEdgeCases:
    """Tests for edge cases in tamper detection"""
    
    def test_null_fields_not_flagged_as_tampering(self, client, db_session: Session, test_users, test_appointment):
        """Test that records with null optional fields are not flagged as tampered"""
        doctor_user = test_users['doctor']['user']
        patient_user = test_users['patient']['user']
        headers = get_auth_header(doctor_user)
        
        # Create consultation note without diagnosis (null field)
        payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Notes without diagnosis"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        assert response.status_code == 201
        
        # Retrieve and verify not tampered
        patient_headers = get_auth_header(patient_user)
        response = client.get(
            f"/api/v1/medical-records/patient/{test_users['patient']['patient'].id}",
            headers=patient_headers
        )
        
        assert response.status_code == 200
        records = response.json()
        assert records[0]["is_tampered"] is False
    
    def test_updated_record_versions_not_flagged_as_tampering(self, client, db_session: Session, test_users, test_appointment):
        """Test that legitimate updates (new versions) are not flagged as tampering"""
        doctor_user = test_users['doctor']['user']
        patient_user = test_users['patient']['user']
        headers = get_auth_header(doctor_user)
        
        # Create initial consultation note
        payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Version 1",
            "diagnosis": "Initial"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        assert response.status_code == 201
        v1_id = response.json()["id"]
        
        # Legitimately update via API (creates new version)
        update_payload = {
            "consultation_notes": "Version 2 - legitimate update"
        }
        
        response = client.put(
            f"/api/v1/medical-records/consultation-notes/{v1_id}",
            json=update_payload,
            headers=headers
        )
        assert response.status_code == 200
        
        # Retrieve records - neither version should be tampered
        patient_headers = get_auth_header(patient_user)
        response = client.get(
            f"/api/v1/medical-records/patient/{test_users['patient']['patient'].id}",
            headers=patient_headers
        )
        
        assert response.status_code == 200
        records = response.json()
        # Should return latest version only
        assert len(records) == 1
        assert records[0]["is_tampered"] is False
        
        # Check version history - both versions should be valid
        response = client.get(
            f"/api/v1/medical-records/{v1_id}/versions",
            headers=patient_headers
        )
        
        assert response.status_code == 200
        versions = response.json()
        assert len(versions) == 2
        assert all(v["is_tampered"] is False for v in versions)
