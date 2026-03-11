"""
Tests for appointment creation and management
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.appointment import Appointment, AppointmentStatus, AppointmentType
from app.services.appointment_service import AppointmentService
from app.schemas.appointment import AppointmentCreate
from app.core.security import create_access_token


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def test_users(db_session: Session):
    """Create test users (patient and doctor)"""
    # Create patient user
    patient_user = User(
        name="Test Patient",
        email="patient@test.com",
        password_hash="$2b$12$test_hash",
        role=UserRole.PATIENT
    )
    db_session.add(patient_user)
    db_session.flush()
    
    # Create patient record
    patient = Patient(
        user_id=patient_user.id,
        phone="1234567890",
        gender="Male"
    )
    db_session.add(patient)
    
    # Create doctor user
    doctor_user = User(
        name="Dr. Test",
        email="doctor@test.com",
        password_hash="$2b$12$test_hash",
        role=UserRole.DOCTOR
    )
    db_session.add(doctor_user)
    db_session.flush()
    
    # Create doctor record
    doctor = Doctor(
        user_id=doctor_user.id,
        specialization="Cardiology",
        license_number="DOC123",
        average_consultation_duration=15
    )
    db_session.add(doctor)
    
    db_session.commit()
    db_session.refresh(patient_user)
    db_session.refresh(doctor_user)
    db_session.refresh(patient)
    db_session.refresh(doctor)
    
    return {
        "patient_user": patient_user,
        "patient": patient,
        "doctor_user": doctor_user,
        "doctor": doctor
    }


class TestAppointmentService:
    """Test AppointmentService business logic"""
    
    def test_check_doctor_availability_success(self, db_session: Session, test_users):
        """Test checking doctor availability when slot is free"""
        doctor = test_users["doctor"]
        scheduled_time = datetime.now() + timedelta(days=1)
        
        is_available = AppointmentService.check_doctor_availability(
            db=db_session,
            doctor_id=doctor.id,
            scheduled_time=scheduled_time
        )
        
        assert is_available is True
    
    def test_check_doctor_availability_conflict(self, db_session: Session, test_users):
        """Test checking doctor availability when slot is occupied"""
        doctor = test_users["doctor"]
        patient = test_users["patient"]
        scheduled_time = datetime.now() + timedelta(days=1)
        
        # Create existing appointment
        existing_appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(existing_appointment)
        db_session.commit()
        
        # Try to book same time slot
        is_available = AppointmentService.check_doctor_availability(
            db=db_session,
            doctor_id=doctor.id,
            scheduled_time=scheduled_time
        )
        
        assert is_available is False
    
    def test_check_doctor_availability_within_window(self, db_session: Session, test_users):
        """Test that appointments within consultation duration window are blocked"""
        doctor = test_users["doctor"]
        patient = test_users["patient"]
        scheduled_time = datetime.now() + timedelta(days=1)
        
        # Create existing appointment
        existing_appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(existing_appointment)
        db_session.commit()
        
        # Try to book 10 minutes later (within 15-minute window)
        new_time = scheduled_time + timedelta(minutes=10)
        is_available = AppointmentService.check_doctor_availability(
            db=db_session,
            doctor_id=doctor.id,
            scheduled_time=new_time
        )
        
        assert is_available is False
    
    def test_check_doctor_availability_outside_window(self, db_session: Session, test_users):
        """Test that appointments outside consultation duration window are allowed"""
        doctor = test_users["doctor"]
        patient = test_users["patient"]
        scheduled_time = datetime.now() + timedelta(days=1)
        
        # Create existing appointment
        existing_appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(existing_appointment)
        db_session.commit()
        
        # Try to book 30 minutes later (outside 15-minute window)
        new_time = scheduled_time + timedelta(minutes=30)
        is_available = AppointmentService.check_doctor_availability(
            db=db_session,
            doctor_id=doctor.id,
            scheduled_time=new_time
        )
        
        assert is_available is True
    
    def test_get_next_queue_position_empty_queue(self, db_session: Session, test_users):
        """Test getting queue position when queue is empty"""
        doctor = test_users["doctor"]
        
        position = AppointmentService.get_next_queue_position(
            db=db_session,
            doctor_id=doctor.id
        )
        
        assert position == 1
    
    def test_get_next_queue_position_with_existing(self, db_session: Session, test_users):
        """Test getting queue position when queue has existing appointments"""
        doctor = test_users["doctor"]
        patient = test_users["patient"]
        
        # Create existing appointments
        for i in range(3):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=datetime.now() + timedelta(hours=i),
                status=AppointmentStatus.SCHEDULED,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=i + 1
            )
            db_session.add(appointment)
        db_session.commit()
        
        position = AppointmentService.get_next_queue_position(
            db=db_session,
            doctor_id=doctor.id
        )
        
        assert position == 4
    
    def test_create_appointment_success(self, db_session: Session, test_users):
        """Test successful appointment creation"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        scheduled_time = datetime.now() + timedelta(days=1)
        
        appointment_data = AppointmentCreate(
            doctor_id=doctor.id,
            scheduled_time=scheduled_time
        )
        
        appointment = AppointmentService.create_appointment(
            db=db_session,
            patient_id=patient.id,
            appointment_data=appointment_data
        )
        
        assert appointment.id is not None
        assert appointment.patient_id == patient.id
        assert appointment.doctor_id == doctor.id
        assert appointment.status == AppointmentStatus.SCHEDULED
        assert appointment.appointment_type == AppointmentType.SCHEDULED
        assert appointment.queue_position == 1
    
    def test_create_appointment_double_booking_prevented(self, db_session: Session, test_users):
        """Test that double-booking is prevented"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        scheduled_time = datetime.now() + timedelta(days=1)
        
        # Create first appointment
        appointment_data = AppointmentCreate(
            doctor_id=doctor.id,
            scheduled_time=scheduled_time
        )
        
        AppointmentService.create_appointment(
            db=db_session,
            patient_id=patient.id,
            appointment_data=appointment_data
        )
        
        # Try to create second appointment at same time
        with pytest.raises(Exception) as exc_info:
            AppointmentService.create_appointment(
                db=db_session,
                patient_id=patient.id,
                appointment_data=appointment_data
            )
        
        assert "not available" in str(exc_info.value).lower()
    
    def test_calculate_estimated_wait_time(self, db_session: Session, test_users):
        """Test estimated wait time calculation"""
        doctor = test_users["doctor"]
        
        # Queue position 1 (next patient) should have 0 wait time
        wait_time = AppointmentService.calculate_estimated_wait_time(
            db=db_session,
            doctor_id=doctor.id,
            queue_position=1
        )
        assert wait_time == 0
        
        # Queue position 3 should have 2 * 15 = 30 minutes wait
        wait_time = AppointmentService.calculate_estimated_wait_time(
            db=db_session,
            doctor_id=doctor.id,
            queue_position=3
        )
        assert wait_time == 30
    
    def test_list_appointments_no_filters(self, db_session: Session, test_users):
        """Test listing all appointments without filters"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create multiple appointments
        for i in range(3):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=datetime.now() + timedelta(days=i+1),
                status=AppointmentStatus.SCHEDULED,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=i + 1
            )
            db_session.add(appointment)
        db_session.commit()
        
        appointments = AppointmentService.list_appointments(db=db_session)
        
        assert len(appointments) == 3
    
    def test_list_appointments_filter_by_patient(self, db_session: Session, test_users):
        """Test filtering appointments by patient_id"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create appointments
        for i in range(2):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=datetime.now() + timedelta(days=i+1),
                status=AppointmentStatus.SCHEDULED,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=i + 1
            )
            db_session.add(appointment)
        db_session.commit()
        
        appointments = AppointmentService.list_appointments(
            db=db_session,
            patient_id=patient.id
        )
        
        assert len(appointments) == 2
        for appointment in appointments:
            assert appointment.patient_id == patient.id
    
    def test_list_appointments_filter_by_doctor(self, db_session: Session, test_users):
        """Test filtering appointments by doctor_id"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create appointments
        for i in range(2):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=datetime.now() + timedelta(days=i+1),
                status=AppointmentStatus.SCHEDULED,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=i + 1
            )
            db_session.add(appointment)
        db_session.commit()
        
        appointments = AppointmentService.list_appointments(
            db=db_session,
            doctor_id=doctor.id
        )
        
        assert len(appointments) == 2
        for appointment in appointments:
            assert appointment.doctor_id == doctor.id
    
    def test_list_appointments_filter_by_status(self, db_session: Session, test_users):
        """Test filtering appointments by status"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create appointments with different statuses
        statuses = [AppointmentStatus.SCHEDULED, AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]
        for i, status in enumerate(statuses):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=datetime.now() + timedelta(days=i+1),
                status=status,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=i + 1 if status == AppointmentStatus.SCHEDULED else None
            )
            db_session.add(appointment)
        db_session.commit()
        
        # Filter by scheduled status
        appointments = AppointmentService.list_appointments(
            db=db_session,
            status=AppointmentStatus.SCHEDULED
        )
        
        assert len(appointments) == 1
        assert appointments[0].status == AppointmentStatus.SCHEDULED
    
    def test_list_appointments_filter_by_date_range(self, db_session: Session, test_users):
        """Test filtering appointments by date range"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        base_date = datetime.now()
        
        # Create appointments on different dates
        for i in range(5):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=base_date + timedelta(days=i+1),
                status=AppointmentStatus.SCHEDULED,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=i + 1
            )
            db_session.add(appointment)
        db_session.commit()
        
        # Filter by date range (days 2-4)
        start_date = base_date + timedelta(days=2)
        end_date = base_date + timedelta(days=4)
        
        appointments = AppointmentService.list_appointments(
            db=db_session,
            start_date=start_date,
            end_date=end_date
        )
        
        assert len(appointments) == 3
    
    def test_list_appointments_sorted_by_time(self, db_session: Session, test_users):
        """Test that appointments are sorted by scheduled_time"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create appointments in random order
        times = [
            datetime.now() + timedelta(days=3),
            datetime.now() + timedelta(days=1),
            datetime.now() + timedelta(days=2)
        ]
        
        for i, scheduled_time in enumerate(times):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=scheduled_time,
                status=AppointmentStatus.SCHEDULED,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=i + 1
            )
            db_session.add(appointment)
        db_session.commit()
        
        appointments = AppointmentService.list_appointments(db=db_session)
        
        assert len(appointments) == 3
        # Verify sorted by scheduled_time (ascending)
        for i in range(len(appointments) - 1):
            assert appointments[i].scheduled_time <= appointments[i+1].scheduled_time
    
    def test_list_appointments_multiple_filters(self, db_session: Session, test_users):
        """Test combining multiple filters"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        base_date = datetime.now()
        
        # Create appointments with various attributes
        for i in range(5):
            status = AppointmentStatus.SCHEDULED if i < 3 else AppointmentStatus.COMPLETED
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=base_date + timedelta(days=i+1),
                status=status,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=i + 1 if status == AppointmentStatus.SCHEDULED else None
            )
            db_session.add(appointment)
        db_session.commit()
        
        # Filter by patient, status, and date range
        start_date = base_date + timedelta(days=1)
        end_date = base_date + timedelta(days=3)
        
        appointments = AppointmentService.list_appointments(
            db=db_session,
            patient_id=patient.id,
            status=AppointmentStatus.SCHEDULED,
            start_date=start_date,
            end_date=end_date
        )
        
        assert len(appointments) == 3
        for appointment in appointments:
            assert appointment.patient_id == patient.id
            assert appointment.status == AppointmentStatus.SCHEDULED


