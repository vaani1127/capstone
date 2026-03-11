"""
Appointment schemas for request/response validation
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from app.models.appointment import AppointmentStatus, AppointmentType


class AppointmentBase(BaseModel):
    """Base appointment schema"""
    doctor_id: int = Field(..., gt=0)
    scheduled_time: datetime


class AppointmentCreate(AppointmentBase):
    """Schema for creating a new appointment"""
    pass


class AppointmentResponse(AppointmentBase):
    """Schema for appointment response"""
    id: int
    patient_id: int
    status: AppointmentStatus
    appointment_type: AppointmentType
    queue_position: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AppointmentWithDetails(AppointmentResponse):
    """Schema for appointment with patient and doctor details"""
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    doctor_specialization: Optional[str] = None
    estimated_wait_time: Optional[int] = None  # in minutes


class AppointmentUpdate(BaseModel):
    """Schema for updating an appointment"""
    scheduled_time: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None


class RescheduleRequest(BaseModel):
    """Schema for rescheduling an appointment"""
    new_scheduled_time: datetime = Field(..., description="New scheduled time for the appointment")


class WalkInCreate(BaseModel):
    """Schema for walk-in patient registration"""
    doctor_id: int = Field(..., gt=0)
    patient_name: str = Field(..., min_length=1, max_length=255)
    patient_email: Optional[str] = None
    patient_phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    blood_group: Optional[str] = None


class QueuePatient(BaseModel):
    """Schema for patient in queue"""
    appointment_id: int
    patient_id: int
    patient_name: str
    queue_position: int
    estimated_wait_time: int  # in minutes
    status: AppointmentStatus
    scheduled_time: datetime
    
    class Config:
        from_attributes = True


class DoctorQueueResponse(BaseModel):
    """Schema for doctor queue status response"""
    doctor_id: int
    doctor_name: str
    doctor_specialization: str
    average_consultation_duration: int  # in minutes
    total_queue_length: int
    patients: List[QueuePatient]
    
    class Config:
        from_attributes = True


class QueueStatusSummary(BaseModel):
    """Schema for overall queue status summary"""
    doctor_id: int
    doctor_name: str
    doctor_specialization: str
    queue_length: int
    average_wait_time: int  # in minutes
    
    class Config:
        from_attributes = True


class StatusUpdateRequest(BaseModel):
    """Schema for updating appointment status"""
    status: AppointmentStatus = Field(..., description="New status for the appointment")
    
    @validator('status')
    def validate_status_transition(cls, v):
        """Validate that status is a valid transition status"""
        # Only allow transitions to these statuses
        allowed_statuses = [
            AppointmentStatus.CHECKED_IN,
            AppointmentStatus.IN_PROGRESS,
            AppointmentStatus.COMPLETED
        ]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {[s.value for s in allowed_statuses]}")
        return v
