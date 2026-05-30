"""
Allergy model for patient allergy records
"""
from sqlalchemy import Boolean, CheckConstraint, Column, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class Allergy(BaseModel):
    """
    Stores a single allergy record for a patient.

    is_active tracks whether this allergy is still clinically relevant.
    Doctors can deactivate (not delete) a record when an allergy resolves or
    was entered in error, preserving full history.

    Attributes:
        patient_id:   FK -> patients.id
        recorded_by:  FK -> users.id (doctor or nurse who entered the data)
        allergen:     Name of the allergen (e.g., "Penicillin", "Peanuts")
        reaction:     Description of the allergic reaction
        severity:     'mild' | 'moderate' | 'severe'  (CHECK constraint enforced)
        onset_date:   Date allergy first appeared (nullable)
        is_active:    False once deactivated by a doctor
        notes:        Free-text clinical notes
    """
    __tablename__ = "allergies"

    __table_args__ = (
        CheckConstraint(
            "severity IN ('mild', 'moderate', 'severe')",
            name='ck_allergies_severity',
        ),
    )

    patient_id = Column(
        Integer, ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    recorded_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False, index=True,
    )
    allergen = Column(String(255), nullable=False)
    reaction = Column(Text, nullable=True)
    severity = Column(String(20), nullable=False)
    onset_date = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    notes = Column(Text, nullable=True)

    # One-directional relationships — no back_populates so existing models
    # do not need modification.
    patient = relationship("Patient", foreign_keys=[patient_id])
    recorder = relationship("User", foreign_keys=[recorded_by])

    def __repr__(self) -> str:
        return (
            f"<Allergy(id={self.id}, patient_id={self.patient_id}, "
            f"allergen='{self.allergen}', severity='{self.severity}')>"
        )
