"""
Patient schemas for search results
"""
from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class PatientSearchResult(BaseModel):
    """Single patient row returned by the search endpoint."""
    id: int
    user_id: int
    name: str
    phone: Optional[str] = None
    blood_group: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    age: Optional[int] = None

    class Config:
        from_attributes = True


class PatientSearchResponse(BaseModel):
    """Paginated patient search response."""
    results: List[PatientSearchResult]
    total: int
    page: int
    page_size: int
