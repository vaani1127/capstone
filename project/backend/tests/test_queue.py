"""
Tests for queue management endpoints and services
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.appointment import Appointment, AppointmentStatus, AppointmentType
from app.services.appointment_service import AppointmentService
from app.core.security import create_access_token


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def test_patient_user(db_session: Session):
    """Create test patient user"""
    user = User(
        name="Test Patient",
        email="patient@test.com",
        password_hash="$2b$12$test_hash",
        role=UserRole.PATIENT
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_patient(db_session: Session, test_patient_user: User):
    """Create test patient"""
    patient = Patient(
        user_id=test_patient_user.id,
        phone="1234567890",
        gender="Male"
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)
    return patient


@pytest.fixture
def test_patient2(db_session: Session):
    """Create second test patient"""
    user = User(
        name="Test Patient 2",
        email="patient2@test.com",
        password_hash="$2b$12$test_hash",
        role=UserRole.PATIENT
    )
    db_session.add(user)
    db_session.flush()
    
    patient = Patient(
        user_id=user.id,
        phone="0987654321",
        gender="Female"
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)
    return patient


@pytest.fixture
def test_doctor_user(db_session: Session):
    """Create test doctor user"""
    user = User(
        name="Dr. Test",
        email="doctor@test.com",
        password_hash="$2b$12$test_hash",
        role=UserRole.DOCTOR
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_doctor(db_session: Session, test_doctor_user: User):
    """Create test doctor"""
    doctor = Doctor(
        user_id=test_doctor_user.id,
        specialization="Cardiology",
        license_number="DOC123",
        average_consultation_duration=15
    )
    db_session.add(doctor)
    db_session.commit()
    db_session.refresh(doctor)
    return doctor


@pytest.fixture
def test_doctor2(db_session: Session):
    """Create second test doctor"""
    user = User(
        name="Dr. Test 2",
        email="doctor2@test.com",
        password_hash="$2b$12$test_hash",
        role=UserRole.DOCTOR
    )
    db_session.add(user)
    db_session.flush()
    
    doctor = Doctor(
        user_id=user.id,
        specialization="Neurology",
        license_number="DOC456",
        average_consultation_duration=20
    )
    db_session.add(doctor)
    db_session.commit()
    db_session.refresh(doctor)
    return doctor


@pytest.fixture
def test_nurse_user(db_session: Session):
    """Create test nurse user"""
    user = User(
        name="Test Nurse",
        email="nurse@test.com",
        password_hash="$2b$12$test_hash",
        role=UserRole.NURSE
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin_user(db_session: Session):
    """Create test admin user"""
    user = User(
        name="Test Admin",
        email="admin@test.com",
        password_hash="$2b$12$test_hash",
        role=UserRole.ADMIN
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestQueueService:
    """Test queue service methods"""
    
    def test_get_doctor_queue_empty(self, db_session: Session, test_doctor: Doctor):
        """Test getting queue for doctor with no appointments"""
        queue_data = AppointmentService.get_doctor_queue(db=db_session, doctor_id=test_doctor.id)
        
        assert queue_data["doctor_id"] == test_doctor.id
        assert queue_data["total_queue_length"] == 0
        assert len(queue_data["patients"]) == 0
        assert queue_data["average_consultation_duration"] == test_doctor.average_consultation_duration
    
    def test_get_doctor_queue_with_patients(
        self, 
        db_session: Session, 
        test_doctor: Doctor,
        test_patient: Patient,
        test_patient2: Patient
    ):
        """Test getting queue with multiple patients"""
        # Create appointments in queue
        scheduled_time = datetime.now() + timedelta(hours=1)
        
        # First appointment
        appointment1 = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.CHECKED_IN,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment1)
        
        # Second appointment
        appointment2 = Appointment(
            patient_id=test_patient2.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time + timedelta(minutes=30),
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=2
        )
        db_session.add(appointment2)
        db_session.commit()
        
        # Get queue
        queue_data = AppointmentService.get_doctor_queue(db=db_session, doctor_id=test_doctor.id)
        
        assert queue_data["total_queue_length"] == 2
        assert len(queue_data["patients"]) == 2
        
        # Check first patient
        patient1 = queue_data["patients"][0]
        assert patient1["queue_position"] == 1
        assert patient1["patient_id"] == test_patient.id
        assert patient1["estimated_wait_time"] == 0  # First in queue
        
        # Check second patient
        patient2 = queue_data["patients"][1]
        assert patient2["queue_position"] == 2
        assert patient2["patient_id"] == test_patient2.id
        assert patient2["estimated_wait_time"] == test_doctor.average_consultation_duration
    
    def test_get_doctor_queue_excludes_completed(
        self,
        db_session: Session,
        test_doctor: Doctor,
        test_patient: Patient
    ):
        """Test that completed appointments are not in queue"""
        scheduled_time = datetime.now() + timedelta(hours=1)
        
        # Create completed appointment
        appointment = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.COMPLETED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=None
        )
        db_session.add(appointment)
        db_session.commit()
        
        # Get queue
        queue_data = AppointmentService.get_doctor_queue(db=db_session, doctor_id=test_doctor.id)
        
        assert queue_data["total_queue_length"] == 0
        assert len(queue_data["patients"]) == 0
    
    def test_get_doctor_queue_excludes_cancelled(
        self,
        db_session: Session,
        test_doctor: Doctor,
        test_patient: Patient
    ):
        """Test that cancelled appointments are not in queue"""
        scheduled_time = datetime.now() + timedelta(hours=1)
        
        # Create cancelled appointment
        appointment = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.CANCELLED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=None
        )
        db_session.add(appointment)
        db_session.commit()
        
        # Get queue
        queue_data = AppointmentService.get_doctor_queue(db=db_session, doctor_id=test_doctor.id)
        
        assert queue_data["total_queue_length"] == 0
        assert len(queue_data["patients"]) == 0
    
    def test_get_doctor_queue_sorted_by_position(
        self,
        db_session: Session,
        test_doctor: Doctor,
        test_patient: Patient,
        test_patient2: Patient
    ):
        """Test that queue is sorted by queue_position"""
        scheduled_time = datetime.now() + timedelta(hours=1)
        
        # Create appointments out of order
        appointment2 = Appointment(
            patient_id=test_patient2.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time + timedelta(minutes=30),
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=2
        )
        db_session.add(appointment2)
        
        appointment1 = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.CHECKED_IN,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment1)
        db_session.commit()
        
        # Get queue
        queue_data = AppointmentService.get_doctor_queue(db=db_session, doctor_id=test_doctor.id)
        
        # Verify order
        assert queue_data["patients"][0]["queue_position"] == 1
        assert queue_data["patients"][1]["queue_position"] == 2
    
    def test_get_doctor_queue_nonexistent_doctor(self, db_session: Session):
        """Test getting queue for non-existent doctor raises error"""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            AppointmentService.get_doctor_queue(db=db_session, doctor_id=99999)
        
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()
    
    def test_get_all_queues_status(
        self,
        db_session: Session,
        test_doctor: Doctor,
        test_doctor2: Doctor,
        test_patient: Patient
    ):
        """Test getting queue status for all doctors"""
        scheduled_time = datetime.now() + timedelta(hours=1)
        
        # Create appointment for first doctor
        appointment = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment)
        db_session.commit()
        
        # Get all queues
        queue_summaries = AppointmentService.get_all_queues_status(db=db_session)
        
        # Should have summaries for both doctors
        assert len(queue_summaries) >= 2
        
        # Find our test doctors
        doctor1_summary = next((s for s in queue_summaries if s["doctor_id"] == test_doctor.id), None)
        doctor2_summary = next((s for s in queue_summaries if s["doctor_id"] == test_doctor2.id), None)
        
        assert doctor1_summary is not None
        assert doctor1_summary["queue_length"] == 1
        assert doctor1_summary["average_wait_time"] > 0
        
        assert doctor2_summary is not None
        assert doctor2_summary["queue_length"] == 0
        assert doctor2_summary["average_wait_time"] == 0


class TestQueueEndpoints:
    """Test queue API endpoints"""
    
    def test_get_queue_status_requires_auth(self, client: TestClient):
        """Test that queue status endpoint requires authentication"""
        response = client.get("/api/v1/queue/status")
        assert response.status_code == 401
    
    def test_get_queue_status_success(
        self,
        client: TestClient,
        db_session: Session,
        test_patient_user: User,
        test_doctor: Doctor
    ):
        """Test getting queue status for all doctors"""
        # Create access token
        token = create_access_token(data={
            "sub": test_patient_user.email,
            "user_id": test_patient_user.id,
            "email": test_patient_user.email
        })
        
        # Get queue status
        response = client.get(
            "/api/v1/queue/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Should have at least one doctor
        assert len(data) > 0
        
        # Check structure
        for summary in data:
            assert "doctor_id" in summary
            assert "doctor_name" in summary
            assert "doctor_specialization" in summary
            assert "queue_length" in summary
            assert "average_wait_time" in summary
    
    def test_get_doctor_queue_requires_auth(self, client: TestClient, test_doctor: Doctor):
        """Test that doctor queue endpoint requires authentication"""
        response = client.get(f"/api/v1/queue/doctor/{test_doctor.id}")
        assert response.status_code == 401
    
    def test_get_doctor_queue_success(
        self,
        client: TestClient,
        db_session: Session,
        test_patient_user: User,
        test_doctor: Doctor,
        test_patient: Patient
    ):
        """Test getting queue for specific doctor"""
        # Create appointment
        scheduled_time = datetime.now() + timedelta(hours=1)
        appointment = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.CHECKED_IN,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment)
        db_session.commit()
        
        # Create access token
        token = create_access_token(data={
            "sub": test_patient_user.email,
            "user_id": test_patient_user.id,
            "email": test_patient_user.email
        })
        
        # Get doctor queue
        response = client.get(
            f"/api/v1/queue/doctor/{test_doctor.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert data["doctor_id"] == test_doctor.id
        assert "doctor_name" in data
        assert "doctor_specialization" in data
        assert data["average_consultation_duration"] == test_doctor.average_consultation_duration
        assert data["total_queue_length"] == 1
        assert len(data["patients"]) == 1
        
        # Check patient data
        patient_data = data["patients"][0]
        assert patient_data["patient_id"] == test_patient.id
        assert patient_data["queue_position"] == 1
        assert "patient_name" in patient_data
        assert "estimated_wait_time" in patient_data
        assert patient_data["status"] == AppointmentStatus.CHECKED_IN.value
    
    def test_get_doctor_queue_nonexistent(
        self,
        client: TestClient,
        test_patient_user: User
    ):
        """Test getting queue for non-existent doctor"""
        token = create_access_token(data={
            "sub": test_patient_user.email,
            "user_id": test_patient_user.id,
            "email": test_patient_user.email
        })
        
        response = client.get(
            "/api/v1/queue/doctor/99999",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404
    
    def test_get_doctor_queue_accessible_by_all_roles(
        self,
        client: TestClient,
        db_session: Session,
        test_doctor: Doctor,
        test_doctor_user: User,
        test_nurse_user: User,
        test_admin_user: User,
        test_patient_user: User
    ):
        """Test that all authenticated users can access queue"""
        users = [test_doctor_user, test_nurse_user, test_admin_user, test_patient_user]
        
        for user in users:
            token = create_access_token(data={
                "sub": user.email,
                "user_id": user.id,
                "email": user.email
            })
            
            response = client.get(
                f"/api/v1/queue/doctor/{test_doctor.id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200, f"Failed for role: {user.role}"



class TestQueueUpdates:
    """Test queue updates when appointment status changes"""
    
    def test_update_status_checked_in(
        self,
        client: TestClient,
        db_session: Session,
        test_doctor_user: User,
        test_doctor: Doctor,
        test_patient: Patient
    ):
        """Test updating appointment status to CHECKED_IN"""
        # Create scheduled appointment
        scheduled_time = datetime.now() + timedelta(hours=1)
        appointment = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment)
        db_session.commit()
        
        # Create access token for doctor
        token = create_access_token(data={
            "sub": test_doctor_user.email,
            "user_id": test_doctor_user.id,
            "email": test_doctor_user.email
        })
        
        # Update status to CHECKED_IN
        response = client.patch(
            f"/api/v1/appointments/{appointment.id}/status",
            json={"status": "checked_in"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "checked_in"
        assert data["queue_position"] == 1  # Still in queue
    
    def test_update_status_in_progress(
        self,
        client: TestClient,
        db_session: Session,
        test_doctor_user: User,
        test_doctor: Doctor,
        test_patient: Patient
    ):
        """Test updating appointment status to IN_PROGRESS"""
        # Create checked-in appointment
        scheduled_time = datetime.now() + timedelta(hours=1)
        appointment = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.CHECKED_IN,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment)
        db_session.commit()
        
        # Create access token for doctor
        token = create_access_token(data={
            "sub": test_doctor_user.email,
            "user_id": test_doctor_user.id,
            "email": test_doctor_user.email
        })
        
        # Update status to IN_PROGRESS
        response = client.patch(
            f"/api/v1/appointments/{appointment.id}/status",
            json={"status": "in_progress"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["queue_position"] == 1  # Still in queue
    
    def test_update_status_completed_clears_queue_position(
        self,
        client: TestClient,
        db_session: Session,
        test_doctor_user: User,
        test_doctor: Doctor,
        test_patient: Patient
    ):
        """Test that completing appointment clears queue position"""
        # Create in-progress appointment
        scheduled_time = datetime.now() + timedelta(hours=1)
        appointment = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.IN_PROGRESS,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment)
        db_session.commit()
        
        # Create access token for doctor
        token = create_access_token(data={
            "sub": test_doctor_user.email,
            "user_id": test_doctor_user.id,
            "email": test_doctor_user.email
        })
        
        # Update status to COMPLETED
        response = client.patch(
            f"/api/v1/appointments/{appointment.id}/status",
            json={"status": "completed"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["queue_position"] is None  # Queue position cleared
    
    def test_update_status_completed_recalculates_queue(
        self,
        client: TestClient,
        db_session: Session,
        test_doctor_user: User,
        test_doctor: Doctor,
        test_patient: Patient,
        test_patient2: Patient
    ):
        """Test that completing appointment recalculates queue positions"""
        scheduled_time = datetime.now() + timedelta(hours=1)
        
        # Create first appointment (in progress)
        appointment1 = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.IN_PROGRESS,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment1)
        
        # Create second appointment (waiting)
        appointment2 = Appointment(
            patient_id=test_patient2.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time + timedelta(minutes=30),
            status=AppointmentStatus.CHECKED_IN,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=2
        )
        db_session.add(appointment2)
        db_session.commit()
        
        # Create access token for doctor
        token = create_access_token(data={
            "sub": test_doctor_user.email,
            "user_id": test_doctor_user.id,
            "email": test_doctor_user.email
        })
        
        # Complete first appointment
        response = client.patch(
            f"/api/v1/appointments/{appointment1.id}/status",
            json={"status": "completed"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        
        # Verify second appointment moved up in queue
        db_session.refresh(appointment2)
        assert appointment2.queue_position == 1  # Moved from position 2 to 1
    
    def test_update_status_invalid_transition(
        self,
        client: TestClient,
        db_session: Session,
        test_doctor_user: User,
        test_doctor: Doctor,
        test_patient: Patient
    ):
        """Test that invalid status transitions are rejected"""
        # Create scheduled appointment
        scheduled_time = datetime.now() + timedelta(hours=1)
        appointment = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment)
        db_session.commit()
        
        # Create access token for doctor
        token = create_access_token(data={
            "sub": test_doctor_user.email,
            "user_id": test_doctor_user.id,
            "email": test_doctor_user.email
        })
        
        # Try to jump directly to COMPLETED (invalid)
        response = client.patch(
            f"/api/v1/appointments/{appointment.id}/status",
            json={"status": "completed"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert "Invalid status transition" in response.json()["detail"]
    
    def test_update_status_requires_staff_role(
        self,
        client: TestClient,
        db_session: Session,
        test_patient_user: User,
        test_doctor: Doctor,
        test_patient: Patient
    ):
        """Test that only staff can update appointment status"""
        # Create scheduled appointment
        scheduled_time = datetime.now() + timedelta(hours=1)
        appointment = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment)
        db_session.commit()
        
        # Create access token for patient
        token = create_access_token(data={
            "sub": test_patient_user.email,
            "user_id": test_patient_user.id,
            "email": test_patient_user.email
        })
        
        # Try to update status as patient
        response = client.patch(
            f"/api/v1/appointments/{appointment.id}/status",
            json={"status": "checked_in"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        assert "Only doctors and staff" in response.json()["detail"]
    
    def test_update_status_nurse_can_update(
        self,
        client: TestClient,
        db_session: Session,
        test_nurse_user: User,
        test_doctor: Doctor,
        test_patient: Patient
    ):
        """Test that nurses can update appointment status"""
        # Create scheduled appointment
        scheduled_time = datetime.now() + timedelta(hours=1)
        appointment = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment)
        db_session.commit()
        
        # Create access token for nurse
        token = create_access_token(data={
            "sub": test_nurse_user.email,
            "user_id": test_nurse_user.id,
            "email": test_nurse_user.email
        })
        
        # Update status as nurse
        response = client.patch(
            f"/api/v1/appointments/{appointment.id}/status",
            json={"status": "checked_in"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "checked_in"
    
    def test_update_status_admin_can_update(
        self,
        client: TestClient,
        db_session: Session,
        test_admin_user: User,
        test_doctor: Doctor,
        test_patient: Patient
    ):
        """Test that admins can update appointment status"""
        # Create scheduled appointment
        scheduled_time = datetime.now() + timedelta(hours=1)
        appointment = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment)
        db_session.commit()
        
        # Create access token for admin
        token = create_access_token(data={
            "sub": test_admin_user.email,
            "user_id": test_admin_user.id,
            "email": test_admin_user.email
        })
        
        # Update status as admin
        response = client.patch(
            f"/api/v1/appointments/{appointment.id}/status",
            json={"status": "checked_in"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "checked_in"
    
    def test_update_status_nonexistent_appointment(
        self,
        client: TestClient,
        test_doctor_user: User
    ):
        """Test updating status of non-existent appointment"""
        token = create_access_token(data={
            "sub": test_doctor_user.email,
            "user_id": test_doctor_user.id,
            "email": test_doctor_user.email
        })
        
        response = client.patch(
            "/api/v1/appointments/99999/status",
            json={"status": "checked_in"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404
    
    def test_update_status_requires_auth(self, client: TestClient):
        """Test that status update requires authentication"""
        response = client.patch(
            "/api/v1/appointments/1/status",
            json={"status": "checked_in"}
        )
        
        assert response.status_code == 401
    
    def test_complete_multiple_appointments_queue_updates(
        self,
        client: TestClient,
        db_session: Session,
        test_doctor_user: User,
        test_doctor: Doctor,
        test_patient: Patient,
        test_patient2: Patient
    ):
        """Test completing multiple appointments updates queue correctly"""
        scheduled_time = datetime.now() + timedelta(hours=1)
        
        # Create third patient
        user3 = User(
            name="Test Patient 3",
            email="patient3@test.com",
            password_hash="$2b$12$test_hash",
            role=UserRole.PATIENT
        )
        db_session.add(user3)
        db_session.flush()
        
        patient3 = Patient(
            user_id=user3.id,
            phone="1112223333",
            gender="Male"
        )
        db_session.add(patient3)
        db_session.flush()
        
        # Create three appointments
        appointment1 = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.IN_PROGRESS,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment1)
        
        appointment2 = Appointment(
            patient_id=test_patient2.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time + timedelta(minutes=30),
            status=AppointmentStatus.CHECKED_IN,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=2
        )
        db_session.add(appointment2)
        
        appointment3 = Appointment(
            patient_id=patient3.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time + timedelta(hours=1),
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=3
        )
        db_session.add(appointment3)
        db_session.commit()
        
        # Create access token for doctor
        token = create_access_token(data={
            "sub": test_doctor_user.email,
            "user_id": test_doctor_user.id,
            "email": test_doctor_user.email
        })
        
        # Complete first appointment
        response = client.patch(
            f"/api/v1/appointments/{appointment1.id}/status",
            json={"status": "completed"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        # Verify queue positions updated
        db_session.refresh(appointment2)
        db_session.refresh(appointment3)
        assert appointment2.queue_position == 1  # Moved from 2 to 1
        assert appointment3.queue_position == 2  # Moved from 3 to 2
        
        # Complete second appointment
        # First transition to IN_PROGRESS
        response = client.patch(
            f"/api/v1/appointments/{appointment2.id}/status",
            json={"status": "in_progress"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        # Then complete
        response = client.patch(
            f"/api/v1/appointments/{appointment2.id}/status",
            json={"status": "completed"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        # Verify final queue position
        db_session.refresh(appointment3)
        assert appointment3.queue_position == 1  # Now first in queue



class TestQueuePositionCalculation:
    """Test queue position calculation logic"""
    
    def test_get_next_queue_position_empty_queue(
        self,
        db_session: Session,
        test_doctor: Doctor
    ):
        """Test getting next queue position when queue is empty"""
        next_position = AppointmentService.get_next_queue_position(
            db=db_session,
            doctor_id=test_doctor.id
        )
        
        assert next_position == 1
    
    def test_get_next_queue_position_with_existing_appointments(
        self,
        db_session: Session,
        test_doctor: Doctor,
        test_patient: Patient,
        test_patient2: Patient
    ):
        """Test getting next queue position with existing appointments"""
        scheduled_time = datetime.now() + timedelta(hours=1)
        
        # Create two appointments
        appointment1 = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment1)
        
        appointment2 = Appointment(
            patient_id=test_patient2.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time + timedelta(minutes=30),
            status=AppointmentStatus.CHECKED_IN,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=2
        )
        db_session.add(appointment2)
        db_session.commit()
        
        # Get next position
        next_position = AppointmentService.get_next_queue_position(
            db=db_session,
            doctor_id=test_doctor.id
        )
        
        assert next_position == 3
    
    def test_get_next_queue_position_ignores_completed(
        self,
        db_session: Session,
        test_doctor: Doctor,
        test_patient: Patient
    ):
        """Test that completed appointments don't affect next queue position"""
        scheduled_time = datetime.now() + timedelta(hours=1)
        
        # Create completed appointment with no queue position
        appointment1 = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.COMPLETED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=None
        )
        db_session.add(appointment1)
        db_session.commit()
        
        # Get next position - should be 1 since completed appointments are ignored
        next_position = AppointmentService.get_next_queue_position(
            db=db_session,
            doctor_id=test_doctor.id
        )
        
        assert next_position == 1
    
    def test_get_next_queue_position_ignores_cancelled(
        self,
        db_session: Session,
        test_doctor: Doctor,
        test_patient: Patient
    ):
        """Test that cancelled appointments don't affect next queue position"""
        scheduled_time = datetime.now() + timedelta(hours=1)
        
        # Create cancelled appointment
        appointment1 = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.CANCELLED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=None
        )
        db_session.add(appointment1)
        db_session.commit()
        
        # Get next position - should be 1 since cancelled appointments are ignored
        next_position = AppointmentService.get_next_queue_position(
            db=db_session,
            doctor_id=test_doctor.id
        )
        
        assert next_position == 1
    
    def test_queue_position_assigned_on_appointment_creation(
        self,
        db_session: Session,
        test_doctor: Doctor,
        test_patient: Patient
    ):
        """Test that queue position is automatically assigned when creating appointment"""
        from app.schemas.appointment import AppointmentCreate
        
        scheduled_time = datetime.now() + timedelta(hours=1)
        appointment_data = AppointmentCreate(
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time
        )
        
        # Create appointment
        appointment = AppointmentService.create_appointment(
            db=db_session,
            patient_id=test_patient.id,
            appointment_data=appointment_data
        )
        
        assert appointment.queue_position == 1
    
    def test_queue_position_increments_correctly(
        self,
        db_session: Session,
        test_doctor: Doctor,
        test_patient: Patient,
        test_patient2: Patient
    ):
        """Test that queue positions increment correctly for multiple appointments"""
        from app.schemas.appointment import AppointmentCreate
        
        scheduled_time = datetime.now() + timedelta(hours=1)
        
        # Create first appointment
        appointment_data1 = AppointmentCreate(
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time
        )
        appointment1 = AppointmentService.create_appointment(
            db=db_session,
            patient_id=test_patient.id,
            appointment_data=appointment_data1
        )
        
        # Create second appointment
        appointment_data2 = AppointmentCreate(
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time + timedelta(minutes=30)
        )
        appointment2 = AppointmentService.create_appointment(
            db=db_session,
            patient_id=test_patient2.id,
            appointment_data=appointment_data2
        )
        
        assert appointment1.queue_position == 1
        assert appointment2.queue_position == 2
    
    def test_queue_position_recalculation_after_completion(
        self,
        db_session: Session,
        test_doctor_user: User,
        test_doctor: Doctor,
        test_patient: Patient,
        test_patient2: Patient
    ):
        """Test that queue positions are recalculated when an appointment is completed"""
        scheduled_time = datetime.now() + timedelta(hours=1)
        
        # Create two appointments
        appointment1 = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.IN_PROGRESS,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1,
            consultation_start_time=datetime.now()
        )
        db_session.add(appointment1)
        
        appointment2 = Appointment(
            patient_id=test_patient2.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time + timedelta(minutes=30),
            status=AppointmentStatus.CHECKED_IN,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=2
        )
        db_session.add(appointment2)
        db_session.commit()
        
        # Complete first appointment
        AppointmentService.update_appointment_status(
            db=db_session,
            appointment_id=appointment1.id,
            new_status=AppointmentStatus.COMPLETED,
            user_id=test_doctor_user.id,
            user_role=test_doctor_user.role.value
        )
        
        # Verify second appointment moved to position 1
        db_session.refresh(appointment2)
        assert appointment2.queue_position == 1
        
        # Verify first appointment has no queue position
        db_session.refresh(appointment1)
        assert appointment1.queue_position is None


