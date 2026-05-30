"""
Provider model for healthcare providers (may or may not have system accounts)
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Provider(Base):
    """
    A healthcare provider (physician, therapist, etc.).

    user_id is nullable because providers imported from external datasets may
    not have system accounts.  encounter_count and procedure_count are
    pre-aggregated analytics fields from the import pipeline.
    """
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    organization_id = Column(
        Integer, ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    name = Column(String(255), nullable=False)
    gender = Column(String(10), nullable=True)
    speciality = Column(String(100), nullable=True, index=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True, index=True)
    state = Column(String(50), nullable=True)
    zip = Column(String(20), nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    encounter_count = Column(Integer, nullable=False, default=0, server_default="0")
    procedure_count = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    organization = relationship("Organization", back_populates="providers")

    def __repr__(self) -> str:
        return f"<Provider(id={self.id}, name='{self.name}', speciality='{self.speciality}')>"
