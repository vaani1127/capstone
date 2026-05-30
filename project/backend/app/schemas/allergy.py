"""
Allergy schemas for request/response validation
"""
from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class AllergyCreate(BaseModel):
    """Schema for recording a new allergy (Doctor or Nurse)."""
    patient_id: int = Field(..., gt=0, description="Patient record ID")
    allergen: str = Field(..., min_length=1, max_length=255, description="Name of the allergen")
    reaction: Optional[str] = Field(None, description="Description of the allergic reaction")
    severity: Literal['mild', 'moderate', 'severe'] = Field(
        ..., description="Clinical severity of the allergy"
    )
    onset_date: Optional[date] = Field(None, description="Date allergy first appeared")
    notes: Optional[str] = Field(None, description="Free-text clinical notes")


class AllergyResponse(BaseModel):
    """Full allergy record returned by the API."""
    id: int
    patient_id: int
    recorded_by: int
    recorded_by_name: Optional[str] = None
    allergen: str
    reaction: Optional[str] = None
    severity: str
    onset_date: Optional[date] = None
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AllergyListResponse(BaseModel):
    """List of allergy records with total count."""
    allergies: List[AllergyResponse]
    total: int
