"""
Procedure schemas for request/response validation
"""
import bleach
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


def _strip_html(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    return bleach.clean(value, tags=[], attributes={}, strip=True)


class ProcedureCreate(BaseModel):
    """Schema for recording a new clinical procedure (Doctor only)."""
    patient_id: int = Field(..., gt=0, description="Patient record ID")
    encounter_id: Optional[int] = Field(None, description="Associated appointment/encounter")
    procedure_code: Optional[str] = Field(None, max_length=20, description="ICD or CPT code")
    description: str = Field(..., min_length=1, description="Description of the procedure")
    performed_at: datetime = Field(..., description="Date and time the procedure was performed")
    duration_minutes: Optional[int] = Field(None, ge=0, description="Procedure duration in minutes")
    outcome: Optional[str] = Field(None, description="Clinical outcome or result")
    base_cost: Optional[float] = Field(None, ge=0, description="List price before insurance")
    notes: Optional[str] = Field(None, description="Free-text clinical notes")

    @field_validator('description', 'outcome', 'notes', mode='before')
    @classmethod
    def sanitize_text(cls, value: Optional[str]) -> Optional[str]:
        return _strip_html(value)


class ProcedureResponse(BaseModel):
    """Full procedure record returned by the API."""
    id: int
    patient_id: int
    encounter_id: Optional[int] = None
    performed_by: Optional[int] = None
    performed_by_name: Optional[str] = None
    procedure_code: Optional[str] = None
    description: str
    performed_at: datetime
    duration_minutes: Optional[int] = None
    outcome: Optional[str] = None
    base_cost: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProcedureListResponse(BaseModel):
    """List of procedure records with total count."""
    procedures: List[ProcedureResponse]
    total: int
