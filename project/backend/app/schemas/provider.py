"""
Provider schemas for request/response validation
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ProviderCreate(BaseModel):
    """Schema for creating a provider record."""
    user_id: Optional[int] = None
    organization_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=255)
    gender: Optional[str] = None
    speciality: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    encounter_count: int = 0
    procedure_count: int = 0


class ProviderResponse(BaseModel):
    """Full provider record returned by the API."""
    id: int
    user_id: Optional[int] = None
    organization_id: Optional[int] = None
    organization_name: Optional[str] = None
    name: str
    gender: Optional[str] = None
    speciality: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    encounter_count: int = 0
    procedure_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class ProviderListResponse(BaseModel):
    """Paginated list of providers."""
    providers: List[ProviderResponse]
    total: int
    page: int
    page_size: int
