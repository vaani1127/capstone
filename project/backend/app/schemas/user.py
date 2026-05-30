"""
User schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8, max_length=72)
    role: UserRole
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    email: str  # override EmailStr — walk-in patients use internal placeholder emails
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for admin user update (PUT /users/{user_id})"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None


class UserRoleUpdate(BaseModel):
    """Schema for admin role change (PATCH /users/{user_id}/role)"""
    role: UserRole


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse




class TokenRefresh(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str


class DoctorProfileResponse(BaseModel):
    """Doctor profile with user info — for any authenticated user"""
    id: int
    user_id: int
    name: str
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    average_consultation_duration: int = 15

    class Config:
        from_attributes = True
