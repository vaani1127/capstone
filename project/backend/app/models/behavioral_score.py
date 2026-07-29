"""
BehavioralScore model — stores every computed anomaly score, including
sub-threshold ones that do not produce an AnomalyAlert.
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class BehavioralScore(BaseModel):
    """
    One row per anomaly-score computation for a user.

    Unlike AnomalyAlert (created only when score >= 0.50), a BehavioralScore
    row is written for every call to analyze_and_alert(), including low-scoring
    ones.  This enables trend detection over rolling windows.

    Attributes:
        user_id:     FK to users — the scored user.
        score:       Normalised anomaly score in [0, 1].
        computed_at: UTC timestamp of when the score was computed.
        role:        Plain-string role at time of scoring ("Doctor", etc.).
    """
    __tablename__ = "behavioral_scores"

    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    score       = Column(Float, nullable=False)
    computed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    role        = Column(String(32), nullable=False)

    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return (
            f"<BehavioralScore(id={self.id}, user_id={self.user_id}, "
            f"score={self.score:.3f}, computed_at={self.computed_at})>"
        )
