"""
Anomaly alert model for ML-based behavioural anomaly detection
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, JSON, Text
# trigger_type values — kept as module-level constants so callers never
# hardcode the string literals.
TRIGGER_SINGLE_EVENT   = "single_event"
TRIGGER_SUSTAINED_TREND = "sustained_trend"
TRIGGER_IDENTITY_DRIFT = "identity_drift"
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class AnomalyAlert(BaseModel):
    """
    Anomaly alert model for storing ML-generated behavioral anomaly detection results.

    Attributes:
        id: Primary key (inherited from BaseModel)
        user_id: FK to users — the user whose behaviour was flagged
        anomaly_score: IsolationForest anomaly score normalised to 0–1
        severity: Alert severity — LOW, MEDIUM, or HIGH
        top_features: JSON list of top SHAP-attributed features [{feature, value, contribution}]
        explanation: Natural-language explanation string generated from SHAP values
        audit_entry_id: FK to audit_chain — the triggering audit block (nullable, SET NULL on delete)
        trigger_type:   How the alert was created — "single_event" (score >= 0.50) or
                        "sustained_trend" (7 consecutive scores > 0.35). Never NULL.
        is_acknowledged: Whether the alert has been reviewed by an admin
        acknowledged_by: FK to users — admin who acknowledged the alert
        acknowledged_at: Timestamp of acknowledgement

    Relationships:
        user: User whose behaviour was flagged
    """
    __tablename__ = "anomaly_alerts"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    anomaly_score = Column(Float, nullable=False)
    severity = Column(String(10), nullable=False, index=True)
    top_features = Column(JSON, nullable=False, default=list)
    explanation = Column(Text, nullable=False)
    narrative = Column(Text, nullable=True)
    audit_entry_id = Column(Integer, ForeignKey("audit_chain.id", ondelete="SET NULL"), nullable=True)
    trigger_type   = Column(String(32), nullable=False, default=TRIGGER_SINGLE_EVENT, index=True)
    is_acknowledged = Column(Boolean, nullable=False, default=False, index=True)
    acknowledged_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)

    # Relationship to the flagged user; explicit foreign_keys required because
    # two columns on this table reference users.id
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return (
            f"<AnomalyAlert(id={self.id}, user_id={self.user_id}, "
            f"severity='{self.severity}', anomaly_score={self.anomaly_score})>"
        )
