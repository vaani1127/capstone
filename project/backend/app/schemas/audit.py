"""
Audit schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class AuditLogResponse(BaseModel):
    """Schema for audit log entry response"""
    id: int
    record_id: int
    record_type: str
    record_data: dict
    hash: str
    previous_hash: str
    timestamp: datetime
    user_id: Optional[int]
    is_tampered: bool
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    
    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Schema for paginated audit log list response"""
    total: int
    page: int
    page_size: int
    total_pages: int
    logs: list[AuditLogResponse]


class TamperingAlertResponse(BaseModel):
    """Schema for tampering alert response"""
    id: int
    record_id: int
    record_type: str
    hash: str
    timestamp: datetime
    user_id: Optional[int]
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    
    class Config:
        from_attributes = True


class IntegrityVerificationResponse(BaseModel):
    """Schema for integrity verification response"""
    record_id: int
    record_type: str
    is_valid: bool
    stored_hash: str
    computed_hash: str
    message: str
