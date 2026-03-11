"""
Additional unit tests for medical records endpoints
Focuses on edge cases and integration scenarios
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


class TestRecordCreationEdgeCases:
    """Additional edge case tests for record creation"""
    
    def test_create_record_with_very_long_notes(self, client, db_session: Session, test_users, test_appointment):
        """Test creating a record with very long consultation notes"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Create very long notes (10,000 characters)
        long_notes = "A" * 10000
        
        payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": long_notes,
            "diagnosis": "Test diagnosis"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert len(data["consultation_notes"]) == 10000
    
    def test_create_record_with_unicode_characters(self, client, db_session: Session, test_users, test_appointment):
        """Test creating a record with unicode characters"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Patient has 发烧 (fever) and 咳嗽 (cough). Prescribed 药物 (medication).",
            "diagnosis": "上呼吸道感染 (Upper respiratory infection)"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "发烧" in data["consultation_notes"]
        assert "上呼吸道感染" in data["diagnosis"]
    
    def test_create_prescription_with_complex_dosage(self, client, db_session: Session, test_users, test_appointment):
        """Test creating a prescription with complex dosage instructions"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        payload = {
            "appointment_id": test_appointment.id,
            "medication": "Insulin Glargine",
            "dosage": "10 units subcutaneously",
            "frequency": "Once daily at bedtime, adjust based on fasting glucose levels",
            "duration": "Ongoing - review every 3 months"
        }
        
        response = client.post(
            "/api/v1/medical-records/prescriptions",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "subcutaneously" in data["prescription"]
        assert "fasting glucose" in data["prescription"]


class TestVersioningEdgeCases:
    """Additional edge case tests for versioning logic"""
    
    def test_version_chain_integrity(self, client, db_session: Session, test_users, test_appointment):
        """Test that version chain maintains integrity through multiple updates"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Create initial record
        create_payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Version 1"
        }
        
        response1 = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=create_payload,
            headers=headers
        )
        assert response1.status_code == 201
        v1 = response1.json()
        
        # Create 5 more versions
        previous_id = v1["id"]
        for i in range(2, 7):
            update_payload = {
                "consultation_notes": f"Version {i}"
            }
            
            response = client.put(
                f"/api/v1/medical-records/consultation-notes/{previous_id}",
                json=update_payload,
                headers=headers
            )
            assert response.status_code == 200
            data = response.json()
            
            # Verify version number increments correctly
            assert data["version_number"] == i
            # Verify parent_record_id points to previous version
            assert data["parent_record_id"] == previous_id
            
            previous_id = data["id"]
        
        # Verify all versions exist in database
        all_versions = db_session.query(MedicalRecord).filter(
            MedicalRecord.appointment_id == test_appointment.id
        ).order_by(MedicalRecord.version_number).all()
        
        assert len(all_versions) == 6
        for i, version in enumerate(all_versions, start=1):
            assert version.version_number == i
    
    def test_concurrent_version_creation(self, client, db_session: Session, test_users, test_appointment):
        """Test that version numbers are correctly assigned even with concurrent updates"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Create initial record
        create_payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Initial version"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=create_payload,
            headers=headers
        )
        assert response.status_code == 201
        original = response.json()
        
        # Simulate concurrent updates by updating from the same base version
        update_payload1 = {
            "consultation_notes": "Update 1"
        }
        
        update_payload2 = {
            "consultation_notes": "Update 2"
        }
        
        response1 = client.put(
            f"/api/v1/medical-records/consultation-notes/{original['id']}",
            json=update_payload1,
            headers=headers
        )
        
        response2 = client.put(
            f"/api/v1/medical-records/consultation-notes/{original['id']}",
            json=update_payload2,
            headers=headers
        )
        
        # Both should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Both should have version_number = 2 (updating from v1)
        assert response1.json()["version_number"] == 2
        assert response2.json()["version_number"] == 2