class TestWaitingTimeCalculation:
    """Test waiting time calculation logic"""
    
    def test_calculate_estimated_wait_time_first_position(
        self,
        db_session: Session,
        test_doctor: Doctor
    ):
        """Test that first position has zero wait time"""
        wait_time = AppointmentService.calculate_estimated_wait_time(
            db=db_session,
            doctor_id=test_doctor.id,
            queue_position=1
        )
        
        assert wait_time == 0
    
    def test_calculate_estimated_wait_time_second_position(
        self,
        db_session: Session,
        test_doctor: Doctor
    ):
        """Test wait time calculation for second position"""
        # Doctor has average_consultation_duration of 15 minutes
        wait_time = AppointmentService.calculate_estimated_wait_time(
            db=db_session,
            doctor_id=test_doctor.id,
            queue_position=2
        )
        
        # Position 2 means 1 person ahead, so wait time = 1 * 15 = 15 minutes
        assert wait_time == 15
    
    def test_calculate_estimated_wait_time_multiple_positions(
        self,
        db_session: Session,
        test_doctor: Doctor
    ):
        """Test wait time calculation for various queue positions"""
        # Doctor has average_consultation_duration of 15 minutes
        
        # Position 3: 2 people ahead = 2 * 15 = 30 minutes
        wait_time_3 = AppointmentService.calculate_estimated_wait_time(
            db=db_session,
            doctor_id=test_doctor.id,
            queue_position=3
        )
        assert wait_time_3 == 30
        
        # Position 5: 4 people ahead = 4 * 15 = 60 minutes
        wait_time_5 = AppointmentService.calculate_estimated_wait_time(
            db=db_session,
            doctor_id=test_doctor.id,
            queue_position=5
        )
        assert wait_time_5 == 60
        
        # Position 10: 9 people ahead = 9 * 15 = 135 minutes
        wait_time_10 = AppointmentService.calculate_estimated_wait_time(
            db=db_session,
            doctor_id=test_doctor.id,
            queue_position=10
        )
        assert wait_time_10 == 135
    
    def test_calculate_estimated_wait_time_with_different_doctor_duration(
        self,
        db_session: Session,
        test_doctor2: Doctor
    ):
        """Test wait time calculation with different average consultation duration"""
        # test_doctor2 has average_consultation_duration of 20 minutes
        
        # Position 2: 1 person ahead = 1 * 20 = 20 minutes
        wait_time = AppointmentService.calculate_estimated_wait_time(
            db=db_session,
            doctor_id=test_doctor2.id,
            queue_position=2
        )
        
        assert wait_time == 20
    
    def test_calculate_estimated_wait_time_nonexistent_doctor(
        self,
        db_session: Session
    ):
        """Test wait time calculation for non-existent doctor returns 0"""
        wait_time = AppointmentService.calculate_estimated_wait_time(
            db=db_session,
            doctor_id=99999,
            queue_position=5
        )
        
        assert wait_time == 0
    
    def test_wait_time_in_queue_response(
        self,
        db_session: Session,
        test_doctor: Doctor,
        test_patient: Patient,
        test_patient2: Patient
    ):
        """Test that wait times are correctly included in queue response"""
        scheduled_time = datetime.now() + timedelta(hours=1)
        
        # Create three appointments
        appointment1 = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.IN_PROGRESS,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment1)
        
        appointment2 = Appointment(
            patient_id=test_patient2.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time + timedelta(minutes=30),
            status=AppointmentStatus.CHECKED_IN,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=2
        )
        db_session.add(appointment2)
        db_session.commit()
        
        # Get queue
        queue_data = AppointmentService.get_doctor_queue(
            db=db_session,
            doctor_id=test_doctor.id
        )
        
        # Verify wait times
        assert queue_data["patients"][0]["estimated_wait_time"] == 0  # Position 1
        assert queue_data["patients"][1]["estimated_wait_time"] == 15  # Position 2
    
    def test_wait_time_updates_after_queue_position_change(
        self,
        db_session: Session,
        test_doctor_user: User,
        test_doctor: Doctor,
        test_patient: Patient,
        test_patient2: Patient
    ):
        """Test that wait times update correctly when queue positions change"""
        scheduled_time = datetime.now() + timedelta(hours=1)
        
        # Create two appointments
        appointment1 = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.IN_PROGRESS,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1,
            consultation_start_time=datetime.now()
        )
        db_session.add(appointment1)
        
        appointment2 = Appointment(
            patient_id=test_patient2.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time + timedelta(minutes=30),
            status=AppointmentStatus.CHECKED_IN,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=2
        )
        db_session.add(appointment2)
        db_session.commit()
        
        # Initial wait time for appointment2 is 15 minutes (position 2)
        queue_data = AppointmentService.get_doctor_queue(
            db=db_session,
            doctor_id=test_doctor.id
        )
        patient2_data = next(p for p in queue_data["patients"] if p["patient_id"] == test_patient2.id)
        assert patient2_data["estimated_wait_time"] == 15
        
        # Complete first appointment
        AppointmentService.update_appointment_status(
            db=db_session,
            appointment_id=appointment1.id,
            new_status=AppointmentStatus.COMPLETED,
            user_id=test_doctor_user.id,
            user_role=test_doctor_user.role.value
        )
        
        # Wait time for appointment2 should now be 0 (moved to position 1)
        queue_data = AppointmentService.get_doctor_queue(
            db=db_session,
            doctor_id=test_doctor.id
        )
        patient2_data = next(p for p in queue_data["patients"] if p["patient_id"] == test_patient2.id)
        assert patient2_data["estimated_wait_time"] == 0


