"""
Tests for SQLAlchemy model structure
Tests model definitions without requiring database connection
"""
import pytest
import sys
import os
from datetime import datetime, date

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set required environment variables before importing models
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-testing-only')

from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.appointment import Appointment, AppointmentStatus, AppointmentType
from app.models.medical_record import MedicalRecord
from app.models.audit_chain import AuditChain


class TestUserModel:
    """Test User model"""
    
    def test_user_model_attributes(self):
        """Test that User model has all required attributes"""
        user = User(
            name="John Doe",
            email="john@example.com",
            password_hash="hashed_password",
            role=UserRole.PATIENT
        )
        
        assert user.name == "John Doe"
        assert user.email == "john@example.com"
        assert user.password_hash == "hashed_password"
        assert user.role == UserRole.PATIENT
    
    def test_user_role_enum(self):
        """Test UserRole enum values"""
        assert UserRole.ADMIN == "Admin"
        assert UserRole.DOCTOR == "Doctor"
        assert UserRole.NURSE == "Nurse"
        assert UserRole.PATIENT == "Patient"
    
    def test_user_tablename(self):
        """Test User table name"""
        assert User.__tablename__ == "users"


class TestPatientModel:
    """Test Patient model"""
    
    def test_patient_model_attributes(self):
        """Test that Patient model has all required attributes"""
        patient = Patient(
            user_id=1,
            date_of_birth=date(1990, 1, 1),
            gender="Male",
            phone="1234567890",
            address="123 Main St",
            blood_group="O+"
        )
        
        assert patient.user_id == 1
        assert patient.date_of_birth == date(1990, 1, 1)
        assert patient.gender == "Male"
        assert patient.phone == "1234567890"
        assert patient.address == "123 Main St"
        assert patient.blood_group == "O+"
    
    def test_patient_tablename(self):
        """Test Patient table name"""
        assert Patient.__tablename__ == "patients"


class TestDoctorModel:
    """Test Doctor model"""
    
    def test_doctor_model_attributes(self):
        """Test that Doctor model has all required attributes"""
        doctor = Doctor(
            user_id=2,
            specialization="Cardiology",
            license_number="LIC123456",
            average_consultation_duration=20
        )
        
        assert doctor.user_id == 2
        assert doctor.specialization == "Cardiology"
        assert doctor.license_number == "LIC123456"
        assert doctor.average_consultation_duration == 20
    
    def test_doctor_default_consultation_duration(self):
        """Test default consultation duration"""
        doctor = Doctor(user_id=2, specialization="Pediatrics")
        assert doctor.average_consultation_duration == 15
    
    def test_doctor_tablename(self):
        """Test Doctor table name"""
        assert Doctor.__tablename__ == "doctors"


class TestAppointmentModel:
    """Test Appointment model"""
    
    def test_appointment_model_attributes(self):
        """Test that Appointment model has all required attributes"""
        scheduled_time = datetime(2026, 3, 1, 10, 0, 0)
        appointment = Appointment(
            patient_id=1,
            doctor_id=1,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.SCHEDULED,
            queue_position=1
        )
        
        assert appointment.patient_id == 1
        assert appointment.doctor_id == 1
        assert appointment.scheduled_time == scheduled_time
        assert appointment.status == AppointmentStatus.SCHEDULED
        assert appointment.appointment_type == AppointmentType.SCHEDULED
        assert appointment.queue_position == 1
    
    def test_appointment_status_enum(self):
        """Test AppointmentStatus enum values"""
        assert AppointmentStatus.SCHEDULED == "scheduled"
        assert AppointmentStatus.CHECKED_IN == "checked_in"
        assert AppointmentStatus.IN_PROGRESS == "in_progress"
        assert AppointmentStatus.COMPLETED == "completed"
        assert AppointmentStatus.CANCELLED == "cancelled"
    
    def test_appointment_type_enum(self):
        """Test AppointmentType enum values"""
        assert AppointmentType.SCHEDULED == "scheduled"
        assert AppointmentType.WALK_IN == "walk_in"
    
    def test_appointment_tablename(self):
        """Test Appointment table name"""
        assert Appointment.__tablename__ == "appointments"


