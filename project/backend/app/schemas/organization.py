"""
Organization schemas for request/response validation
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    """Schema for creating an organisation record."""
    name: str = Field(..., min_length=1, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    phone: Optional[str] = None
    revenue: Optional[float] = None
    utilization: Optional[float] = None
    lat: Optional[float] = None
    lon: Optional[float] = None


class OrganizationResponse(BaseModel):
    """Full organisation record returned by the API."""
    id: int
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    phone: Optional[str] = None
    revenue: Optional[float] = None
    utilization: Optional[float] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OrganizationListResponse(BaseModel):
    """Paginated list of organisations."""
    organizations: List[OrganizationResponse]
    total: int
    page: int
    page_size: int