class TestConsultationDurationTracking:
    """Test consultation duration tracking and average calculation"""
    
    def test_consultation_start_time_set_on_in_progress(
        self,
        db_session: Session,
        test_doctor_user: User,
        test_doctor: Doctor,
        test_patient: Patient
    ):
        """Test that consultation_start_time is set when status changes to IN_PROGRESS"""
        # Create checked-in appointment
        scheduled_time = datetime.now() + timedelta(hours=1)
        appointment = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.CHECKED_IN,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment)
        db_session.commit()
        
        # Verify consultation_start_time is None initially
        assert appointment.consultation_start_time is None
        
        # Update status to IN_PROGRESS
        before_update = datetime.now()
        updated_appointment = AppointmentService.update_appointment_status(
            db=db_session,
            appointment_id=appointment.id,
            new_status=AppointmentStatus.IN_PROGRESS,
            user_id=test_doctor_user.id,
            user_role=test_doctor_user.role.value
        )
        after_update = datetime.now()
        
        # Verify consultation_start_time is set
        assert updated_appointment.consultation_start_time is not None
        assert before_update <= updated_appointment.consultation_start_time <= after_update
    
    def test_average_consultation_duration_updated_on_completion(
        self,
        db_session: Session,
        test_doctor_user: User,
        test_doctor: Doctor,
        test_patient: Patient
    ):
        """Test that doctor's average consultation duration is updated when appointment completes"""
        # Store initial average
        initial_average = test_doctor.average_consultation_duration  # 15 minutes
        
        # Create in-progress appointment with consultation_start_time
        scheduled_time = datetime.now() + timedelta(hours=1)
        consultation_start = datetime.now() - timedelta(minutes=20)  # Started 20 minutes ago
        appointment = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.IN_PROGRESS,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1,
            consultation_start_time=consultation_start
        )
        db_session.add(appointment)
        db_session.commit()
        
        # Complete the appointment
        AppointmentService.update_appointment_status(
            db=db_session,
            appointment_id=appointment.id,
            new_status=AppointmentStatus.COMPLETED,
            user_id=test_doctor_user.id,
            user_role=test_doctor_user.role.value
        )
        
        # Refresh doctor to get updated average
        db_session.refresh(test_doctor)
        
        # Verify average was updated
        # EMA formula: new_average = (0.2 * 20) + (0.8 * 15) = 4 + 12 = 16
        expected_average = int(round((0.2 * 20) + (0.8 * initial_average)))
        assert test_doctor.average_consultation_duration == expected_average
        assert test_doctor.average_consultation_duration != initial_average
    
    def test_average_consultation_duration_ema_calculation(
        self,
        db_session: Session,
        test_doctor: Doctor
    ):
        """Test EMA calculation for average consultation duration"""
        # Initial average is 15 minutes
        initial_average = 15
        test_doctor.average_consultation_duration = initial_average
        db_session.commit()
        
        # Test with actual duration of 30 minutes
        actual_duration = 30
        AppointmentService.update_average_consultation_duration(
            db=db_session,
            doctor_id=test_doctor.id,
            actual_duration=actual_duration
        )
        
        # Refresh doctor
        db_session.refresh(test_doctor)
        
        # EMA formula: new_average = (0.2 * 30) + (0.8 * 15) = 6 + 12 = 18
        expected_average = int(round((0.2 * actual_duration) + (0.8 * initial_average)))
        assert test_doctor.average_consultation_duration == expected_average
        assert test_doctor.average_consultation_duration == 18
    
    def test_average_consultation_duration_multiple_updates(
        self,
        db_session: Session,
        test_doctor: Doctor
    ):
        """Test that average consultation duration updates correctly over multiple consultations"""
        # Start with 15 minutes average
        test_doctor.average_consultation_duration = 15
        db_session.commit()
        
        # First consultation: 20 minutes
        AppointmentService.update_average_consultation_duration(
            db=db_session,
            doctor_id=test_doctor.id,
            actual_duration=20
        )
        db_session.refresh(test_doctor)
        # new_avg = (0.2 * 20) + (0.8 * 15) = 4 + 12 = 16
        assert test_doctor.average_consultation_duration == 16
        
        # Second consultation: 10 minutes
        AppointmentService.update_average_consultation_duration(
            db=db_session,
            doctor_id=test_doctor.id,
            actual_duration=10
        )
        db_session.refresh(test_doctor)
        # new_avg = (0.2 * 10) + (0.8 * 16) = 2 + 12.8 = 14.8 ≈ 15
        assert test_doctor.average_consultation_duration == 15
        
        # Third consultation: 25 minutes
        AppointmentService.update_average_consultation_duration(
            db=db_session,
            doctor_id=test_doctor.id,
            actual_duration=25
        )
        db_session.refresh(test_doctor)
        # new_avg = (0.2 * 25) + (0.8 * 15) = 5 + 12 = 17
        assert test_doctor.average_consultation_duration == 17
    
    def test_average_not_updated_without_consultation_start_time(
        self,
        db_session: Session,
        test_doctor_user: User,
        test_doctor: Doctor,
        test_patient: Patient
    ):
        """Test that average is not updated if consultation_start_time is missing"""
        # Store initial average
        initial_average = test_doctor.average_consultation_duration
        
        # Create in-progress appointment WITHOUT consultation_start_time
        scheduled_time = datetime.now() + timedelta(hours=1)
        appointment = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.IN_PROGRESS,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1,
            consultation_start_time=None  # Explicitly None
        )
        db_session.add(appointment)
        db_session.commit()
        
        # Complete the appointment
        AppointmentService.update_appointment_status(
            db=db_session,
            appointment_id=appointment.id,
            new_status=AppointmentStatus.COMPLETED,
            user_id=test_doctor_user.id,
            user_role=test_doctor_user.role.value
        )
        
        # Refresh doctor
        db_session.refresh(test_doctor)
        
        # Verify average was NOT updated
        assert test_doctor.average_consultation_duration == initial_average
    
    def test_consultation_duration_with_short_consultation(
        self,
        db_session: Session,
        test_doctor_user: User,
        test_doctor: Doctor,
        test_patient: Patient
    ):
        """Test consultation duration tracking with a very short consultation"""
        # Create in-progress appointment with consultation_start_time 5 minutes ago
        scheduled_time = datetime.now() + timedelta(hours=1)
        consultation_start = datetime.now() - timedelta(minutes=5)
        appointment = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.IN_PROGRESS,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1,
            consultation_start_time=consultation_start
        )
        db_session.add(appointment)
        db_session.commit()
        
        initial_average = test_doctor.average_consultation_duration  # 15
        
        # Complete the appointment
        AppointmentService.update_appointment_status(
            db=db_session,
            appointment_id=appointment.id,
            new_status=AppointmentStatus.COMPLETED,
            user_id=test_doctor_user.id,
            user_role=test_doctor_user.role.value
        )
        
        # Refresh doctor
        db_session.refresh(test_doctor)
        
        # EMA formula: new_average = (0.2 * 5) + (0.8 * 15) = 1 + 12 = 13
        expected_average = int(round((0.2 * 5) + (0.8 * initial_average)))
        assert test_doctor.average_consultation_duration == expected_average
    
    def test_consultation_duration_with_long_consultation(
        self,
        db_session: Session,
        test_doctor_user: User,
        test_doctor: Doctor,
        test_patient: Patient
    ):
        """Test consultation duration tracking with a very long consultation"""
        # Create in-progress appointment with consultation_start_time 60 minutes ago
        scheduled_time = datetime.now() + timedelta(hours=1)
        consultation_start = datetime.now() - timedelta(minutes=60)
        appointment = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.IN_PROGRESS,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1,
            consultation_start_time=consultation_start
        )
        db_session.add(appointment)
        db_session.commit()
        
        initial_average = test_doctor.average_consultation_duration  # 15
        
        # Complete the appointment
        AppointmentService.update_appointment_status(
            db=db_session,
            appointment_id=appointment.id,
            new_status=AppointmentStatus.COMPLETED,
            user_id=test_doctor_user.id,
            user_role=test_doctor_user.role.value
        )
        
        # Refresh doctor
        db_session.refresh(test_doctor)
        
        # EMA formula: new_average = (0.2 * 60) + (0.8 * 15) = 12 + 12 = 24
        expected_average = int(round((0.2 * 60) + (0.8 * initial_average)))
        assert test_doctor.average_consultation_duration == expected_average
    
    def test_ema_smooths_outliers(
        self,
        db_session: Session,
        test_doctor: Doctor
    ):
        """Test that EMA with alpha=0.2 smooths out outliers effectively"""
        # Start with 15 minutes average
        test_doctor.average_consultation_duration = 15
        db_session.commit()
        
        # Outlier: 120 minutes (very long consultation)
        AppointmentService.update_average_consultation_duration(
            db=db_session,
            doctor_id=test_doctor.id,
            actual_duration=120
        )
        db_session.refresh(test_doctor)
        
        # With alpha=0.2, the outlier has limited impact
        # new_avg = (0.2 * 120) + (0.8 * 15) = 24 + 12 = 36
        assert test_doctor.average_consultation_duration == 36
        
        # The average increased but not dramatically (from 15 to 36, not to 120)
        # This shows the smoothing effect of low alpha value
    
    def test_update_average_with_nonexistent_doctor(
        self,
        db_session: Session
    ):
        """Test that updating average for non-existent doctor doesn't crash"""
        # Should not raise an exception
        AppointmentService.update_average_consultation_duration(
            db=db_session,
            doctor_id=99999,
            actual_duration=20
        )
        # No assertion needed - just verify it doesn't crash
    
    def test_full_workflow_with_duration_tracking(
        self,
        db_session: Session,
        test_doctor_user: User,
        test_doctor: Doctor,
        test_patient: Patient
    ):
        """Test complete workflow: SCHEDULED -> CHECKED_IN -> IN_PROGRESS -> COMPLETED with duration tracking"""
        scheduled_time = datetime.now() + timedelta(hours=1)
        
        # Create scheduled appointment
        appointment = Appointment(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment)
        db_session.commit()
        
        initial_average = test_doctor.average_consultation_duration
        
        # Step 1: SCHEDULED -> CHECKED_IN
        AppointmentService.update_appointment_status(
            db=db_session,
            appointment_id=appointment.id,
            new_status=AppointmentStatus.CHECKED_IN,
            user_id=test_doctor_user.id,
            user_role=test_doctor_user.role.value
        )
        db_session.refresh(appointment)
        assert appointment.status == AppointmentStatus.CHECKED_IN
        assert appointment.consultation_start_time is None
        
        # Step 2: CHECKED_IN -> IN_PROGRESS
        before_start = datetime.now()
        AppointmentService.update_appointment_status(
            db=db_session,
            appointment_id=appointment.id,
            new_status=AppointmentStatus.IN_PROGRESS,
            user_id=test_doctor_user.id,
            user_role=test_doctor_user.role.value
        )
        db_session.refresh(appointment)
        assert appointment.status == AppointmentStatus.IN_PROGRESS
        assert appointment.consultation_start_time is not None
        assert appointment.consultation_start_time >= before_start
        
        # Simulate some consultation time (modify start time to be 18 minutes ago)
        appointment.consultation_start_time = datetime.now() - timedelta(minutes=18)
        db_session.commit()
        
        # Step 3: IN_PROGRESS -> COMPLETED
        AppointmentService.update_appointment_status(
            db=db_session,
            appointment_id=appointment.id,
            new_status=AppointmentStatus.COMPLETED,
            user_id=test_doctor_user.id,
            user_role=test_doctor_user.role.value
        )
        db_session.refresh(appointment)
        db_session.refresh(test_doctor)
        
        # Verify appointment completed
        assert appointment.status == AppointmentStatus.COMPLETED
        assert appointment.queue_position is None
        
        # Verify average was updated
        # EMA: new_avg = (0.2 * 18) + (0.8 * 15) = 3.6 + 12 = 15.6 ≈ 16
        expected_average = int(round((0.2 * 18) + (0.8 * initial_average)))
        assert test_doctor.average_consultation_duration == expected_average