class TestAppointmentEndpoints:
    """Test appointment API endpoints"""
    
    def test_list_appointments_as_patient(self, client: TestClient, db_session: Session, test_users):
        """Test that patients can only see their own appointments"""
        patient_user = test_users["patient_user"]
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create appointments for this patient
        for i in range(3):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=datetime.now() + timedelta(days=i+1),
                status=AppointmentStatus.SCHEDULED,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=i + 1
            )
            db_session.add(appointment)
        db_session.commit()
        
        # Generate token for patient
        token = create_access_token(data={
            "user_id": patient_user.id,
            "email": patient_user.email,
            "role": patient_user.role.value
        })
        
        response = client.get(
            "/api/v1/appointments/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Verify all appointments belong to this patient
        for appointment in data:
            assert appointment["patient_id"] == patient.id
    
    def test_list_appointments_as_doctor(self, client: TestClient, db_session: Session, test_users):
        """Test that doctors can only see their own appointments"""
        doctor_user = test_users["doctor_user"]
        doctor = test_users["doctor"]
        patient = test_users["patient"]
        
        # Create appointments for this doctor
        for i in range(2):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=datetime.now() + timedelta(days=i+1),
                status=AppointmentStatus.SCHEDULED,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=i + 1
            )
            db_session.add(appointment)
        db_session.commit()
        
        # Generate token for doctor
        token = create_access_token(data={
            "user_id": doctor_user.id,
            "email": doctor_user.email,
            "role": doctor_user.role.value
        })
        
        response = client.get(
            "/api/v1/appointments/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Verify all appointments belong to this doctor
        for appointment in data:
            assert appointment["doctor_id"] == doctor.id
    
    def test_list_appointments_as_admin(self, client: TestClient, db_session: Session, test_users):
        """Test that admins can see all appointments"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create admin user
        admin_user = User(
            name="Admin User",
            email="admin@test.com",
            password_hash="$2b$12$test_hash",
            role=UserRole.ADMIN
        )
        db_session.add(admin_user)
        db_session.commit()
        db_session.refresh(admin_user)
        
        # Create appointments
        for i in range(3):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=datetime.now() + timedelta(days=i+1),
                status=AppointmentStatus.SCHEDULED,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=i + 1
            )
            db_session.add(appointment)
        db_session.commit()
        
        # Generate token for admin
        token = create_access_token(data={
            "user_id": admin_user.id,
            "email": admin_user.email,
            "role": admin_user.role.value
        })
        
        response = client.get(
            "/api/v1/appointments/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
    
    def test_list_appointments_filter_by_status(self, client: TestClient, db_session: Session, test_users):
        """Test filtering appointments by status"""
        patient_user = test_users["patient_user"]
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create appointments with different statuses
        statuses = [AppointmentStatus.SCHEDULED, AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]
        for i, status in enumerate(statuses):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=datetime.now() + timedelta(days=i+1),
                status=status,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=i + 1 if status == AppointmentStatus.SCHEDULED else None
            )
            db_session.add(appointment)
        db_session.commit()
        
        # Generate token for patient
        token = create_access_token(data={
            "user_id": patient_user.id,
            "email": patient_user.email,
            "role": patient_user.role.value
        })
        
        # Filter by scheduled status
        response = client.get(
            "/api/v1/appointments/?status=scheduled",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "scheduled"
    
    def test_list_appointments_filter_by_date_range(self, client: TestClient, db_session: Session, test_users):
        """Test filtering appointments by date range"""
        patient_user = test_users["patient_user"]
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create appointments on different dates
        base_date = datetime.now()
        for i in range(5):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=base_date + timedelta(days=i+1),
                status=AppointmentStatus.SCHEDULED,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=i + 1
            )
            db_session.add(appointment)
        db_session.commit()
        
        # Generate token for patient
        token = create_access_token(data={
            "user_id": patient_user.id,
            "email": patient_user.email,
            "role": patient_user.role.value
        })
        
        # Filter by date range (days 2-4)
        start_date = (base_date + timedelta(days=2)).isoformat()
        end_date = (base_date + timedelta(days=4)).isoformat()
        
        response = client.get(
            f"/api/v1/appointments/?start_date={start_date}&end_date={end_date}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3  # Days 2, 3, 4
    
    def test_list_appointments_sorted_by_time(self, client: TestClient, db_session: Session, test_users):
        """Test that appointments are sorted by scheduled time"""
        patient_user = test_users["patient_user"]
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create appointments in random order
        times = [
            datetime.now() + timedelta(days=3),
            datetime.now() + timedelta(days=1),
            datetime.now() + timedelta(days=2)
        ]
        
        for i, scheduled_time in enumerate(times):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=scheduled_time,
                status=AppointmentStatus.SCHEDULED,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=i + 1
            )
            db_session.add(appointment)
        db_session.commit()
        
        # Generate token for patient
        token = create_access_token(data={
            "user_id": patient_user.id,
            "email": patient_user.email,
            "role": patient_user.role.value
        })
        
        response = client.get(
            "/api/v1/appointments/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        # Verify sorted by scheduled_time (ascending)
        for i in range(len(data) - 1):
            current_time = datetime.fromisoformat(data[i]["scheduled_time"].replace('Z', '+00:00'))
            next_time = datetime.fromisoformat(data[i+1]["scheduled_time"].replace('Z', '+00:00'))
            assert current_time <= next_time
    
    def test_list_appointments_includes_details(self, client: TestClient, db_session: Session, test_users):
        """Test that appointment listing includes patient and doctor details"""
        patient_user = test_users["patient_user"]
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create appointment
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=datetime.now() + timedelta(days=1),
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment)
        db_session.commit()
        
        # Generate token for patient
        token = create_access_token(data={
            "user_id": patient_user.id,
            "email": patient_user.email,
            "role": patient_user.role.value
        })
        
        response = client.get(
            "/api/v1/appointments/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        
        appointment_data = data[0]
        assert appointment_data["patient_name"] == patient_user.name
        assert appointment_data["doctor_name"] == test_users["doctor_user"].name
        assert appointment_data["doctor_specialization"] == doctor.specialization
        assert "estimated_wait_time" in appointment_data
    
    def test_list_appointments_admin_filter_by_patient(self, client: TestClient, db_session: Session, test_users):
        """Test that admins can filter by patient_id"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create admin user
        admin_user = User(
            name="Admin User",
            email="admin@test.com",
            password_hash="$2b$12$test_hash",
            role=UserRole.ADMIN
        )
        db_session.add(admin_user)
        db_session.commit()
        db_session.refresh(admin_user)
        
        # Create another patient
        patient_user2 = User(
            name="Test Patient 2",
            email="patient2@test.com",
            password_hash="$2b$12$test_hash",
            role=UserRole.PATIENT
        )
        db_session.add(patient_user2)
        db_session.flush()
        
        patient2 = Patient(
            user_id=patient_user2.id,
            phone="9876543210",
            gender="Female"
        )
        db_session.add(patient2)
        db_session.commit()
        db_session.refresh(patient2)
        
        # Create appointments for both patients
        for p in [patient, patient2]:
            appointment = Appointment(
                patient_id=p.id,
                doctor_id=doctor.id,
                scheduled_time=datetime.now() + timedelta(days=1),
                status=AppointmentStatus.SCHEDULED,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=1
            )
            db_session.add(appointment)
        db_session.commit()
        
        # Generate token for admin
        token = create_access_token(data={
            "user_id": admin_user.id,
            "email": admin_user.email,
            "role": admin_user.role.value
        })
        
        # Filter by first patient
        response = client.get(
            f"/api/v1/appointments/?patient_id={patient.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["patient_id"] == patient.id
    
    def test_list_appointments_admin_filter_by_doctor(self, client: TestClient, db_session: Session, test_users):
        """Test that admins can filter by doctor_id"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create admin user
        admin_user = User(
            name="Admin User",
            email="admin@test.com",
            password_hash="$2b$12$test_hash",
            role=UserRole.ADMIN
        )
        db_session.add(admin_user)
        db_session.commit()
        db_session.refresh(admin_user)
        
        # Create another doctor
        doctor_user2 = User(
            name="Dr. Test 2",
            email="doctor2@test.com",
            password_hash="$2b$12$test_hash",
            role=UserRole.DOCTOR
        )
        db_session.add(doctor_user2)
        db_session.flush()
        
        doctor2 = Doctor(
            user_id=doctor_user2.id,
            specialization="Neurology",
            license_number="DOC456",
            average_consultation_duration=20
        )
        db_session.add(doctor2)
        db_session.commit()
        db_session.refresh(doctor2)
        
        # Create appointments for both doctors
        for d in [doctor, doctor2]:
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=d.id,
                scheduled_time=datetime.now() + timedelta(days=1),
                status=AppointmentStatus.SCHEDULED,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=1
            )
            db_session.add(appointment)
        db_session.commit()
        
        # Generate token for admin
        token = create_access_token(data={
            "user_id": admin_user.id,
            "email": admin_user.email,
            "role": admin_user.role.value
        })
        
        # Filter by first doctor
        response = client.get(
            f"/api/v1/appointments/?doctor_id={doctor.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["doctor_id"] == doctor.id
    
    def test_list_appointments_unauthorized(self, client: TestClient):
        """Test that listing appointments requires authentication"""
        response = client.get("/api/v1/appointments/")
        assert response.status_code == 401
    
    def test_list_appointments_invalid_status(self, client: TestClient, db_session: Session, test_users):
        """Test that invalid status values are rejected"""
        patient_user = test_users["patient_user"]
        
        # Generate token for patient
        token = create_access_token(data={
            "user_id": patient_user.id,
            "email": patient_user.email,
            "role": patient_user.role.value
        })
        
        response = client.get(
            "/api/v1/appointments/?status=invalid_status",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert "Invalid status value" in response.json()["detail"]
    
    def test_create_appointment_success(self, client: TestClient, db_session: Session, test_users):
        """Test successful appointment creation via API"""
        patient_user = test_users["patient_user"]
        doctor = test_users["doctor"]
        
        # Generate token for patient with correct payload
        token = create_access_token(data={
            "user_id": patient_user.id,
            "email": patient_user.email,
            "role": patient_user.role.value
        })
        
        scheduled_time = (datetime.now() + timedelta(days=1)).isoformat()
        
        response = client.post(
            "/api/v1/appointments/",
            json={
                "doctor_id": doctor.id,
                "scheduled_time": scheduled_time
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["doctor_id"] == doctor.id
        assert data["status"] == "scheduled"
        assert data["queue_position"] == 1
        assert "estimated_wait_time" in data
    
    def test_create_appointment_unauthorized(self, client: TestClient, db_session: Session, test_users):
        """Test that appointment creation requires authentication"""
        doctor = test_users["doctor"]
        scheduled_time = (datetime.now() + timedelta(days=1)).isoformat()
        
        response = client.post(
            "/api/v1/appointments/",
            json={
                "doctor_id": doctor.id,
                "scheduled_time": scheduled_time
            }
        )
        
        assert response.status_code == 401
    
    def test_create_appointment_wrong_role(self, client: TestClient, db_session: Session, test_users):
        """Test that only patients can create appointments"""
        doctor_user = test_users["doctor_user"]
        doctor = test_users["doctor"]
        
        # Generate token for doctor (wrong role) with correct payload
        token = create_access_token(data={
            "user_id": doctor_user.id,
            "email": doctor_user.email,
            "role": doctor_user.role.value
        })
        
        scheduled_time = (datetime.now() + timedelta(days=1)).isoformat()
        
        response = client.post(
            "/api/v1/appointments/",
            json={
                "doctor_id": doctor.id,
                "scheduled_time": scheduled_time
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
    
    def test_create_appointment_invalid_doctor(self, client: TestClient, db_session: Session, test_users):
        """Test appointment creation with non-existent doctor"""
        patient_user = test_users["patient_user"]
        
        # Generate token for patient with correct payload
        token = create_access_token(data={
            "user_id": patient_user.id,
            "email": patient_user.email,
            "role": patient_user.role.value
        })
        
        scheduled_time = (datetime.now() + timedelta(days=1)).isoformat()
        
        response = client.post(
            "/api/v1/appointments/",
            json={
                "doctor_id": 99999,  # Non-existent doctor
                "scheduled_time": scheduled_time
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404
    
    def test_create_appointment_double_booking(self, client: TestClient, db_session: Session, test_users):
        """Test that double-booking is prevented via API"""
        patient_user = test_users["patient_user"]
        doctor = test_users["doctor"]
        
        # Generate token for patient with correct payload
        token = create_access_token(data={
            "user_id": patient_user.id,
            "email": patient_user.email,
            "role": patient_user.role.value
        })
        
        scheduled_time = (datetime.now() + timedelta(days=1)).isoformat()
        
        # Create first appointment
        response1 = client.post(
            "/api/v1/appointments/",
            json={
                "doctor_id": doctor.id,
                "scheduled_time": scheduled_time
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response1.status_code == 201
        
        # Try to create second appointment at same time
        response2 = client.post(
            "/api/v1/appointments/",
            json={
                "doctor_id": doctor.id,
                "scheduled_time": scheduled_time
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response2.status_code == 409
        assert "not available" in response2.json()["detail"].lower()


class TestAppointmentCancellation:
    """Test appointment cancellation functionality"""
    
    def test_cancel_appointment_service_success(self, db_session: Session, test_users):
        """Test successful appointment cancellation via service"""
        patient = test_users["patient"]
        patient_user = test_users["patient_user"]
        doctor = test_users["doctor"]
        
        # Create appointment 3 hours in future (beyond 2-hour rule)
        scheduled_time = datetime.now() + timedelta(hours=3)
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
        
        # Cancel appointment
        cancelled = AppointmentService.cancel_appointment(
            db=db_session,
            appointment_id=appointment.id,
            user_id=patient_user.id,
            user_role=patient_user.role.value
        )
        
        assert cancelled.status == AppointmentStatus.CANCELLED
        assert cancelled.queue_position is None
    
    def test_cancel_appointment_not_found(self, db_session: Session, test_users):
        """Test cancelling non-existent appointment"""
        patient_user = test_users["patient_user"]
        
        with pytest.raises(HTTPException) as exc_info:
            AppointmentService.cancel_appointment(
                db=db_session,
                appointment_id=99999,
                user_id=patient_user.id,
                user_role=patient_user.role.value
            )
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()
    
    def test_cancel_appointment_already_cancelled(self, db_session: Session, test_users):
        """Test cancelling already cancelled appointment"""
        patient = test_users["patient"]
        patient_user = test_users["patient_user"]
        doctor = test_users["doctor"]
        
        # Create cancelled appointment
        scheduled_time = datetime.now() + timedelta(hours=3)
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.CANCELLED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=None
        )
        db_session.add(appointment)
        db_session.commit()
        db_session.refresh(appointment)
        
        # Try to cancel again
        with pytest.raises(HTTPException) as exc_info:
            AppointmentService.cancel_appointment(
                db=db_session,
                appointment_id=appointment.id,
                user_id=patient_user.id,
                user_role=patient_user.role.value
            )
        
        assert exc_info.value.status_code == 400
        assert "already cancelled" in exc_info.value.detail.lower()
    
    def test_cancel_appointment_patient_not_owner(self, db_session: Session, test_users):
        """Test patient cannot cancel another patient's appointment"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create another patient
        patient_user2 = User(
            name="Test Patient 2",
            email="patient2@test.com",
            password_hash="$2b$12$test_hash",
            role=UserRole.PATIENT
        )
        db_session.add(patient_user2)
        db_session.flush()
        
        patient2 = Patient(
            user_id=patient_user2.id,
            phone="9876543210",
            gender="Female"
        )
        db_session.add(patient2)
        db_session.commit()
        db_session.refresh(patient_user2)
        db_session.refresh(patient2)
        
        # Create appointment for patient 1
        scheduled_time = datetime.now() + timedelta(hours=3)
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
        
        # Try to cancel as patient 2
        with pytest.raises(HTTPException) as exc_info:
            AppointmentService.cancel_appointment(
                db=db_session,
                appointment_id=appointment.id,
                user_id=patient_user2.id,
                user_role=patient_user2.role.value
            )
        
        assert exc_info.value.status_code == 403
        assert "your own" in exc_info.value.detail.lower()
    
    def test_cancel_appointment_within_2_hour_window(self, db_session: Session, test_users):
        """Test that appointments cannot be cancelled within 2 hours of scheduled time"""
        patient = test_users["patient"]
        patient_user = test_users["patient_user"]
        doctor = test_users["doctor"]
        
        # Create appointment 1 hour in future (within 2-hour rule)
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
        
        # Try to cancel
        with pytest.raises(HTTPException) as exc_info:
            AppointmentService.cancel_appointment(
                db=db_session,
                appointment_id=appointment.id,
                user_id=patient_user.id,
                user_role=patient_user.role.value
            )
        
        assert exc_info.value.status_code == 400
        assert "2 hours" in exc_info.value.detail.lower()
    
    def test_cancel_appointment_staff_can_cancel_any(self, db_session: Session, test_users):
        """Test that staff can cancel any appointment"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create admin user
        admin_user = User(
            name="Admin User",
            email="admin@test.com",
            password_hash="$2b$12$test_hash",
            role=UserRole.ADMIN
        )
        db_session.add(admin_user)
        db_session.commit()
        db_session.refresh(admin_user)
        
        # Create appointment
        scheduled_time = datetime.now() + timedelta(hours=3)
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
        
        # Admin cancels appointment
        cancelled = AppointmentService.cancel_appointment(
            db=db_session,
            appointment_id=appointment.id,
            user_id=admin_user.id,
            user_role=admin_user.role.value
        )
        
        assert cancelled.status == AppointmentStatus.CANCELLED
        assert cancelled.queue_position is None
    
    def test_update_queue_positions_after_cancellation(self, db_session: Session, test_users):
        """Test that queue positions are updated after cancellation"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create 5 appointments in queue
        appointments = []
        for i in range(5):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=datetime.now() + timedelta(hours=i+3),
                status=AppointmentStatus.SCHEDULED,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=i + 1
            )
            db_session.add(appointment)
            appointments.append(appointment)
        db_session.commit()
        
        # Refresh all appointments
        for appointment in appointments:
            db_session.refresh(appointment)
        
        # Cancel appointment at position 3
        AppointmentService.update_queue_positions_after_cancellation(
            db=db_session,
            doctor_id=doctor.id,
            cancelled_position=3
        )
        
        # Refresh all appointments
        for appointment in appointments:
            db_session.refresh(appointment)
        
        # Verify queue positions
        assert appointments[0].queue_position == 1  # Unchanged
        assert appointments[1].queue_position == 2  # Unchanged
        assert appointments[2].queue_position == 3  # This one was cancelled (not updated here)
        assert appointments[3].queue_position == 3  # Decremented from 4
        assert appointments[4].queue_position == 4  # Decremented from 5
    
    def test_cancel_appointment_endpoint_success(self, client: TestClient, db_session: Session, test_users):
        """Test successful appointment cancellation via API"""
        patient_user = test_users["patient_user"]
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create appointment 3 hours in future
        scheduled_time = datetime.now() + timedelta(hours=3)
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
        
        # Generate token for patient
        token = create_access_token(data={
            "user_id": patient_user.id,
            "email": patient_user.email,
            "role": patient_user.role.value
        })
        
        # Cancel appointment
        response = client.delete(
            f"/api/v1/appointments/{appointment.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 204
        
        # Verify appointment is cancelled
        db_session.refresh(appointment)
        assert appointment.status == AppointmentStatus.CANCELLED
        assert appointment.queue_position is None
    
    def test_cancel_appointment_endpoint_not_found(self, client: TestClient, db_session: Session, test_users):
        """Test cancelling non-existent appointment via API"""
        patient_user = test_users["patient_user"]
        
        # Generate token for patient
        token = create_access_token(data={
            "user_id": patient_user.id,
            "email": patient_user.email,
            "role": patient_user.role.value
        })
        
        # Try to cancel non-existent appointment
        response = client.delete(
            "/api/v1/appointments/99999",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404
    
    def test_cancel_appointment_endpoint_unauthorized(self, client: TestClient, db_session: Session, test_users):
        """Test that cancellation requires authentication"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create appointment
        scheduled_time = datetime.now() + timedelta(hours=3)
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
        
        # Try to cancel without token
        response = client.delete(f"/api/v1/appointments/{appointment.id}")
        
        assert response.status_code == 401
    
    def test_cancel_appointment_endpoint_not_owner(self, client: TestClient, db_session: Session, test_users):
        """Test patient cannot cancel another patient's appointment via API"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create another patient
        patient_user2 = User(
            name="Test Patient 2",
            email="patient2@test.com",
            password_hash="$2b$12$test_hash",
            role=UserRole.PATIENT
        )
        db_session.add(patient_user2)
        db_session.flush()
        
        patient2 = Patient(
            user_id=patient_user2.id,
            phone="9876543210",
            gender="Female"
        )
        db_session.add(patient2)
        db_session.commit()
        db_session.refresh(patient_user2)
        
        # Create appointment for patient 1
        scheduled_time = datetime.now() + timedelta(hours=3)
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
        
        # Generate token for patient 2
        token = create_access_token(data={
            "user_id": patient_user2.id,
            "email": patient_user2.email,
            "role": patient_user2.role.value
        })
        
        # Try to cancel patient 1's appointment
        response = client.delete(
            f"/api/v1/appointments/{appointment.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
    
    def test_cancel_appointment_endpoint_within_2_hours(self, client: TestClient, db_session: Session, test_users):
        """Test that appointments cannot be cancelled within 2 hours via API"""
        patient_user = test_users["patient_user"]
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create appointment 1 hour in future
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
        
        # Generate token for patient
        token = create_access_token(data={
            "user_id": patient_user.id,
            "email": patient_user.email,
            "role": patient_user.role.value
        })
        
        # Try to cancel
        response = client.delete(
            f"/api/v1/appointments/{appointment.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert "2 hours" in response.json()["detail"].lower()
    
    def test_cancel_appointment_endpoint_staff_can_cancel(self, client: TestClient, db_session: Session, test_users):
        """Test that staff can cancel any appointment via API"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create nurse user
        nurse_user = User(
            name="Nurse User",
            email="nurse@test.com",
            password_hash="$2b$12$test_hash",
            role=UserRole.NURSE
        )
        db_session.add(nurse_user)
        db_session.commit()
        db_session.refresh(nurse_user)
        
        # Create appointment
        scheduled_time = datetime.now() + timedelta(hours=3)
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
        
        # Generate token for nurse
        token = create_access_token(data={
            "user_id": nurse_user.id,
            "email": nurse_user.email,
            "role": nurse_user.role.value
        })
        
        # Nurse cancels appointment
        response = client.delete(
            f"/api/v1/appointments/{appointment.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 204
        
        # Verify appointment is cancelled
        db_session.refresh(appointment)
        assert appointment.status == AppointmentStatus.CANCELLED
    
    def test_cancel_appointment_updates_queue_positions(self, client: TestClient, db_session: Session, test_users):
        """Test that cancelling an appointment updates queue positions for remaining appointments"""
        patient_user = test_users["patient_user"]
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create 5 appointments in queue
        appointments = []
        for i in range(5):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=datetime.now() + timedelta(hours=i+3),
                status=AppointmentStatus.SCHEDULED,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=i + 1
            )
            db_session.add(appointment)
            appointments.append(appointment)
        db_session.commit()
        
        # Refresh all appointments
        for appointment in appointments:
            db_session.refresh(appointment)
        
        # Generate token for patient
        token = create_access_token(data={
            "user_id": patient_user.id,
            "email": patient_user.email,
            "role": patient_user.role.value
        })
        
        # Cancel appointment at position 3
        response = client.delete(
            f"/api/v1/appointments/{appointments[2].id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 204
        
        # Refresh all appointments
        for appointment in appointments:
            db_session.refresh(appointment)
        
        # Verify queue positions
        assert appointments[0].queue_position == 1  # Unchanged
        assert appointments[1].queue_position == 2  # Unchanged
        assert appointments[2].queue_position is None  # Cancelled
        assert appointments[2].status == AppointmentStatus.CANCELLED
        assert appointments[3].queue_position == 3  # Decremented from 4
        assert appointments[4].queue_position == 4  # Decremented from 5



class TestAppointmentRescheduling:
    """Test appointment rescheduling functionality"""
    
    def test_reschedule_appointment_service_success(self, db_session: Session, test_users):
        """Test successful appointment rescheduling via service"""
        patient = test_users["patient"]
        patient_user = test_users["patient_user"]
        doctor = test_users["doctor"]
        
        # Create appointment
        scheduled_time = datetime.now() + timedelta(days=1)
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
        
        # Reschedule to new time
        new_time = datetime.now() + timedelta(days=2)
        rescheduled = AppointmentService.reschedule_appointment(
            db=db_session,
            appointment_id=appointment.id,
            new_scheduled_time=new_time,
            user_id=patient_user.id,
            user_role=patient_user.role.value
        )
        
        assert rescheduled.scheduled_time == new_time
        assert rescheduled.status == AppointmentStatus.SCHEDULED
        assert rescheduled.queue_position is not None
    
    def test_reschedule_appointment_not_found(self, db_session: Session, test_users):
        """Test rescheduling non-existent appointment"""
        patient_user = test_users["patient_user"]
        new_time = datetime.now() + timedelta(days=2)
        
        with pytest.raises(HTTPException) as exc_info:
            AppointmentService.reschedule_appointment(
                db=db_session,
                appointment_id=99999,
                new_scheduled_time=new_time,
                user_id=patient_user.id,
                user_role=patient_user.role.value
            )
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()
    
    def test_reschedule_appointment_already_cancelled(self, db_session: Session, test_users):
        """Test rescheduling already cancelled appointment"""
        patient = test_users["patient"]
        patient_user = test_users["patient_user"]
        doctor = test_users["doctor"]
        
        # Create cancelled appointment
        scheduled_time = datetime.now() + timedelta(days=1)
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.CANCELLED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=None
        )
        db_session.add(appointment)
        db_session.commit()
        db_session.refresh(appointment)
        
        # Try to reschedule
        new_time = datetime.now() + timedelta(days=2)
        with pytest.raises(HTTPException) as exc_info:
            AppointmentService.reschedule_appointment(
                db=db_session,
                appointment_id=appointment.id,
                new_scheduled_time=new_time,
                user_id=patient_user.id,
                user_role=patient_user.role.value
            )
        
        assert exc_info.value.status_code == 400
        assert "cannot reschedule" in exc_info.value.detail.lower()
    
    def test_reschedule_appointment_already_completed(self, db_session: Session, test_users):
        """Test rescheduling already completed appointment"""
        patient = test_users["patient"]
        patient_user = test_users["patient_user"]
        doctor = test_users["doctor"]
        
        # Create completed appointment
        scheduled_time = datetime.now() - timedelta(days=1)
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.COMPLETED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=None
        )
        db_session.add(appointment)
        db_session.commit()
        db_session.refresh(appointment)
        
        # Try to reschedule
        new_time = datetime.now() + timedelta(days=2)
        with pytest.raises(HTTPException) as exc_info:
            AppointmentService.reschedule_appointment(
                db=db_session,
                appointment_id=appointment.id,
                new_scheduled_time=new_time,
                user_id=patient_user.id,
                user_role=patient_user.role.value
            )
        
        assert exc_info.value.status_code == 400
        assert "cannot reschedule" in exc_info.value.detail.lower()
    
    def test_reschedule_appointment_patient_not_owner(self, db_session: Session, test_users):
        """Test patient cannot reschedule another patient's appointment"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create another patient
        patient_user2 = User(
            name="Test Patient 2",
            email="patient2@test.com",
            password_hash="$2b$12$test_hash",
            role=UserRole.PATIENT
        )
        db_session.add(patient_user2)
        db_session.flush()
        
        patient2 = Patient(
            user_id=patient_user2.id,
            phone="9876543210",
            gender="Female"
        )
        db_session.add(patient2)
        db_session.commit()
        db_session.refresh(patient_user2)
        db_session.refresh(patient2)
        
        # Create appointment for patient 1
        scheduled_time = datetime.now() + timedelta(days=1)
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
        
        # Try to reschedule as patient 2
        new_time = datetime.now() + timedelta(days=2)
        with pytest.raises(HTTPException) as exc_info:
            AppointmentService.reschedule_appointment(
                db=db_session,
                appointment_id=appointment.id,
                new_scheduled_time=new_time,
                user_id=patient_user2.id,
                user_role=patient_user2.role.value
            )
        
        assert exc_info.value.status_code == 403
        assert "your own" in exc_info.value.detail.lower()
    
    def test_reschedule_appointment_time_not_available(self, db_session: Session, test_users):
        """Test rescheduling to unavailable time slot"""
        patient = test_users["patient"]
        patient_user = test_users["patient_user"]
        doctor = test_users["doctor"]
        
        # Create two appointments
        scheduled_time1 = datetime.now() + timedelta(days=1)
        appointment1 = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=scheduled_time1,
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment1)
        
        scheduled_time2 = datetime.now() + timedelta(days=2)
        appointment2 = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=scheduled_time2,
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=2
        )
        db_session.add(appointment2)
        db_session.commit()
        db_session.refresh(appointment1)
        db_session.refresh(appointment2)
        
        # Try to reschedule appointment1 to appointment2's time
        with pytest.raises(HTTPException) as exc_info:
            AppointmentService.reschedule_appointment(
                db=db_session,
                appointment_id=appointment1.id,
                new_scheduled_time=scheduled_time2,
                user_id=patient_user.id,
                user_role=patient_user.role.value
            )
        
        assert exc_info.value.status_code == 409
        assert "not available" in exc_info.value.detail.lower()
    
    def test_reschedule_appointment_staff_can_reschedule_any(self, db_session: Session, test_users):
        """Test that staff can reschedule any appointment"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create admin user
        admin_user = User(
            name="Admin User",
            email="admin@test.com",
            password_hash="$2b$12$test_hash",
            role=UserRole.ADMIN
        )
        db_session.add(admin_user)
        db_session.commit()
        db_session.refresh(admin_user)
        
        # Create appointment
        scheduled_time = datetime.now() + timedelta(days=1)
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
        
        # Admin reschedules appointment
        new_time = datetime.now() + timedelta(days=2)
        rescheduled = AppointmentService.reschedule_appointment(
            db=db_session,
            appointment_id=appointment.id,
            new_scheduled_time=new_time,
            user_id=admin_user.id,
            user_role=admin_user.role.value
        )
        
        assert rescheduled.scheduled_time == new_time
        assert rescheduled.status == AppointmentStatus.SCHEDULED
    
    def test_reschedule_appointment_updates_queue_position(self, db_session: Session, test_users):
        """Test that rescheduling updates queue positions correctly"""
        patient = test_users["patient"]
        patient_user = test_users["patient_user"]
        doctor = test_users["doctor"]
        
        # Create 3 appointments in queue
        appointments = []
        for i in range(3):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=datetime.now() + timedelta(days=i+1),
                status=AppointmentStatus.SCHEDULED,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=i + 1
            )
            db_session.add(appointment)
            appointments.append(appointment)
        db_session.commit()
        
        # Refresh all appointments
        for appointment in appointments:
            db_session.refresh(appointment)
        
        # Reschedule first appointment (position 1) to later time
        new_time = datetime.now() + timedelta(days=5)
        rescheduled = AppointmentService.reschedule_appointment(
            db=db_session,
            appointment_id=appointments[0].id,
            new_scheduled_time=new_time,
            user_id=patient_user.id,
            user_role=patient_user.role.value
        )
        
        # Refresh all appointments
        for appointment in appointments:
            db_session.refresh(appointment)
        
        # Rescheduled appointment should be at end of queue
        assert rescheduled.queue_position == 3
        # Other appointments should move up
        assert appointments[1].queue_position == 1  # Was 2, now 1
        assert appointments[2].queue_position == 2  # Was 3, now 2
    
    def test_reschedule_appointment_endpoint_success(self, client: TestClient, db_session: Session, test_users):
        """Test successful appointment rescheduling via API"""
        patient_user = test_users["patient_user"]
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create appointment
        scheduled_time = datetime.now() + timedelta(days=1)
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
        
        # Generate token for patient
        token = create_access_token(data={
            "user_id": patient_user.id,
            "email": patient_user.email,
            "role": patient_user.role.value
        })
        
        # Reschedule appointment
        new_time = (datetime.now() + timedelta(days=2)).isoformat()
        response = client.put(
            f"/api/v1/appointments/{appointment.id}/reschedule",
            json={"new_scheduled_time": new_time},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == appointment.id
        assert data["status"] == "scheduled"
        assert "queue_position" in data
        assert "estimated_wait_time" in data
        
        # Verify appointment is rescheduled
        db_session.refresh(appointment)
        assert appointment.scheduled_time.date() == (datetime.now() + timedelta(days=2)).date()
    
    def test_reschedule_appointment_endpoint_not_found(self, client: TestClient, db_session: Session, test_users):
        """Test rescheduling non-existent appointment via API"""
        patient_user = test_users["patient_user"]
        
        # Generate token for patient
        token = create_access_token(data={
            "user_id": patient_user.id,
            "email": patient_user.email,
            "role": patient_user.role.value
        })
        
        # Try to reschedule non-existent appointment
        new_time = (datetime.now() + timedelta(days=2)).isoformat()
        response = client.put(
            "/api/v1/appointments/99999/reschedule",
            json={"new_scheduled_time": new_time},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404
    
    def test_reschedule_appointment_endpoint_unauthorized(self, client: TestClient, db_session: Session, test_users):
        """Test that rescheduling requires authentication"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create appointment
        scheduled_time = datetime.now() + timedelta(days=1)
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
        
        # Try to reschedule without token
        new_time = (datetime.now() + timedelta(days=2)).isoformat()
        response = client.put(
            f"/api/v1/appointments/{appointment.id}/reschedule",
            json={"new_scheduled_time": new_time}
        )
        
        assert response.status_code == 401
    
    def test_reschedule_appointment_endpoint_not_owner(self, client: TestClient, db_session: Session, test_users):
        """Test patient cannot reschedule another patient's appointment via API"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create another patient
        patient_user2 = User(
            name="Test Patient 2",
            email="patient2@test.com",
            password_hash="$2b$12$test_hash",
            role=UserRole.PATIENT
        )
        db_session.add(patient_user2)
        db_session.flush()
        
        patient2 = Patient(
            user_id=patient_user2.id,
            phone="9876543210",
            gender="Female"
        )
        db_session.add(patient2)
        db_session.commit()
        db_session.refresh(patient_user2)
        
        # Create appointment for patient 1
        scheduled_time = datetime.now() + timedelta(days=1)
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
        
        # Generate token for patient 2
        token = create_access_token(data={
            "user_id": patient_user2.id,
            "email": patient_user2.email,
            "role": patient_user2.role.value
        })
        
        # Try to reschedule patient 1's appointment
        new_time = (datetime.now() + timedelta(days=2)).isoformat()
        response = client.put(
            f"/api/v1/appointments/{appointment.id}/reschedule",
            json={"new_scheduled_time": new_time},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
    
    def test_reschedule_appointment_endpoint_time_not_available(self, client: TestClient, db_session: Session, test_users):
        """Test rescheduling to unavailable time slot via API"""
        patient_user = test_users["patient_user"]
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create two appointments
        scheduled_time1 = datetime.now() + timedelta(days=1)
        appointment1 = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=scheduled_time1,
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment1)
        
        scheduled_time2 = datetime.now() + timedelta(days=2)
        appointment2 = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=scheduled_time2,
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=2
        )
        db_session.add(appointment2)
        db_session.commit()
        db_session.refresh(appointment1)
        db_session.refresh(appointment2)
        
        # Generate token for patient
        token = create_access_token(data={
            "user_id": patient_user.id,
            "email": patient_user.email,
            "role": patient_user.role.value
        })
        
        # Try to reschedule appointment1 to appointment2's time
        response = client.put(
            f"/api/v1/appointments/{appointment1.id}/reschedule",
            json={"new_scheduled_time": scheduled_time2.isoformat()},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 409
        assert "not available" in response.json()["detail"].lower()
    
    def test_reschedule_appointment_endpoint_staff_can_reschedule(self, client: TestClient, db_session: Session, test_users):
        """Test that staff can reschedule any appointment via API"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create nurse user
        nurse_user = User(
            name="Nurse User",
            email="nurse@test.com",
            password_hash="$2b$12$test_hash",
            role=UserRole.NURSE
        )
        db_session.add(nurse_user)
        db_session.commit()
        db_session.refresh(nurse_user)
        
        # Create appointment
        scheduled_time = datetime.now() + timedelta(days=1)
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
        
        # Generate token for nurse
        token = create_access_token(data={
            "user_id": nurse_user.id,
            "email": nurse_user.email,
            "role": nurse_user.role.value
        })
        
        # Nurse reschedules appointment
        new_time = (datetime.now() + timedelta(days=2)).isoformat()
        response = client.put(
            f"/api/v1/appointments/{appointment.id}/reschedule",
            json={"new_scheduled_time": new_time},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == appointment.id
        
        # Verify appointment is rescheduled
        db_session.refresh(appointment)
        assert appointment.scheduled_time.date() == (datetime.now() + timedelta(days=2)).date()
    
    def test_reschedule_appointment_endpoint_cancelled_appointment(self, client: TestClient, db_session: Session, test_users):
        """Test that cancelled appointments cannot be rescheduled via API"""
        patient_user = test_users["patient_user"]
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create cancelled appointment
        scheduled_time = datetime.now() + timedelta(days=1)
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.CANCELLED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=None
        )
        db_session.add(appointment)
        db_session.commit()
        db_session.refresh(appointment)
        
        # Generate token for patient
        token = create_access_token(data={
            "user_id": patient_user.id,
            "email": patient_user.email,
            "role": patient_user.role.value
        })
        
        # Try to reschedule
        new_time = (datetime.now() + timedelta(days=2)).isoformat()
        response = client.put(
            f"/api/v1/appointments/{appointment.id}/reschedule",
            json={"new_scheduled_time": new_time},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert "cannot reschedule" in response.json()["detail"].lower()


class TestWalkInRegistration:
    """Test walk-in patient registration functionality"""
    
    def test_register_walk_in_new_patient_with_email(self, db_session: Session, test_users):
        """Test walk-in registration for new patient with email"""
        doctor = test_users["doctor"]
        
        # Register walk-in patient
        appointment, patient, is_new = AppointmentService.register_walk_in(
            db=db_session,
            doctor_id=doctor.id,
            patient_name="Walk-in Patient",
            patient_email="walkin@test.com",
            patient_phone="5551234567",
            gender="Male"
        )
        
        assert is_new is True
        assert appointment.id is not None
        assert appointment.appointment_type == AppointmentType.WALK_IN
        assert appointment.status == AppointmentStatus.CHECKED_IN
        assert appointment.queue_position == 1
        assert patient.user.name == "Walk-in Patient"
        assert patient.user.email == "walkin@test.com"
        assert patient.phone == "5551234567"
    
    def test_register_walk_in_new_patient_without_email(self, db_session: Session, test_users):
        """Test walk-in registration for new patient without email (generates email)"""
        doctor = test_users["doctor"]
        
        # Register walk-in patient without email
        appointment, patient, is_new = AppointmentService.register_walk_in(
            db=db_session,
            doctor_id=doctor.id,
            patient_name="Walk-in Patient No Email",
            patient_phone="5559876543",
            gender="Female"
        )
        
        assert is_new is True
        assert appointment.id is not None
        assert patient.user.email is not None
        # Email should be auto-generated using phone
        assert "5559876543" in patient.user.email or "@walkin.healthsaathi.local" in patient.user.email
    
    def test_register_walk_in_existing_patient_by_email(self, db_session: Session, test_users):
        """Test walk-in registration for existing patient (found by email)"""
        doctor = test_users["doctor"]
        patient = test_users["patient"]
        patient_user = test_users["patient_user"]
        
        # Register walk-in for existing patient
        appointment, returned_patient, is_new = AppointmentService.register_walk_in(
            db=db_session,
            doctor_id=doctor.id,
            patient_name="Different Name",  # Name doesn't matter for existing patient
            patient_email=patient_user.email,  # Use existing email
            patient_phone="9999999999"
        )
        
        assert is_new is False
        assert returned_patient.id == patient.id
        assert appointment.patient_id == patient.id
        assert appointment.appointment_type == AppointmentType.WALK_IN
    
    def test_register_walk_in_existing_patient_by_phone(self, db_session: Session, test_users):
        """Test walk-in registration for existing patient (found by phone)"""
        doctor = test_users["doctor"]
        patient = test_users["patient"]
        
        # Register walk-in for existing patient using phone
        appointment, returned_patient, is_new = AppointmentService.register_walk_in(
            db=db_session,
            doctor_id=doctor.id,
            patient_name="Different Name",
            patient_phone=patient.phone,  # Use existing phone
            gender="Female"
        )
        
        assert is_new is False
        assert returned_patient.id == patient.id
        assert appointment.patient_id == patient.id
    
    def test_register_walk_in_invalid_doctor(self, db_session: Session):
        """Test walk-in registration with non-existent doctor"""
        with pytest.raises(HTTPException) as exc_info:
            AppointmentService.register_walk_in(
                db=db_session,
                doctor_id=99999,
                patient_name="Walk-in Patient",
                patient_email="walkin@test.com"
            )
        
        assert exc_info.value.status_code == 404
        assert "Doctor" in exc_info.value.detail
    
    def test_register_walk_in_queue_position(self, db_session: Session, test_users):
        """Test that walk-in patients are added to queue correctly"""
        doctor = test_users["doctor"]
        patient = test_users["patient"]
        
        # Create existing appointment in queue
        existing_appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=datetime.now(),
            status=AppointmentStatus.CHECKED_IN,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(existing_appointment)
        db_session.commit()
        
        # Register walk-in patient
        appointment, _, _ = AppointmentService.register_walk_in(
            db=db_session,
            doctor_id=doctor.id,
            patient_name="Walk-in Patient",
            patient_email="walkin2@test.com"
        )
        
        # Should be added to end of queue
        assert appointment.queue_position == 2
    
    def test_register_walk_in_immediate_scheduled_time(self, db_session: Session, test_users):
        """Test that walk-in appointments have immediate scheduled time"""
        doctor = test_users["doctor"]
        
        before_time = datetime.now()
        
        appointment, _, _ = AppointmentService.register_walk_in(
            db=db_session,
            doctor_id=doctor.id,
            patient_name="Walk-in Patient",
            patient_email="walkin@test.com"
        )
        
        after_time = datetime.now()
        
        # Scheduled time should be between before and after (immediate)
        assert before_time <= appointment.scheduled_time <= after_time
    
    def test_register_walk_in_with_all_patient_details(self, db_session: Session, test_users):
        """Test walk-in registration with all optional patient details"""
        doctor = test_users["doctor"]
        
        from datetime import date
        dob = date(1990, 5, 15)  # Use date instead of datetime
        
        appointment, patient, is_new = AppointmentService.register_walk_in(
            db=db_session,
            doctor_id=doctor.id,
            patient_name="Complete Walk-in Patient",
            patient_email="complete@test.com",
            patient_phone="5551112222",
            gender="Female",
            date_of_birth=dob,
            address="123 Main St",
            blood_group="O+"
        )
        
        assert is_new is True
        assert patient.date_of_birth == dob
        assert patient.gender == "Female"
        assert patient.address == "123 Main St"
        assert patient.blood_group == "O+"
    
    def test_register_walk_in_endpoint_success(self, client: TestClient, db_session: Session, test_users):
        """Test walk-in registration endpoint with nurse role"""
        doctor = test_users["doctor"]
        
        # Create nurse user
        nurse_user = User(
            name="Nurse User",
            email="nurse@test.com",
            password_hash="$2b$12$test_hash",
            role=UserRole.NURSE
        )
        db_session.add(nurse_user)
        db_session.commit()
        db_session.refresh(nurse_user)
        
        # Generate token for nurse
        token = create_access_token(data={
            "user_id": nurse_user.id,
            "email": nurse_user.email,
            "role": nurse_user.role.value
        })
        
        response = client.post(
            "/api/v1/appointments/walk-in",
            json={
                "doctor_id": doctor.id,
                "patient_name": "Walk-in Patient",
                "patient_email": "walkin@test.com",
                "patient_phone": "5551234567",
                "gender": "Male"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["appointment_type"] == "walk_in"
        assert data["status"] == "checked_in"
        assert data["queue_position"] == 1
        assert "estimated_wait_time" in data
        assert data["patient_name"] == "Walk-in Patient"
    
    def test_register_walk_in_endpoint_admin_role(self, client: TestClient, db_session: Session, test_users):
        """Test walk-in registration endpoint with admin role"""
        doctor = test_users["doctor"]
        
        # Create admin user
        admin_user = User(
            name="Admin User",
            email="admin@test.com",
            password_hash="$2b$12$test_hash",
            role=UserRole.ADMIN
        )
        db_session.add(admin_user)
        db_session.commit()
        db_session.refresh(admin_user)
        
        # Generate token for admin
        token = create_access_token(data={
            "user_id": admin_user.id,
            "email": admin_user.email,
            "role": admin_user.role.value
        })
        
        response = client.post(
            "/api/v1/appointments/walk-in",
            json={
                "doctor_id": doctor.id,
                "patient_name": "Walk-in Patient Admin",
                "patient_email": "walkin_admin@test.com"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
    
    def test_register_walk_in_endpoint_patient_forbidden(self, client: TestClient, db_session: Session, test_users):
        """Test that patients cannot register walk-in patients"""
        patient_user = test_users["patient_user"]
        doctor = test_users["doctor"]
        
        # Generate token for patient
        token = create_access_token(data={
            "user_id": patient_user.id,
            "email": patient_user.email,
            "role": patient_user.role.value
        })
        
        response = client.post(
            "/api/v1/appointments/walk-in",
            json={
                "doctor_id": doctor.id,
                "patient_name": "Walk-in Patient",
                "patient_email": "walkin@test.com"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
    
    def test_register_walk_in_endpoint_doctor_forbidden(self, client: TestClient, db_session: Session, test_users):
        """Test that doctors cannot register walk-in patients"""
        doctor_user = test_users["doctor_user"]
        doctor = test_users["doctor"]
        
        # Generate token for doctor
        token = create_access_token(data={
            "user_id": doctor_user.id,
            "email": doctor_user.email,
            "role": doctor_user.role.value
        })
        
        response = client.post(
            "/api/v1/appointments/walk-in",
            json={
                "doctor_id": doctor.id,
                "patient_name": "Walk-in Patient",
                "patient_email": "walkin@test.com"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
    
    def test_register_walk_in_endpoint_unauthorized(self, client: TestClient, db_session: Session, test_users):
        """Test that walk-in registration requires authentication"""
        doctor = test_users["doctor"]
        
        response = client.post(
            "/api/v1/appointments/walk-in",
            json={
                "doctor_id": doctor.id,
                "patient_name": "Walk-in Patient",
                "patient_email": "walkin@test.com"
            }
        )
        
        assert response.status_code == 401
    
    def test_register_walk_in_endpoint_invalid_doctor(self, client: TestClient, db_session: Session, test_users):
        """Test walk-in registration with non-existent doctor"""
        # Create nurse user
        nurse_user = User(
            name="Nurse User",
            email="nurse@test.com",
            password_hash="$2b$12$test_hash",
            role=UserRole.NURSE
        )
        db_session.add(nurse_user)
        db_session.commit()
        db_session.refresh(nurse_user)
        
        # Generate token for nurse
        token = create_access_token(data={
            "user_id": nurse_user.id,
            "email": nurse_user.email,
            "role": nurse_user.role.value
        })
        
        response = client.post(
            "/api/v1/appointments/walk-in",
            json={
                "doctor_id": 99999,
                "patient_name": "Walk-in Patient",
                "patient_email": "walkin@test.com"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404
    
    def test_register_walk_in_endpoint_existing_patient(self, client: TestClient, db_session: Session, test_users):
        """Test walk-in registration for existing patient via endpoint"""
        doctor = test_users["doctor"]
        patient = test_users["patient"]
        patient_user = test_users["patient_user"]
        
        # Create nurse user
        nurse_user = User(
            name="Nurse User",
            email="nurse@test.com",
            password_hash="$2b$12$test_hash",
            role=UserRole.NURSE
        )
        db_session.add(nurse_user)
        db_session.commit()
        db_session.refresh(nurse_user)
        
        # Generate token for nurse
        token = create_access_token(data={
            "user_id": nurse_user.id,
            "email": nurse_user.email,
            "role": nurse_user.role.value
        })
        
        response = client.post(
            "/api/v1/appointments/walk-in",
            json={
                "doctor_id": doctor.id,
                "patient_name": "Different Name",
                "patient_email": patient_user.email  # Use existing patient email
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["patient_id"] == patient.id
        assert data["patient_name"] == patient_user.name  # Should use existing patient's name
    
    def test_register_walk_in_estimated_wait_time(self, client: TestClient, db_session: Session, test_users):
        """Test that walk-in registration returns estimated wait time"""
        doctor = test_users["doctor"]
        patient = test_users["patient"]
        
        # Create existing appointments in queue
        for i in range(2):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=datetime.now(),
                status=AppointmentStatus.CHECKED_IN,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=i + 1
            )
            db_session.add(appointment)
        db_session.commit()
        
        # Create nurse user
        nurse_user = User(
            name="Nurse User",
            email="nurse@test.com",
            password_hash="$2b$12$test_hash",
            role=UserRole.NURSE
        )
        db_session.add(nurse_user)
        db_session.commit()
        db_session.refresh(nurse_user)
        
        # Generate token for nurse
        token = create_access_token(data={
            "user_id": nurse_user.id,
            "email": nurse_user.email,
            "role": nurse_user.role.value
        })
        
        response = client.post(
            "/api/v1/appointments/walk-in",
            json={
                "doctor_id": doctor.id,
                "patient_name": "Walk-in Patient",
                "patient_email": "walkin@test.com"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["queue_position"] == 3
        # Estimated wait time should be (3-1) * 15 = 30 minutes
        assert data["estimated_wait_time"] == 30


class TestAppointmentStatusUpdate:
    """Test appointment status update functionality"""
    
    def test_update_status_scheduled_to_checked_in(self, db_session: Session, test_users):
        """Test status transition from SCHEDULED to CHECKED_IN"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        doctor_user = test_users["doctor_user"]
        
        # Create scheduled appointment
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=datetime.now() + timedelta(hours=1),
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment)
        db_session.commit()
        db_session.refresh(appointment)
        
        # Update status to CHECKED_IN
        updated = AppointmentService.update_appointment_status(
            db=db_session,
            appointment_id=appointment.id,
            new_status=AppointmentStatus.CHECKED_IN,
            user_id=doctor_user.id,
            user_role=doctor_user.role.value
        )
        
        assert updated.status == AppointmentStatus.CHECKED_IN
        assert updated.queue_position == 1  # Still in queue
    
    def test_update_status_checked_in_to_in_progress(self, db_session: Session, test_users):
        """Test status transition from CHECKED_IN to IN_PROGRESS"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        doctor_user = test_users["doctor_user"]
        
        # Create checked-in appointment
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=datetime.now(),
            status=AppointmentStatus.CHECKED_IN,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment)
        db_session.commit()
        db_session.refresh(appointment)
        
        # Update status to IN_PROGRESS
        before_time = datetime.now()
        updated = AppointmentService.update_appointment_status(
            db=db_session,
            appointment_id=appointment.id,
            new_status=AppointmentStatus.IN_PROGRESS,
            user_id=doctor_user.id,
            user_role=doctor_user.role.value
        )
        after_time = datetime.now()
        
        assert updated.status == AppointmentStatus.IN_PROGRESS
        assert updated.consultation_start_time is not None
        assert before_time <= updated.consultation_start_time <= after_time
        assert updated.queue_position == 1  # Still in queue
    
    def test_update_status_in_progress_to_completed(self, db_session: Session, test_users):
        """Test status transition from IN_PROGRESS to COMPLETED"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        doctor_user = test_users["doctor_user"]
        
        # Create in-progress appointment with consultation start time
        consultation_start = datetime.now() - timedelta(minutes=20)
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=datetime.now(),
            status=AppointmentStatus.IN_PROGRESS,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1,
            consultation_start_time=consultation_start
        )
        db_session.add(appointment)
        db_session.commit()
        db_session.refresh(appointment)
        
        # Store original average duration
        original_avg = doctor.average_consultation_duration
        
        # Update status to COMPLETED
        updated = AppointmentService.update_appointment_status(
            db=db_session,
            appointment_id=appointment.id,
            new_status=AppointmentStatus.COMPLETED,
            user_id=doctor_user.id,
            user_role=doctor_user.role.value
        )
        
        assert updated.status == AppointmentStatus.COMPLETED
        assert updated.queue_position is None  # Removed from queue
        
        # Verify average consultation duration was updated
        db_session.refresh(doctor)
        assert doctor.average_consultation_duration != original_avg
    
    def test_update_status_invalid_transition(self, db_session: Session, test_users):
        """Test that invalid status transitions are rejected"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        doctor_user = test_users["doctor_user"]
        
        # Create scheduled appointment
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=datetime.now() + timedelta(hours=1),
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment)
        db_session.commit()
        db_session.refresh(appointment)
        
        # Try to jump directly to COMPLETED (invalid)
        with pytest.raises(HTTPException) as exc_info:
            AppointmentService.update_appointment_status(
                db=db_session,
                appointment_id=appointment.id,
                new_status=AppointmentStatus.COMPLETED,
                user_id=doctor_user.id,
                user_role=doctor_user.role.value
            )
        
        assert exc_info.value.status_code == 400
        assert "invalid status transition" in exc_info.value.detail.lower()
    
    def test_update_status_patient_cannot_update(self, db_session: Session, test_users):
        """Test that patients cannot update appointment status"""
        patient = test_users["patient"]
        patient_user = test_users["patient_user"]
        doctor = test_users["doctor"]
        
        # Create scheduled appointment
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=datetime.now() + timedelta(hours=1),
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment)
        db_session.commit()
        db_session.refresh(appointment)
        
        # Try to update status as patient
        with pytest.raises(HTTPException) as exc_info:
            AppointmentService.update_appointment_status(
                db=db_session,
                appointment_id=appointment.id,
                new_status=AppointmentStatus.CHECKED_IN,
                user_id=patient_user.id,
                user_role=patient_user.role.value
            )
        
        assert exc_info.value.status_code == 403
        assert "only doctors and staff" in exc_info.value.detail.lower()
    
    def test_update_status_nurse_can_update(self, db_session: Session, test_users):
        """Test that nurses can update appointment status"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        
        # Create nurse user
        nurse_user = User(
            name="Nurse User",
            email="nurse@test.com",
            password_hash="$2b$12$test_hash",
            role=UserRole.NURSE
        )
        db_session.add(nurse_user)
        db_session.commit()
        db_session.refresh(nurse_user)
        
        # Create scheduled appointment
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=datetime.now() + timedelta(hours=1),
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        db_session.add(appointment)
        db_session.commit()
        db_session.refresh(appointment)
        
        # Nurse updates status
        updated = AppointmentService.update_appointment_status(
            db=db_session,
            appointment_id=appointment.id,
            new_status=AppointmentStatus.CHECKED_IN,
            user_id=nurse_user.id,
            user_role=nurse_user.role.value
        )
        
        assert updated.status == AppointmentStatus.CHECKED_IN
    
    def test_update_status_completed_updates_queue_positions(self, db_session: Session, test_users):
        """Test that completing appointment updates queue positions for remaining appointments"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        doctor_user = test_users["doctor_user"]
        
        # Create 3 appointments in queue
        appointments = []
        for i in range(3):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=datetime.now() + timedelta(hours=i),
                status=AppointmentStatus.IN_PROGRESS if i == 0 else AppointmentStatus.CHECKED_IN,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=i + 1,
                consultation_start_time=datetime.now() if i == 0 else None
            )
            db_session.add(appointment)
            appointments.append(appointment)
        db_session.commit()
        
        # Refresh all appointments
        for appointment in appointments:
            db_session.refresh(appointment)
        
        # Complete first appointment
        AppointmentService.update_appointment_status(
            db=db_session,
            appointment_id=appointments[0].id,
            new_status=AppointmentStatus.COMPLETED,
            user_id=doctor_user.id,
            user_role=doctor_user.role.value
        )
        
        # Refresh all appointments
        for appointment in appointments:
            db_session.refresh(appointment)
        
        # Verify queue positions updated
        assert appointments[0].queue_position is None  # Completed
        assert appointments[1].queue_position == 1  # Moved from 2 to 1
        assert appointments[2].queue_position == 2  # Moved from 3 to 2
    
    def test_update_status_not_found(self, db_session: Session, test_users):
        """Test updating status of non-existent appointment"""
        doctor_user = test_users["doctor_user"]
        
        with pytest.raises(HTTPException) as exc_info:
            AppointmentService.update_appointment_status(
                db=db_session,
                appointment_id=99999,
                new_status=AppointmentStatus.CHECKED_IN,
                user_id=doctor_user.id,
                user_role=doctor_user.role.value
            )
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()
    
    def test_update_status_from_cancelled(self, db_session: Session, test_users):
        """Test that cancelled appointments cannot have status updated"""
        patient = test_users["patient"]
        doctor = test_users["doctor"]
        doctor_user = test_users["doctor_user"]
        
        # Create cancelled appointment
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=datetime.now() + timedelta(hours=1),
            status=AppointmentStatus.CANCELLED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=None
        )
        db_session.add(appointment)
        db_session.commit()
        db_session.refresh(appointment)
        
        # Try to update status
        with pytest.raises(HTTPException) as exc_info:
            AppointmentService.update_appointment_status(
                db=db_session,
                appointment_id=appointment.id,
                new_status=AppointmentStatus.CHECKED_IN,
                user_id=doctor_user.id,
                user_role=doctor_user.role.value
            )
        
        assert exc_info.value.status_code == 400
        assert "cannot transition" in exc_info.value.detail.lower()


class TestAverageConsultationDuration:
    """Test average consultation duration tracking"""
    
    def test_update_average_consultation_duration(self, db_session: Session, test_users):
        """Test updating average consultation duration using EMA"""
        doctor = test_users["doctor"]
        
        # Initial average is 15 minutes
        assert doctor.average_consultation_duration == 15
        
        # Simulate a 20-minute consultation
        AppointmentService.update_average_consultation_duration(
            db=db_session,
            doctor_id=doctor.id,
            actual_duration=20
        )
        
        db_session.refresh(doctor)
        
        # New average = (0.2 * 20) + (0.8 * 15) = 4 + 12 = 16
        assert doctor.average_consultation_duration == 16
    
    def test_update_average_with_shorter_duration(self, db_session: Session, test_users):
        """Test that shorter consultations decrease the average"""
        doctor = test_users["doctor"]
        
        # Initial average is 15 minutes
        assert doctor.average_consultation_duration == 15
        
        # Simulate a 10-minute consultation
        AppointmentService.update_average_consultation_duration(
            db=db_session,
            doctor_id=doctor.id,
            actual_duration=10
        )
        
        db_session.refresh(doctor)
        
        # New average = (0.2 * 10) + (0.8 * 15) = 2 + 12 = 14
        assert doctor.average_consultation_duration == 14
    
    def test_update_average_multiple_consultations(self, db_session: Session, test_users):
        """Test that average smooths out over multiple consultations"""
        doctor = test_users["doctor"]
        
        # Initial average is 15 minutes
        original_avg = doctor.average_consultation_duration
        
        # Simulate multiple consultations
        durations = [20, 25, 10, 15, 18]
        for duration in durations:
            AppointmentService.update_average_consultation_duration(
                db=db_session,
                doctor_id=doctor.id,
                actual_duration=duration
            )
            db_session.refresh(doctor)
        
        # Average should have changed but not drastically (EMA smoothing)
        assert doctor.average_consultation_duration != original_avg
        # Should be somewhere between min and max of durations
        assert 10 <= doctor.average_consultation_duration <= 25
    
    def test_update_average_invalid_doctor(self, db_session: Session):
        """Test updating average for non-existent doctor (should not raise error)"""
        # Should handle gracefully without raising exception
        AppointmentService.update_average_consultation_duration(
            db=db_session,
            doctor_id=99999,
            actual_duration=20
        )
        # No assertion needed - just verify it doesn't crash


class TestQueueManagement:
    """Test queue management functionality"""
    
    def test_get_doctor_queue_empty(self, db_session: Session, test_users):
        """Test getting queue for doctor with no appointments"""
        doctor = test_users["doctor"]
        
        queue_data = AppointmentService.get_doctor_queue(
            db=db_session,
            doctor_id=doctor.id
        )
        
        assert queue_data["doctor_id"] == doctor.id
        assert queue_data["total_queue_length"] == 0
        assert len(queue_data["patients"]) == 0
        assert "doctor_name" in queue_data
        assert "doctor_specialization" in queue_data
        assert "average_consultation_duration" in queue_data
    
    def test_get_doctor_queue_with_appointments(self, db_session: Session, test_users):
        """Test getting queue with multiple appointments"""
        doctor = test_users["doctor"]
        patient = test_users["patient"]
        
        # Create 3 appointments in queue
        for i in range(3):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=datetime.now() + timedelta(hours=i),
                status=AppointmentStatus.CHECKED_IN,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=i + 1
            )
            db_session.add(appointment)
        db_session.commit()
        
        queue_data = AppointmentService.get_doctor_queue(
            db=db_session,
            doctor_id=doctor.id
        )
        
        assert queue_data["total_queue_length"] == 3
        assert len(queue_data["patients"]) == 3
        
        # Verify patients are sorted by queue position
        for i, patient_data in enumerate(queue_data["patients"]):
            assert patient_data["queue_position"] == i + 1
            assert "patient_name" in patient_data
            assert "estimated_wait_time" in patient_data
            assert "status" in patient_data
    
    def test_get_doctor_queue_excludes_completed(self, db_session: Session, test_users):
        """Test that completed appointments are not in queue"""
        doctor = test_users["doctor"]
        patient = test_users["patient"]
        
        # Create appointments with different statuses
        statuses = [
            AppointmentStatus.SCHEDULED,
            AppointmentStatus.CHECKED_IN,
            AppointmentStatus.IN_PROGRESS,
            AppointmentStatus.COMPLETED,
            AppointmentStatus.CANCELLED
        ]
        
        for i, status in enumerate(statuses):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=datetime.now() + timedelta(hours=i),
                status=status,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=i + 1 if status in [AppointmentStatus.SCHEDULED, AppointmentStatus.CHECKED_IN, AppointmentStatus.IN_PROGRESS] else None
            )
            db_session.add(appointment)
        db_session.commit()
        
        queue_data = AppointmentService.get_doctor_queue(
            db=db_session,
            doctor_id=doctor.id
        )
        
        # Only SCHEDULED, CHECKED_IN, IN_PROGRESS should be in queue
        assert queue_data["total_queue_length"] == 3
    
    def test_get_doctor_queue_invalid_doctor(self, db_session: Session):
        """Test getting queue for non-existent doctor"""
        with pytest.raises(HTTPException) as exc_info:
            AppointmentService.get_doctor_queue(
                db=db_session,
                doctor_id=99999
            )
        
        assert exc_info.value.status_code == 404
        assert "Doctor" in exc_info.value.detail
    
    def test_get_all_queues_status(self, db_session: Session, test_users):
        """Test getting queue status for all doctors"""
        doctor = test_users["doctor"]
        patient = test_users["patient"]
        
        # Create another doctor
        doctor_user2 = User(
            name="Dr. Test 2",
            email="doctor2@test.com",
            password_hash="$2b$12$test_hash",
            role=UserRole.DOCTOR
        )
        db_session.add(doctor_user2)
        db_session.flush()
        
        doctor2 = Doctor(
            user_id=doctor_user2.id,
            specialization="Neurology",
            license_number="DOC456",
            average_consultation_duration=20
        )
        db_session.add(doctor2)
        db_session.commit()
        db_session.refresh(doctor2)
        
        # Create appointments for both doctors
        for i in range(2):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=datetime.now() + timedelta(hours=i),
                status=AppointmentStatus.CHECKED_IN,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=i + 1
            )
            db_session.add(appointment)
        
        for i in range(3):
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor2.id,
                scheduled_time=datetime.now() + timedelta(hours=i),
                status=AppointmentStatus.SCHEDULED,
                appointment_type=AppointmentType.SCHEDULED,
                queue_position=i + 1
            )
            db_session.add(appointment)
        db_session.commit()
        
        # Get all queues status
        queues = AppointmentService.get_all_queues_status(db=db_session)
        
        assert len(queues) == 2
        
        # Find each doctor's queue
        doctor1_queue = next(q for q in queues if q["doctor_id"] == doctor.id)
        doctor2_queue = next(q for q in queues if q["doctor_id"] == doctor2.id)
        
        assert doctor1_queue["queue_length"] == 2
        assert doctor2_queue["queue_length"] == 3
        
        # Verify all required fields
        for queue in queues:
            assert "doctor_id" in queue
            assert "doctor_name" in queue
            assert "doctor_specialization" in queue
            assert "queue_length" in queue
            assert "average_wait_time" in queue
    
    def test_get_all_queues_status_empty_queues(self, db_session: Session, test_users):
        """Test getting all queues when no appointments exist"""
        queues = AppointmentService.get_all_queues_status(db=db_session)
        
        # Should return all doctors with queue_length = 0
        assert len(queues) >= 1  # At least the test doctor
        
        for queue in queues:
            assert queue["queue_length"] == 0
            assert queue["average_wait_time"] == 0
