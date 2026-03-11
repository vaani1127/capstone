"""
Doctor model for doctor credentials and consultation metrics
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class Doctor(BaseModel):
    """
    Doctor model for storing doctor credentials and consultation metrics.
    
    Attributes:
        id: Primary key (inherited from Base)
        user_id: Foreign key to users table
        specialization: Medical specialization (e.g., Cardiology, Pediatrics)
        license_number: Medical license number
        average_consultation_duration: Rolling average consultation time in minutes
        created_at: Timestamp when record was created (inherited from Base)
    
    Relationships:
        user: Associated user account
        appointments: All appointments for this doctor
        medical_records: All medical records created by this doctor
    """
    __tablename__ = "doctors"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    specialization = Column(String(255), index=True)
    license_number = Column(String(100))
    average_consultation_duration = Column(Integer, default=15)  # in minutes
    
    # Relationships
    user = relationship("User", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="doctor", cascade="all, delete-orphan")
    medical_records = relationship("MedicalRecord", back_populates="doctor")
    
    def __repr__(self):
        return f"<Doctor(id={self.id}, specialization='{self.specialization}')>"
