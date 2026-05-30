"""
Organization model for healthcare provider organisations
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Organization(Base):
    """
    Represents a healthcare organisation (hospital, clinic, practice).

    Revenue and utilisation are analytics fields pre-populated from external
    datasets; lat/lon enable map-based lookups.  This is a read-mostly table
    managed outside the patient-care workflow.
    """
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True, index=True)
    state = Column(String(50), nullable=True)
    zip = Column(String(20), nullable=True)
    phone = Column(String(30), nullable=True)
    revenue = Column(Numeric(15, 2), nullable=True)
    utilization = Column(Float, nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Providers affiliated with this organisation
    providers = relationship("Provider", back_populates="organization")

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name='{self.name}')>"
