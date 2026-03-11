"""
Medical record schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ConsultationNoteCreate(BaseModel):
    """Schema for creating a consultation note"""
    appointment_id: int = Field(..., gt=0, description="ID of the appointment")
    consultation_notes: str = Field(..., min_length=1, description="Consultation notes")
    diagnosis: Optional[str] = Field(None, description="Medical diagnosis")


class ConsultationNoteResponse(BaseModel):
    """Schema for consultation note response"""
    id: int
    patient_id: int
    doctor_id: int
    appointment_id: Optional[int]
    consultation_notes: Optional[str]
    diagnosis: Optional[str]
    prescription: Optional[str]
    version_number: int
    parent_record_id: Optional[int]
    created_by: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class PrescriptionCreate(BaseModel):
    """Schema for creating a prescription"""
    appointment_id: int = Field(..., gt=0, description="ID of the appointment")
    medication: str = Field(..., min_length=1, description="Medication name")
    dosage: str = Field(..., min_length=1, description="Dosage information")
    frequency: str = Field(..., min_length=1, description="Frequency of medication")
    duration: str = Field(..., min_length=1, description="Duration of treatment")


class PrescriptionUpdate(BaseModel):
    """Schema for updating a prescription"""
    medication: str = Field(..., min_length=1, description="Medication name")
    dosage: str = Field(..., min_length=1, description="Dosage information")
    frequency: str = Field(..., min_length=1, description="Frequency of medication")
    duration: str = Field(..., min_length=1, description="Duration of treatment")


class MedicalRecordUpdate(BaseModel):
    """Schema for updating a medical record"""
    consultation_notes: Optional[str] = Field(None, min_length=1)
    diagnosis: Optional[str] = None
    prescription: Optional[str] = None


class MedicalRecordResponse(BaseModel):
    """Schema for medical record response with additional details"""
    id: int
    patient_id: int
    patient_name: Optional[str] = None
    doctor_id: int
    doctor_name: Optional[str] = None
    appointment_id: Optional[int]
    consultation_notes: Optional[str]
    diagnosis: Optional[str]
    prescription: Optional[str]
    version_number: int
    parent_record_id: Optional[int]
    created_by: int
    created_at: datetime
    is_tampered: bool = False
    
    class Config:
        from_attributes = True
