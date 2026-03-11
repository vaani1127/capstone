"""
Medical record model for storing consultation notes and prescriptions with versioning
"""
from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class MedicalRecord(BaseModel):
    """
    Medical record model for storing consultation notes, diagnoses, and prescriptions.
    Supports version control for record updates.
    
    Attributes:
        id: Primary key (inherited from Base)
        patient_id: Foreign key to patients table
        doctor_id: Foreign key to doctors table
        appointment_id: Foreign key to appointments table (nullable)
        consultation_notes: Doctor's consultation notes
        diagnosis: Medical diagnosis
        prescription: Prescription details (medication, dosage, frequency, duration)
        version_number: Version number for record versioning
        parent_record_id: Foreign key to parent record for version tracking
        created_by: Foreign key to users table (who created this record)
        created_at: Timestamp when record was created (inherited from Base)
    
    Relationships:
        patient: Associated patient
        doctor: Associated doctor
        appointment: Associated appointment
        creator: User who created this record
        parent_record: Parent record for version tracking
        child_records: Child records (newer versions)
    """
    __tablename__ = "medical_records"
    
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id", ondelete="SET NULL"), index=True)
    consultation_notes = Column(Text)
    diagnosis = Column(Text)
    prescription = Column(Text)
    version_number = Column(Integer, default=1, nullable=False)
    parent_record_id = Column(Integer, ForeignKey("medical_records.id", ondelete="SET NULL"), index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    
    # Relationships
    patient = relationship("Patient", back_populates="medical_records")
    doctor = relationship("Doctor", back_populates="medical_records")
    appointment = relationship("Appointment", back_populates="medical_records")
    creator = relationship("User", foreign_keys=[created_by], back_populates="medical_records_created")
    parent_record = relationship("MedicalRecord", remote_side="MedicalRecord.id", foreign_keys=[parent_record_id], backref="child_records")
    
    def __repr__(self):
        return f"<MedicalRecord(id={self.id}, patient_id={self.patient_id}, version={self.version_number})>"