class TestAccessControlEdgeCases:
    """Additional edge case tests for access control"""
    
    def test_patient_cannot_modify_own_records(self, client, db_session: Session, test_users, test_appointment):
        """Test that patients cannot modify their own medical records"""
        # Create a record as doctor
        doctor_user = test_users['doctor']['user']
        doctor_headers = get_auth_header(doctor_user)
        
        create_payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Doctor's notes"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=create_payload,
            headers=doctor_headers
        )
        assert response.status_code == 201
        record = response.json()
        
        # Try to update as patient
        patient_user = test_users['patient']['user']
        patient_headers = get_auth_header(patient_user)
        
        update_payload = {
            "consultation_notes": "Patient trying to modify"
        }
        
        response = client.put(
            f"/api/v1/medical-records/consultation-notes/{record['id']}",
            json=update_payload,
            headers=patient_headers
        )
        
        # Should be forbidden
        assert response.status_code == 403
    
    def test_doctor_access_after_treating_patient(self, client, db_session: Session, test_users):
        """Test that doctor can access patient records after treating them"""
        doctor_user = test_users['doctor']['user']
        doctor = test_users['doctor']['doctor']
        patient = test_users['patient']['patient']
        
        # Initially, doctor has not treated this patient
        headers = get_auth_header(doctor_user)
        
        response = client.get(
            f"/api/v1/medical-records/patient/{patient.id}",
            headers=headers
        )
        
        # Should be forbidden
        assert response.status_code == 403
        
        # Now create an appointment and record
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
        
        # Create a medical record
        record = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_id=appointment.id,
            consultation_notes="First consultation",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record)
        db_session.commit()
        
        # Now doctor should be able to access patient records
        response = client.get(
            f"/api/v1/medical-records/patient/{patient.id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    def test_record_isolation_between_patients(self, client, db_session: Session, test_users):
        """Test that records are properly isolated between different patients"""
        doctor_user = test_users['doctor']['user']
        doctor = test_users['doctor']['doctor']
        patient1 = test_users['patient']['patient']
        
        # Create second patient
        patient2_user = User(
            name="Jane Smith",
            email="patient2@test.com",
            password_hash=get_password_hash("password123"),
            role=UserRole.PATIENT
        )
        db_session.add(patient2_user)
        db_session.flush()
        
        patient2 = Patient(
            user_id=patient2_user.id,
            date_of_birth=datetime(1985, 5, 15),
            gender="Female",
            phone="9876543210"
        )
        db_session.add(patient2)
        db_session.commit()
        db_session.refresh(patient2)
        db_session.refresh(patient2_user)
        
        # Create records for both patients
        record1 = MedicalRecord(
            patient_id=patient1.id,
            doctor_id=doctor.id,
            consultation_notes="Patient 1 record",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record1)
        
        record2 = MedicalRecord(
            patient_id=patient2.id,
            doctor_id=doctor.id,
            consultation_notes="Patient 2 record",
            version_number=1,
            created_by=doctor_user.id
        )
        db_session.add(record2)
        db_session.commit()
        
        # Patient 1 retrieves their records
        patient1_user = test_users['patient']['user']
        headers1 = get_auth_header(patient1_user)
        
        response1 = client.get(
            f"/api/v1/medical-records/patient/{patient1.id}",
            headers=headers1
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Verify only patient 1's records are returned
        for record in data1:
            assert record["patient_id"] == patient1.id
            assert "Patient 1 record" in record["consultation_notes"]
            assert "Patient 2 record" not in record["consultation_notes"]
        
        # Patient 2 retrieves their records
        headers2 = get_auth_header(patient2_user)
        
        response2 = client.get(
            f"/api/v1/medical-records/patient/{patient2.id}",
            headers=headers2
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Verify only patient 2's records are returned
        for record in data2:
            assert record["patient_id"] == patient2.id
            assert "Patient 2 record" in record["consultation_notes"]
            assert "Patient 1 record" not in record["consultation_notes"]


class TestRecordDataIntegrity:
    """Tests for data integrity and consistency"""
    
    def test_record_preserves_all_fields_on_update(self, client, db_session: Session, test_users, test_appointment):
        """Test that all fields are preserved correctly when updating a record"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Create initial record with all fields
        create_payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "Initial consultation notes",
            "diagnosis": "Initial diagnosis"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=create_payload,
            headers=headers
        )
        assert response.status_code == 201
        original = response.json()
        
        # Add prescription to the record
        db_record = db_session.query(MedicalRecord).filter(
            MedicalRecord.id == original["id"]
        ).first()
        db_record.prescription = "Original prescription"
        db_session.commit()
        
        # Update only diagnosis
        update_payload = {
            "diagnosis": "Updated diagnosis"
        }
        
        response = client.put(
            f"/api/v1/medical-records/consultation-notes/{original['id']}",
            json=update_payload,
            headers=headers
        )
        
        assert response.status_code == 200
        updated = response.json()
        
        # Verify all fields are preserved
        assert updated["consultation_notes"] == "Initial consultation notes"
        assert updated["diagnosis"] == "Updated diagnosis"
        assert updated["prescription"] == "Original prescription"
        assert updated["patient_id"] == original["patient_id"]
        assert updated["doctor_id"] == original["doctor_id"]
        assert updated["appointment_id"] == original["appointment_id"]
    
    def test_version_history_completeness(self, client, db_session: Session, test_users, test_appointment):
        """Test that version history includes all versions without gaps"""
        doctor_user = test_users['doctor']['user']
        headers = get_auth_header(doctor_user)
        
        # Create initial record
        create_payload = {
            "appointment_id": test_appointment.id,
            "consultation_notes": "V1"
        }
        
        response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json=create_payload,
            headers=headers
        )
        v1_id = response.json()["id"]
        
        # Create multiple versions
        version_ids = [v1_id]
        for i in range(2, 6):
            update_payload = {
                "consultation_notes": f"V{i}"
            }
            
            response = client.put(
                f"/api/v1/medical-records/consultation-notes/{version_ids[-1]}",
                json=update_payload,
                headers=headers
            )
            version_ids.append(response.json()["id"])
        
        # Get version history
        patient_user = test_users['patient']['user']
        patient_headers = get_auth_header(patient_user)
        
        response = client.get(
            f"/api/v1/medical-records/{v1_id}/versions",
            headers=patient_headers
        )
        
        assert response.status_code == 200
        versions = response.json()
        
        # Verify completeness
        assert len(versions) == 5
        
        # Verify no gaps in version numbers
        version_numbers = [v["version_number"] for v in versions]
        assert version_numbers == [1, 2, 3, 4, 5]
        
        # Verify parent_record_id chain
        assert versions[0]["parent_record_id"] is None
        for i in range(1, 5):
            assert versions[i]["parent_record_id"] == versions[i-1]["id"]
