"""
User model for authentication and role-based access control
"""
from sqlalchemy import Column, String, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.db.base import BaseModel


class UserRole(str, enum.Enum):
    """User role enumeration"""
    ADMIN = "Admin"
    DOCTOR = "Doctor"
    NURSE = "Nurse"
    PATIENT = "Patient"


class User(BaseModel):
    """
    User model for all system users.
    
    Attributes:
        id: Primary key (inherited from BaseModel)
        name: User's full name
        email: Unique email address for authentication
        password_hash: Bcrypt hashed password
        role: User role (Admin, Doctor, Nurse, Patient)
        created_at: Timestamp when user was created (inherited from BaseModel)
        updated_at: Timestamp when user was last updated (inherited from BaseModel)
    
    Relationships:
        patient: Patient profile (if role is Patient)
        doctor: Doctor profile (if role is Doctor)
        medical_records_created: Medical records created by this user
        audit_entries: Audit chain entries created by this user
    """
    __tablename__ = "users"
    
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(
        SQLEnum(UserRole, name="user_role", create_type=False),
        nullable=False,
        index=True
    )
    
    # Relationships
    patient = relationship("Patient", back_populates="user", uselist=False, cascade="all, delete-orphan")
    doctor = relationship("Doctor", back_populates="user", uselist=False, cascade="all, delete-orphan")
    medical_records_created = relationship("MedicalRecord", foreign_keys="MedicalRecord.created_by", back_populates="creator")
    audit_entries = relationship("AuditChain", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
