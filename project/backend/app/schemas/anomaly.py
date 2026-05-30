"""
Anomaly detection schemas for request/response validation
"""
from enum import Enum
from pydantic import BaseModel
from typing import Any, List, Optional
from datetime import datetime


class AnomalySeverity(str, Enum):
    """Anomaly alert severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AnomalyFeatureVector(BaseModel):
    """Feature vector used as input to the IsolationForest anomaly scorer"""
    actions_per_hour: float = 0.0
    unique_patients_accessed: int = 0
    off_hours_flag: int = 0
    untreated_patient_ratio: float = 0.0
    record_type_entropy: float = 0.0
    rapid_edit_flag: int = 0
    cross_role_action_flag: int = 0
    session_duration_minutes: float = 0.0


class AnomalyAlertBase(BaseModel):
    """Base anomaly alert schema with fields shared across create and response"""
    user_id: int
    anomaly_score: float
    severity: str
    top_features: List[Any]
    explanation: str
    audit_entry_id: Optional[int] = None


class AnomalyAlertCreate(AnomalyAlertBase):
    """Schema for persisting a new anomaly alert (internal use by anomaly service)"""
    pass


class AnomalyAlertResponse(AnomalyAlertBase):
    """Schema for anomaly alert response returned to API consumers"""
    id: int
    is_acknowledged: bool
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AnomalyAlertListResponse(BaseModel):
    """Schema for paginated anomaly alert list response"""
    alerts: List[AnomalyAlertResponse]
    total: int
    page: int
    page_size: int
