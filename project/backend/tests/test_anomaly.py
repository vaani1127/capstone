"""
Tests for ML-based behavioural anomaly detection service and API endpoints.

Covers: feature extraction, anomaly scoring, severity classification,
NL explanation generation, and the anomaly HTTP API.
"""
import pytest
from datetime import datetime
from unittest.mock import patch

from app.models.anomaly_alert import AnomalyAlert
from app.services.anomaly_service import (
    classify_severity,
    extract_features,
    generate_explanation,
    score_event,
    _models,
)
from app.services.blockchain_service import create_audit_entry

ANOMALY = "/api/v1/anomaly"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _clear_model_cache():
    """Remove cached IsolationForest models so each test trains from scratch."""
    _models.clear()


# ---------------------------------------------------------------------------
# GROUP 1: Feature Extraction
# ---------------------------------------------------------------------------

def test_extract_features_returns_all_keys(db):
    # user_id=9999 doesn't exist → early return with all-zero dict
    result = extract_features(db, user_id=9999)
    expected_keys = [
        "actions_per_hour",
        "unique_patients_accessed",
        "off_hours_flag",
        "untreated_patient_ratio",
        "record_type_entropy",
        "rapid_edit_flag",
        "cross_role_action_flag",
        "session_duration_minutes",
    ]
    assert set(result.keys()) == set(expected_keys)
    for v in result.values():
        assert v == 0 or v == 0.0


def test_extract_features_actions_per_hour(db, doctor_user):
    doc_user, _ = doctor_user

    # Insert 3 audit entries for this user within the last 60-minute window
    for i in range(3):
        create_audit_entry(
            db,
            record_id=100 + i,
            record_type="appointment_created",
            record_data={"patient_id": i + 1},
            user_id=doc_user.id,
        )
    db.commit()

    result = extract_features(db, doc_user.id)
    assert result["actions_per_hour"] > 0


def test_extract_features_off_hours_flag(db, doctor_user):
    from datetime import datetime as real_datetime

    doc_user, _ = doctor_user

    # Patch datetime.utcnow to return 02:00 UTC (off-hours)
    fake_night = real_datetime(2024, 1, 1, 2, 0, 0)
    with patch("app.services.anomaly_service.datetime") as mock_dt:
        mock_dt.utcnow.return_value = fake_night
        mock_dt.side_effect = real_datetime
        result = extract_features(db, doc_user.id)
    assert result["off_hours_flag"] == 1

    # Patch datetime.utcnow to return 14:00 UTC (normal hours)
    fake_day = real_datetime(2024, 1, 1, 14, 0, 0)
    with patch("app.services.anomaly_service.datetime") as mock_dt:
        mock_dt.utcnow.return_value = fake_day
        mock_dt.side_effect = real_datetime
        result = extract_features(db, doc_user.id)
    assert result["off_hours_flag"] == 0


# ---------------------------------------------------------------------------
# GROUP 2: Scoring
# ---------------------------------------------------------------------------

def test_score_returns_float_between_0_and_1(db):
    _clear_model_cache()
    features = {
        "actions_per_hour": 0.0,
        "unique_patients_accessed": 0,
        "off_hours_flag": 0,
        "untreated_patient_ratio": 0.0,
        "record_type_entropy": 0.0,
        "rapid_edit_flag": 0,
        "cross_role_action_flag": 0,
        "session_duration_minutes": 0.0,
    }
    result = score_event(features, "Doctor", db)
    assert isinstance(result, float)
    assert 0.0 <= result <= 1.0


def test_normal_behavior_score_is_low(db):
    _clear_model_cache()
    normal_features = {
        "actions_per_hour": 2.0,
        "unique_patients_accessed": 1,
        "off_hours_flag": 0,
        "untreated_patient_ratio": 0.0,
        "record_type_entropy": 0.0,
        "rapid_edit_flag": 0,
        "cross_role_action_flag": 0,
        "session_duration_minutes": 15.0,
    }
    score = score_event(normal_features, "Doctor", db)
    assert score < 0.75


def test_anomalous_behavior_scores_higher_than_normal(db):
    _clear_model_cache()
    normal = {
        "actions_per_hour": 0.0,
        "unique_patients_accessed": 0,
        "off_hours_flag": 0,
        "untreated_patient_ratio": 0.0,
        "record_type_entropy": 0.0,
        "rapid_edit_flag": 0,
        "cross_role_action_flag": 0,
        "session_duration_minutes": 0.0,
    }
    anomalous = {
        "actions_per_hour": 60.0,
        "unique_patients_accessed": 25,
        "off_hours_flag": 1,
        "untreated_patient_ratio": 0.9,
        "record_type_entropy": 2.5,
        "rapid_edit_flag": 1,
        "cross_role_action_flag": 1,
        "session_duration_minutes": 180.0,
    }
    score_n = score_event(normal, "Doctor", db)
    score_a = score_event(anomalous, "Doctor", db)
    assert score_a >= score_n


# ---------------------------------------------------------------------------
# GROUP 3: Severity Classification
# ---------------------------------------------------------------------------

def test_severity_low():
    assert classify_severity(0.45) == "LOW"


def test_severity_medium():
    assert classify_severity(0.68) == "MEDIUM"


def test_severity_high():
    assert classify_severity(0.82) == "HIGH"


def test_severity_boundary_medium():
    assert classify_severity(0.60) == "MEDIUM"


def test_severity_boundary_high():
    assert classify_severity(0.75) == "HIGH"


# ---------------------------------------------------------------------------
# GROUP 4: NL Explanation
# ---------------------------------------------------------------------------

def test_explanation_is_string_and_nonempty():
    result = generate_explanation("Dr. Test", "Doctor", 0.8, [])
    assert isinstance(result, str)
    assert len(result) > 10


def test_explanation_contains_username():
    result = generate_explanation("Alice Sharma", "Nurse", 0.7, [])
    assert "Alice Sharma" in result


def test_explanation_off_hours_message():
    top_feats = [{"feature": "off_hours_flag", "value": 1, "shap": 0.4}]
    result = generate_explanation("Bob", "Doctor", 0.72, top_feats)
    assert "hour" in result.lower() or "normal" in result.lower()


# ---------------------------------------------------------------------------
# GROUP 5: REST API Endpoints
# ---------------------------------------------------------------------------

def test_anomaly_alerts_requires_admin(client, doctor_headers):
    resp = client.get(f"{ANOMALY}/alerts", headers=doctor_headers)
    assert resp.status_code == 403


def test_anomaly_alerts_admin_returns_200(client, admin_headers):
    resp = client.get(f"{ANOMALY}/alerts", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "alerts" in body
    assert "total" in body


def test_anomaly_stats_admin_returns_200(client, admin_headers):
    resp = client.get(f"{ANOMALY}/stats", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    for key in [
        "total_alerts",
        "high_severity",
        "medium_severity",
        "low_severity",
        "unacknowledged",
        "last_24h",
    ]:
        assert key in body


def test_acknowledge_alert(client, admin_headers, admin_user, db):
    alert = AnomalyAlert(
        user_id=admin_user.id,
        anomaly_score=0.8,
        severity="HIGH",
        top_features=[],
        explanation="Test alert",
        is_acknowledged=False,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    resp = client.post(
        f"{ANOMALY}/alerts/{alert.id}/acknowledge", headers=admin_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_acknowledged"] is True
