"""
Vitals schemas for request/response validation
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class VitalsCreate(BaseModel):
    """Schema for recording a new set of vitals."""
    patient_id: int = Field(..., gt=0, description="Patient record ID")
    appointment_id: Optional[int] = Field(None, description="Associated appointment (optional)")
    systolic_bp: Optional[int] = Field(None, ge=0, le=300, description="Systolic BP in mmHg")
    diastolic_bp: Optional[int] = Field(None, ge=0, le=200, description="Diastolic BP in mmHg")
    heart_rate: Optional[int] = Field(None, ge=0, le=300, description="Heart rate in bpm")
    temperature: Optional[float] = Field(None, ge=86.0, le=113.0, description="Temperature in degrees Fahrenheit")
    respiratory_rate: Optional[int] = Field(None, ge=0, le=100, description="Respiratory rate in breaths/min")
    oxygen_saturation: Optional[float] = Field(None, ge=0.0, le=100.0, description="SpO2 percentage")
    weight_kg: Optional[float] = Field(None, gt=0, le=700, description="Weight in kilograms")
    height_cm: Optional[float] = Field(None, gt=0, le=300, description="Height in centimetres")
    notes: Optional[str] = Field(None, description="Free-text clinical notes")


class VitalsResponse(BaseModel):
    """Full vitals record returned by the API."""
    id: int
    patient_id: int
    appointment_id: Optional[int] = None
    recorded_by: int
    recorded_by_name: Optional[str] = None
    recorded_at: datetime
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    heart_rate: Optional[int] = None
    temperature: Optional[float] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    bmi: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class VitalsListResponse(BaseModel):
    """Paginated list of vitals records."""
    vitals: List[VitalsResponse]
    total: int
