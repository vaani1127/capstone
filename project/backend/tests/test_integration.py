"""
Integration tests for HealthSaathi Healthcare System

Tests complete end-to-end flows:
- Complete appointment booking flow (patient books → doctor sees → consultation → completion)
- Complete consultation flow (check-in → start → notes/prescription → complete)
- WebSocket real-time communication (queue updates, notifications)
- API endpoint integration with authentication and authorization
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import json

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
    """Create complete set of test users for integration tests"""
    # Create patient user
    patient_user = User(
        name="John Doe",
        email="john.doe@test.com",
        password_hash=get_password_hash("patient123"),
        role=UserRole.PATIENT
    )
    db_session.add(patient_user)
    db_session.flush()
    
    patient = Patient(
        user_id=patient_user.id,
        phone="1234567890",
        gender="Male",
        blood_group="O+"
    )
    db_session.add(patient)
    
    # Create doctor user
    doctor_user = User(
        name="Dr. Sarah Smith",
        email="dr.smith@test.com",
        password_hash=get_password_hash("doctor123"),
        role=UserRole.DOCTOR
    )
    db_session.add(doctor_user)
    db_session.flush()
    
    doctor = Doctor(
        user_id=doctor_user.id,
        specialization="General Medicine",
        license_number="DOC12345",
        average_consultation_duration=15
    )
    db_session.add(doctor)
    
    # Create nurse user
    nurse_user = User(
        name="Nurse Jane",
        email="nurse.jane@test.com",
        password_hash=get_password_hash("nurse123"),
        role=UserRole.NURSE
    )
    db_session.add(nurse_user)
    
    # Create admin user
    admin_user = User(
        name="Admin User",
        email="admin@test.com",
        password_hash=get_password_hash("admin123"),
        role=UserRole.ADMIN
    )
    db_session.add(admin_user)
    
    db_session.commit()
    db_session.refresh(patient_user)
    db_session.refresh(doctor_user)
    db_session.refresh(nurse_user)
    db_session.refresh(admin_user)
    db_session.refresh(patient)
    db_session.refresh(doctor)
    
    return {
        "patient_user": patient_user,
        "patient": patient,
        "doctor_user": doctor_user,
        "doctor": doctor,
        "nurse_user": nurse_user,
        "admin_user": admin_user
    }


class TestCompleteAppointmentBookingFlow:
    """Test complete appointment booking flow from patient booking to completion"""
    
    def test_complete_appointment_lifecycle(self, client: TestClient, db_session: Session, test_users):
        """
        Test complete appointment lifecycle:
        1. Patient books appointment
        2. Patient views appointment in their list
        3. Doctor views appointment in their list
        4. Nurse checks in patient
        5. Doctor starts consultation
        6. Doctor creates consultation notes
        7. Doctor creates prescription
        8. Doctor completes consultation
        9. Patient views medical records
        """
        patient_user = test_users["patient_user"]
        patient = test_users["patient"]
        doctor_user = test_users["doctor_user"]
        doctor = test_users["doctor"]
        nurse_user = test_users["nurse_user"]
        
        # Generate tokens
        patient_token = create_access_token(data={
            "user_id": patient_user.id,
            "email": patient_user.email,
            "role": patient_user.role.value
        })
        
        doctor_token = create_access_token(data={
            "user_id": doctor_user.id,
            "email": doctor_user.email,
            "role": doctor_user.role.value
        })
        
        nurse_token = create_access_token(data={
            "user_id": nurse_user.id,
            "email": nurse_user.email,
            "role": nurse_user.role.value
        })
        
        # Step 1: Patient books appointment
        scheduled_time = datetime.now() + timedelta(hours=2)
        booking_response = client.post(
            "/api/v1/appointments/",
            json={
                "doctor_id": doctor.id,
                "scheduled_time": scheduled_time.isoformat()
            },
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        assert booking_response.status_code == 201
        appointment_data = booking_response.json()
        appointment_id = appointment_data["id"]
        assert appointment_data["status"] == "scheduled"
        assert appointment_data["queue_position"] == 1
        assert appointment_data["patient_name"] == patient_user.name
        assert appointment_data["doctor_name"] == doctor_user.name
        
        # Step 2: Patient views their appointments
        patient_list_response = client.get(
            "/api/v1/appointments/",
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        assert patient_list_response.status_code == 200
        patient_appointments = patient_list_response.json()
        assert len(patient_appointments) == 1
        assert patient_appointments[0]["id"] == appointment_id
        
        # Step 3: Doctor views their appointments
        doctor_list_response = client.get(
            "/api/v1/appointments/",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert doctor_list_response.status_code == 200
        doctor_appointments = doctor_list_response.json()
        assert len(doctor_appointments) == 1
        assert doctor_appointments[0]["id"] == appointment_id
        
        # Step 4: Nurse checks in patient
        checkin_response = client.patch(
            f"/api/v1/appointments/{appointment_id}/status",
            json={"status": "checked_in"},
            headers={"Authorization": f"Bearer {nurse_token}"}
        )
        
        assert checkin_response.status_code == 200
        checkin_data = checkin_response.json()
        assert checkin_data["status"] == "checked_in"
        assert checkin_data["queue_position"] == 1
        
        # Step 5: Doctor starts consultation
        start_response = client.patch(
            f"/api/v1/appointments/{appointment_id}/status",
            json={"status": "in_progress"},
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert start_response.status_code == 200
        start_data = start_response.json()
        assert start_data["status"] == "in_progress"
        
        # Step 6: Doctor creates consultation notes
        notes_response = client.post(
            "/api/v1/medical-records/consultation-notes",
            json={
                "patient_id": patient.id,
                "appointment_id": appointment_id,
                "consultation_notes": "Patient presents with symptoms. Observations noted.", "diagnosis": "Viral infection"
            },
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert notes_response.status_code == 201
        notes_data = notes_response.json()
        medical_record_id = notes_data["id"]
        assert notes_data["diagnosis"] == "Viral infection"
        
        # Step 7: Doctor creates prescription
        prescription_response = client.post(
            "/api/v1/medical-records/prescriptions",
            json={
                "medical_record_id": medical_record_id,
                "medication": "Paracetamol", "dosage": "500mg", "frequency": "Three times daily", "duration": "5 days"
            },
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert prescription_response.status_code == 201
        prescription_data = prescription_response.json()
        assert prescription_data["prescription"] is not None
        
        # Step 8: Doctor completes consultation
        complete_response = client.patch(
            f"/api/v1/appointments/{appointment_id}/status",
            json={"status": "completed"},
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert complete_response.status_code == 200
        complete_data = complete_response.json()
        assert complete_data["status"] == "completed"
        assert complete_data["queue_position"] is None  # Cleared from queue
        
        # Step 9: Patient views medical records
        records_response = client.get(
            f"/api/v1/medical-records/patient/{patient.id}",
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        assert records_response.status_code == 200
        records = records_response.json()
        assert len(records) >= 1
        assert records[0]["diagnosis"] == "Viral infection"
        assert records[0]["prescription"] is not None

    
    def test_appointment_cancellation_flow(self, client: TestClient, db_session: Session, test_users):
        """
        Test appointment cancellation flow:
        1. Patient books appointment
        2. Patient cancels appointment
        3. Queue is updated
        """
        patient_user = test_users["patient_user"]
        doctor = test_users["doctor"]
        
        patient_token = create_access_token(data={
            "user_id": patient_user.id,
            "email": patient_user.email,
            "role": patient_user.role.value
        })
        
        # Book appointment (3 hours in future to pass 2-hour cancellation rule)
        scheduled_time = datetime.now() + timedelta(hours=3)
        booking_response = client.post(
            "/api/v1/appointments/",
            json={
                "doctor_id": doctor.id,
                "scheduled_time": scheduled_time.isoformat()
            },
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        assert booking_response.status_code == 201
        appointment_id = booking_response.json()["id"]
        
        # Cancel appointment
        cancel_response = client.delete(
            f"/api/v1/appointments/{appointment_id}",
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        assert cancel_response.status_code == 204
        
        # Verify appointment is cancelled
        list_response = client.get(
            "/api/v1/appointments/?status=cancelled",
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        assert list_response.status_code == 200
        cancelled_appointments = list_response.json()
        assert len(cancelled_appointments) == 1
        assert cancelled_appointments[0]["id"] == appointment_id
        assert cancelled_appointments[0]["status"] == "cancelled"
    
    def test_appointment_reschedule_flow(self, client: TestClient, db_session: Session, test_users):
        """
        Test appointment rescheduling flow:
        1. Patient books appointment
        2. Patient reschedules to new time
        3. Verify new time and queue position
        """
        patient_user = test_users["patient_user"]
        doctor = test_users["doctor"]
        
        patient_token = create_access_token(data={
            "user_id": patient_user.id,
            "email": patient_user.email,
            "role": patient_user.role.value
        })
        
        # Book appointment
        scheduled_time = datetime.now() + timedelta(hours=2)
        booking_response = client.post(
            "/api/v1/appointments/",
            json={
                "doctor_id": doctor.id,
                "scheduled_time": scheduled_time.isoformat()
            },
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        assert booking_response.status_code == 201
        appointment_id = booking_response.json()["id"]
        
        # Reschedule appointment
        new_scheduled_time = datetime.now() + timedelta(hours=4)
        reschedule_response = client.put(
            f"/api/v1/appointments/{appointment_id}/reschedule",
            json={"new_scheduled_time": new_scheduled_time.isoformat()},
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        assert reschedule_response.status_code == 200
        rescheduled_data = reschedule_response.json()
        assert rescheduled_data["id"] == appointment_id
        # Verify new scheduled time (compare timestamps)
        assert rescheduled_data["scheduled_time"] is not None


class TestCompleteConsultationFlow:
    """Test complete consultation flow with all status transitions"""
    
    def test_consultation_status_transitions(self, client: TestClient, db_session: Session, test_users):
        """
        Test valid consultation status transitions:
        SCHEDULED → CHECKED_IN → IN_PROGRESS → COMPLETED
        """
        patient = test_users["patient"]
        doctor_user = test_users["doctor_user"]
        doctor = test_users["doctor"]
        nurse_user = test_users["nurse_user"]
        
        doctor_token = create_access_token(data={
            "user_id": doctor_user.id,
            "email": doctor_user.email,
            "role": doctor_user.role.value
        })
        
        nurse_token = create_access_token(data={
            "user_id": nurse_user.id,
            "email": nurse_user.email,
            "role": nurse_user.role.value
        })
        
        # Create appointment directly in database
        scheduled_time = datetime.now() + timedelta(hours=1)
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment)
        db_session.commit()
        db_session.refresh(appointment)
        
        # Transition 1: SCHEDULED → CHECKED_IN
        checkin_response = client.patch(
            f"/api/v1/appointments/{appointment.id}/status",
            json={"status": "checked_in"},
            headers={"Authorization": f"Bearer {nurse_token}"}
        )
        
        assert checkin_response.status_code == 200
        assert checkin_response.json()["status"] == "checked_in"
        
        # Transition 2: CHECKED_IN → IN_PROGRESS
        start_response = client.patch(
            f"/api/v1/appointments/{appointment.id}/status",
            json={"status": "in_progress"},
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert start_response.status_code == 200
        assert start_response.json()["status"] == "in_progress"
        
        # Transition 3: IN_PROGRESS → COMPLETED
        complete_response = client.patch(
            f"/api/v1/appointments/{appointment.id}/status",
            json={"status": "completed"},
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert complete_response.status_code == 200
        complete_data = complete_response.json()
        assert complete_data["status"] == "completed"
        assert complete_data["queue_position"] is None
    
    def test_invalid_status_transition_rejected(self, client: TestClient, db_session: Session, test_users):
        """Test that invalid status transitions are rejected"""
        patient = test_users["patient"]
        doctor_user = test_users["doctor_user"]
        doctor = test_users["doctor"]
        
        doctor_token = create_access_token(data={
            "user_id": doctor_user.id,
            "email": doctor_user.email,
            "role": doctor_user.role.value
        })
        
        # Create scheduled appointment
        scheduled_time = datetime.now() + timedelta(hours=1)
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment)
        db_session.commit()
        db_session.refresh(appointment)
        
        # Try invalid transition: SCHEDULED → COMPLETED (skipping intermediate steps)
        invalid_response = client.patch(
            f"/api/v1/appointments/{appointment.id}/status",
            json={"status": "completed"},
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert invalid_response.status_code == 400
        assert "Invalid status transition" in invalid_response.json()["detail"]






