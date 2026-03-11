"""
Patient model for patient demographic information
"""
from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class Patient(BaseModel):
    """
    Patient model for storing patient demographic and contact information.
    
    Attributes:
        id: Primary key (inherited from Base)
        user_id: Foreign key to users table
        date_of_birth: Patient's date of birth
        gender: Patient's gender
        phone: Contact phone number
        address: Residential address
        blood_group: Blood group (e.g., A+, O-, AB+)
        created_at: Timestamp when record was created (inherited from Base)
    
    Relationships:
        user: Associated user account
        appointments: All appointments for this patient
        medical_records: All medical records for this patient
    """
    __tablename__ = "patients"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    date_of_birth = Column(Date)
    gender = Column(String(20))
    phone = Column(String(20))
    address = Column(Text)
    blood_group = Column(String(10))
    
    # Relationships
    user = relationship("User", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    medical_records = relationship("MedicalRecord", back_populates="patient")
    
    def __repr__(self):
        return f"<Patient(id={self.id}, user_id={self.user_id})>"
