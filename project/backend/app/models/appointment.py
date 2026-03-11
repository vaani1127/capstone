"""
Appointment model for managing appointments and queue system
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.db.base import BaseModel


class AppointmentStatus(str, enum.Enum):
    """Appointment status enumeration"""
    SCHEDULED = "scheduled"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AppointmentType(str, enum.Enum):
    """Appointment type enumeration"""
    SCHEDULED = "scheduled"
    WALK_IN = "walk_in"


class Appointment(BaseModel):
    """
    Appointment model for managing appointments and queue system.
    
    Attributes:
        id: Primary key (inherited from Base)
        patient_id: Foreign key to patients table
        doctor_id: Foreign key to doctors table
        scheduled_time: Scheduled appointment time
        status: Current appointment status
        appointment_type: Type of appointment (scheduled or walk-in)
        queue_position: Position in doctor's queue (NULL if not in queue)
        created_at: Timestamp when appointment was created (inherited from Base)
        updated_at: Timestamp when appointment was last updated (inherited from Base)
    
    Relationships:
        patient: Associated patient
        doctor: Associated doctor
        medical_records: Medical records created during this appointment
    """
    __tablename__ = "appointments"
    
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), index=True)
    scheduled_time = Column(DateTime, nullable=False, index=True)
    status = Column(
        SQLEnum(AppointmentStatus, name="appointment_status", create_type=False),
        default=AppointmentStatus.SCHEDULED,
        nullable=False,
        index=True
    )
    appointment_type = Column(
        SQLEnum(AppointmentType, name="appointment_type_enum", create_type=False),
        default=AppointmentType.SCHEDULED,
        nullable=False
    )
    queue_position = Column(Integer)
    consultation_start_time = Column(DateTime)  # Track when consultation started (IN_PROGRESS)
    
    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    medical_records = relationship("MedicalRecord", back_populates="appointment")
    
    def __repr__(self):
        return f"<Appointment(id={self.id}, patient_id={self.patient_id}, doctor_id={self.doctor_id}, status='{self.status}')>"
