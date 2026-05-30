"""
Vitals model for patient vital sign recordings
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class Vitals(BaseModel):
    """
    Stores a single set of vital sign measurements for a patient.

    BMI is computed in the application layer (POST /vitals/) from weight_kg
    and height_cm and stored here for fast retrieval.  recorded_at tracks
    when the measurement was physically taken; created_at (inherited from
    BaseModel) tracks when the row was inserted.

    Attributes:
        patient_id:         FK -> patients.id
        appointment_id:     FK -> appointments.id (nullable)
        recorded_by:        FK -> users.id (nurse or doctor who entered the data)
        recorded_at:        When the measurement was physically taken
        systolic_bp:        Systolic blood pressure in mmHg
        diastolic_bp:       Diastolic blood pressure in mmHg
        heart_rate:         Heart rate in bpm
        temperature:        Body temperature in degrees Fahrenheit
        respiratory_rate:   Respiratory rate in breaths per minute
        oxygen_saturation:  SpO2 as a percentage (0-100)
        weight_kg:          Body weight in kilograms
        height_cm:          Height in centimetres
        bmi:                Body Mass Index (weight_kg / (height_cm/100)^2)
        notes:              Free-text clinical notes
    """
    __tablename__ = "vitals"

    patient_id = Column(
        Integer, ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    appointment_id = Column(
        Integer, ForeignKey("appointments.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    recorded_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False, index=True,
    )
    recorded_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, index=True,
    )

    systolic_bp = Column(Integer, nullable=True)
    diastolic_bp = Column(Integer, nullable=True)
    heart_rate = Column(Integer, nullable=True)
    temperature = Column(Float, nullable=True)
    respiratory_rate = Column(Integer, nullable=True)
    oxygen_saturation = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships (one-directional — no back_populates on the other side
    # so existing models are not modified)
    patient = relationship("Patient", foreign_keys=[patient_id])
    recorder = relationship("User", foreign_keys=[recorded_by])
    appointment = relationship("Appointment", foreign_keys=[appointment_id])

    def __repr__(self) -> str:
        return f"<Vitals(id={self.id}, patient_id={self.patient_id}, recorded_at={self.recorded_at})>"