class TestMedicalRecordModel:
    """Test MedicalRecord model"""
    
    def test_medical_record_model_attributes(self):
        """Test that MedicalRecord model has all required attributes"""
        record = MedicalRecord(
            patient_id=1,
            doctor_id=1,
            appointment_id=1,
            consultation_notes="Patient complains of headache",
            diagnosis="Migraine",
            prescription="Ibuprofen 400mg, twice daily",
            version_number=1,
            created_by=1
        )
        
        assert record.patient_id == 1
        assert record.doctor_id == 1
        assert record.appointment_id == 1
        assert record.consultation_notes == "Patient complains of headache"
        assert record.diagnosis == "Migraine"
        assert record.prescription == "Ibuprofen 400mg, twice daily"
        assert record.version_number == 1
        assert record.created_by == 1
    
    def test_medical_record_default_version(self):
        """Test default version number"""
        record = MedicalRecord(
            patient_id=1,
            doctor_id=1,
            consultation_notes="Test",
            created_by=1
        )
        assert record.version_number == 1
    
    def test_medical_record_tablename(self):
        """Test MedicalRecord table name"""
        assert MedicalRecord.__tablename__ == "medical_records"


class TestAuditChainModel:
    """Test AuditChain model"""
    
    def test_audit_chain_model_attributes(self):
        """Test that AuditChain model has all required attributes"""
        audit = AuditChain(
            record_id=1,
            record_type="medical_record",
            record_data={"test": "data"},
            hash="abc123",
            previous_hash="0",
            user_id=1,
            is_tampered=False
        )
        
        assert audit.record_id == 1
        assert audit.record_type == "medical_record"
        assert audit.record_data == {"test": "data"}
        assert audit.hash == "abc123"
        assert audit.previous_hash == "0"
        assert audit.user_id == 1
        assert audit.is_tampered == False
    
    def test_audit_chain_default_tampered_flag(self):
        """Test default is_tampered flag"""
        audit = AuditChain(
            record_id=1,
            record_type="appointment",
            record_data={},
            hash="hash123",
            previous_hash="0"
        )
        assert audit.is_tampered == False
    
    def test_audit_chain_tablename(self):
        """Test AuditChain table name"""
        assert AuditChain.__tablename__ == "audit_chain"


class TestModelStructure:
    """Test model structure and column definitions"""
    
    def test_all_models_have_tablename(self):
        """Test that all models have __tablename__ defined"""
        models = [User, Patient, Doctor, Appointment, MedicalRecord, AuditChain]
        for model in models:
            assert hasattr(model, '__tablename__')
            assert isinstance(model.__tablename__, str)
            assert len(model.__tablename__) > 0
    
    def test_user_has_required_columns(self):
        """Test User model has required columns"""
        required_columns = ['name', 'email', 'password_hash', 'role']
        for col in required_columns:
            assert hasattr(User, col)
    
    def test_patient_has_required_columns(self):
        """Test Patient model has required columns"""
        required_columns = ['user_id', 'date_of_birth', 'gender', 'phone', 'address', 'blood_group']
        for col in required_columns:
            assert hasattr(Patient, col)
    
    def test_doctor_has_required_columns(self):
        """Test Doctor model has required columns"""
        required_columns = ['user_id', 'specialization', 'license_number', 'average_consultation_duration']
        for col in required_columns:
            assert hasattr(Doctor, col)
    
    def test_appointment_has_required_columns(self):
        """Test Appointment model has required columns"""
        required_columns = ['patient_id', 'doctor_id', 'scheduled_time', 'status', 'appointment_type', 'queue_position']
        for col in required_columns:
            assert hasattr(Appointment, col)
    
    def test_medical_record_has_required_columns(self):
        """Test MedicalRecord model has required columns"""
        required_columns = ['patient_id', 'doctor_id', 'appointment_id', 'consultation_notes', 'diagnosis', 'prescription', 'version_number', 'parent_record_id', 'created_by']
        for col in required_columns:
            assert hasattr(MedicalRecord, col)
    
    def test_audit_chain_has_required_columns(self):
        """Test AuditChain model has required columns"""
        required_columns = ['record_id', 'record_type', 'record_data', 'hash', 'previous_hash', 'timestamp', 'user_id', 'is_tampered']
        for col in required_columns:
            assert hasattr(AuditChain, col)
