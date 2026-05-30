"""
Procedure model for clinical procedures performed on patients
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Procedure(Base):
    """
    Records a single clinical procedure performed on a patient.

    encounter_id links to the appointment/encounter in which the procedure
    occurred; it is nullable because procedures may be entered retrospectively.
    performed_by links to the system user who entered the record; base_cost
    stores the list price before insurance adjustments.
    """
    __tablename__ = "procedures"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(
        Integer, ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    encounter_id = Column(
        Integer, ForeignKey("appointments.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    performed_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    procedure_code = Column(String(20), nullable=True)
    description = Column(Text, nullable=False)
    performed_at = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, nullable=True)
    outcome = Column(Text, nullable=True)
    base_cost = Column(Numeric(10, 2), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # One-directional relationships
    patient = relationship("Patient", foreign_keys=[patient_id])
    performer = relationship("User", foreign_keys=[performed_by])
    encounter = relationship("Appointment", foreign_keys=[encounter_id])

    def __repr__(self) -> str:
        return (
            f"<Procedure(id={self.id}, patient_id={self.patient_id}, "
            f"description='{self.description[:40]}')>"
        )
