"""
Base class for SQLAlchemy models
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime
from datetime import datetime

Base = declarative_base()


class BaseModel(Base):
    """
    Abstract base model with common fields for all models.
    
    Attributes:
        id: Primary key
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"


# Import all models here to ensure they are registered with Base
# This is needed for Alembic migrations to detect all models
def import_models():
    """Import all models to register them with SQLAlchemy Base"""
    from app.models.user import User
    from app.models.patient import Patient
    from app.models.doctor import Doctor
    from app.models.appointment import Appointment
    from app.models.medical_record import MedicalRecord
    from app.models.audit_chain import AuditChain
