"""
Anomaly Detection Service

ML-based behavioural anomaly detection using IsolationForest (scikit-learn) and
SHAP TreeExplainer.  One model is trained per user role on the last 30 days of
audit_chain activity.

Model loading priority (get_or_train_model):
  1. In-memory _models cache        — fastest, survives within a process
  2. Disk .pkl file in MODELS_DIR   — survives restarts; written after training
  3. Lazy train from audit_chain    — fallback when no .pkl exists

Pipeline per event:
  extract_features → score_event → (threshold gate) → explain_event
      → generate_explanation → classify_severity → persist AnomalyAlert
"""
import logging
import math
import json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List

import joblib
from sqlalchemy.orm import Session
from sqlalchemy import func  # available for future aggregate queries

import numpy as np
from sklearn.ensemble import IsolationForest
import shap

from app.models.anomaly_alert import AnomalyAlert, TRIGGER_SINGLE_EVENT, TRIGGER_SUSTAINED_TREND
from app.models.audit_chain import AuditChain
from app.models.behavioral_score import BehavioralScore
from app.models.user import User
from app.models.appointment import Appointment


logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Persistence path: project/backend/models/{role}_isolation_forest.pkl
# Resolved relative to this file so it works regardless of CWD.
# ---------------------------------------------------------------------------
MODELS_DIR: Path = Path(__file__).resolve().parent.parent.parent / "models"

# ---------------------------------------------------------------------------
# Module-level model cache: role string → trained IsolationForest
# ---------------------------------------------------------------------------
_models: Dict[str, IsolationForest] = {}

# Canonical feature order — must stay in sync with every caller
FEATURE_ORDER: List[str] = [
    "actions_per_hour",
    "unique_patients_accessed",
    "off_hours_flag",
    "untreated_patient_ratio",
    "record_type_entropy",
    "rapid_edit_flag",
    "cross_role_action_flag",
    "session_duration_minutes",
]

# Per-role normal-behaviour baselines: mean of each continuous feature across
# is_anomaly=0 rows, computed from the training dataset (09_audit_logs_synthetic.csv).
# Used as reference points in the rule-based fallback explanation when SHAP is
# unavailable.  Update these if the model is retrained on a new dataset.
_ROLE_BASELINES: Dict[str, Dict[str, float]] = {
    "Admin":   {"actions_per_hour": 8.0,  "unique_patients_accessed": 4.1,  "session_duration_minutes": 37.8},
    "Doctor":  {"actions_per_hour": 14.9, "unique_patients_accessed": 10.4, "session_duration_minutes": 39.9},
    "Nurse":   {"actions_per_hour": 19.7, "unique_patients_accessed": 16.2, "session_duration_minutes": 40.5},
    "Patient": {"actions_per_hour": 3.4,  "unique_patients_accessed": 2.0,  "session_duration_minutes": 40.2},
}


# Trend-detection parameters for sustained-elevation escalation.
# A MEDIUM alert is raised when all of the last TREND_WINDOW scores exceed
# TREND_THRESHOLD, provided no escalation alert already exists for this user
# within the last TREND_DEDUP_DAYS days.
TREND_WINDOW:     int   = 7      # number of consecutive recent scores required
TREND_THRESHOLD:  float = 0.35   # minimum score for each of those entries
TREND_DEDUP_DAYS: int   = 7      # rolling window in which only one escalation fires

# ---------------------------------------------------------------------------
# SECTION 2: Feature extraction
# ---------------------------------------------------------------------------

def extract_features(db: Session, user_id: int, window_minutes: int = 60) -> dict:
    """
    Extract 8 behavioural features from a user's recent audit activity.

    Queries audit_chain for the last `window_minutes` of entries for the
    given user and computes frequency, access-breadth, temporal, relational,
    entropy, and role-consistency signals.

    Args:
        db: Database session
        user_id: ID of the user to analyse
        window_minutes: Look-back window in minutes (default 60; use 60*24*30
                        for the 30-day training window)

    Returns:
        dict with exactly the 8 keys in FEATURE_ORDER; all values are float/int.
    """
    cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)

    entries = (
        db.query(AuditChain)
        .filter(AuditChain.user_id == user_id, AuditChain.timestamp >= cutoff)
        .order_by(AuditChain.timestamp.asc())
        .all()
    )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {k: 0.0 for k in FEATURE_ORDER}

    # Normalise role enum → plain string ("Doctor", "Admin", …)
    role: str = user.role.value if hasattr(user.role, "value") else str(user.role)

    # ------------------------------------------------------------------
    # 1. actions_per_hour
    # ------------------------------------------------------------------
    count = len(entries)
    actions_per_hour = float(count * (60.0 / window_minutes))

    # ------------------------------------------------------------------
    # 2. unique_patients_accessed
    # ------------------------------------------------------------------
    accessed_patient_ids: set = set()
    for entry in entries:
        data = entry.record_data
        # JSON columns return dicts in PostgreSQL but strings in SQLite tests
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except (json.JSONDecodeError, TypeError):
                data = {}
        if isinstance(data, dict):
            pid = data.get("patient_id")
            if pid is not None:
                try:
                    accessed_patient_ids.add(int(pid))
                except (ValueError, TypeError):
                    pass

    unique_patients_accessed = len(accessed_patient_ids)

    # ------------------------------------------------------------------
    # 3. off_hours_flag  (22:00 – 05:59 UTC)
    # ------------------------------------------------------------------
    current_hour = datetime.utcnow().hour
    off_hours_flag = 1 if (current_hour >= 22 or current_hour <= 5) else 0

    # ------------------------------------------------------------------
    # 4. untreated_patient_ratio  (Doctor role only)
    # ------------------------------------------------------------------
    untreated_patient_ratio = 0.0
    if role == "Doctor" and accessed_patient_ids:
        try:
            from app.models.doctor import Doctor  # local import avoids circular dep
            doctor = db.query(Doctor).filter(Doctor.user_id == user_id).first()
            if doctor:
                treated_ids = {
                    row[0]
                    for row in db.query(Appointment.patient_id)
                    .filter(
                        Appointment.doctor_id == doctor.id,
                        Appointment.patient_id.in_(list(accessed_patient_ids)),
                    )
                    .all()
                }
                unmatched = len(accessed_patient_ids - treated_ids)
                untreated_patient_ratio = unmatched / len(accessed_patient_ids)
        except Exception as exc:
            logger.debug("untreated_patient_ratio query failed: %s", exc)

    # ------------------------------------------------------------------
    # 5. record_type_entropy  (Shannon entropy over record_type values)
    # ------------------------------------------------------------------
    record_types = [e.record_type for e in entries if e.record_type]
    if record_types:
        type_counts = Counter(record_types)
        total = len(record_types)
        record_type_entropy = -sum(
            (c / total) * math.log2(c / total) for c in type_counts.values()
        )
    else:
        record_type_entropy = 0.0

    # ------------------------------------------------------------------
    # 6. rapid_edit_flag  (same record_id modified > 3 times in 15 min)
    # ------------------------------------------------------------------
    rapid_cutoff = datetime.utcnow() - timedelta(minutes=15)
    recent_entries = [e for e in entries if e.timestamp >= rapid_cutoff]
    record_id_counts = Counter(e.record_id for e in recent_entries)
    rapid_edit_flag = 1 if any(v > 3 for v in record_id_counts.values()) else 0

    # ------------------------------------------------------------------
    # 7. cross_role_action_flag  (action type inconsistent with role)
    # ------------------------------------------------------------------
    forbidden: Dict[str, List[str]] = {
        "Patient": ["medical_record_created", "medical_record_updated", "walk_in_registered"],
        "Nurse":   ["medical_record_created", "medical_record_updated"],
        "Doctor":  [],
        "Admin":   [],
    }
    forbidden_types = set(forbidden.get(role, []))
    cross_role_action_flag = (
        1 if any(e.record_type in forbidden_types for e in entries) else 0
    )

    # ------------------------------------------------------------------
    # 8. session_duration_minutes
    # ------------------------------------------------------------------
    if len(entries) >= 2:
        session_duration_minutes = (
            entries[-1].timestamp - entries[0].timestamp
        ).total_seconds() / 60.0
    else:
        session_duration_minutes = 0.0

    return {
        "actions_per_hour":         actions_per_hour,
        "unique_patients_accessed": unique_patients_accessed,
        "off_hours_flag":           off_hours_flag,
        "untreated_patient_ratio":  untreated_patient_ratio,
        "record_type_entropy":      record_type_entropy,
        "rapid_edit_flag":          rapid_edit_flag,
        "cross_role_action_flag":   cross_role_action_flag,
        "session_duration_minutes": session_duration_minutes,
    }


# ---------------------------------------------------------------------------
# SECTION 3 & 4: Array helpers
# ---------------------------------------------------------------------------

def _get_default_features() -> np.ndarray:
    """Return a single all-zero feature row — used to initialise sparse models."""
    return np.zeros((1, 8))


def _features_to_array(features: dict) -> np.ndarray:
    """Convert a features dict to a (1, 8) float numpy array in FEATURE_ORDER."""
    return np.array([[features[k] for k in FEATURE_ORDER]], dtype=float)


# ---------------------------------------------------------------------------
# SECTION 5: Model training / caching
# ---------------------------------------------------------------------------

def get_or_train_model(role: str, db: Session) -> IsolationForest:
    """
    Return the IsolationForest for `role` using a 3-tier priority:

    1. In-memory ``_models`` cache — zero I/O, survives within a process.
    2. Disk .pkl in ``MODELS_DIR``  — survives restarts; pre-trained by train.py.
    3. Lazy train from audit_chain  — fallback when no .pkl exists; result is
       saved to disk so subsequent restarts skip retraining.

    Training uses a 30-day audit window per user.  When fewer than 5 role-users
    exist (e.g., test environments), a minimal model is fitted on zero-vectors to
    guarantee a valid scorer without crashing.

    Args:
        role: Plain-string role name ("Doctor", "Admin", …)
        db:   Database session used for training-data queries (tier-3 only)

    Returns:
        Trained IsolationForest (always cached in _models after first call)
    """
    # ------------------------------------------------------------------
    # Tier 1: in-memory cache
    # ------------------------------------------------------------------
    if role in _models:
        return _models[role]

    # ------------------------------------------------------------------
    # Tier 2: load pre-trained model from disk
    # ------------------------------------------------------------------
    pkl_path = MODELS_DIR / f"{role}_isolation_forest.pkl"
    if pkl_path.exists():
        try:
            model = joblib.load(pkl_path)
            _models[role] = model
            logger.info("Loaded IsolationForest for role=%s from %s", role, pkl_path)
            return model
        except Exception as exc:
            logger.warning(
                "Failed to load model from %s (%s) — falling back to training",
                pkl_path,
                exc,
            )

    # ------------------------------------------------------------------
    # Tier 3: train from scratch using 30-day audit window
    # ------------------------------------------------------------------
    logger.info("Training IsolationForest for role=%s", role)
    users = db.query(User).filter(User.role == role).all()

    feature_rows: List[List[float]] = []
    for u in users:
        feats = extract_features(db, u.id, window_minutes=60 * 24 * 30)
        feature_rows.append([feats[k] for k in FEATURE_ORDER])

    if len(feature_rows) < 5:
        # Not enough real data — initialise on repeated zero-vectors
        model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
        model.fit(_get_default_features().repeat(10, axis=0))
    else:
        feature_matrix = np.array(feature_rows, dtype=float)
        n_samples = min(256, len(feature_matrix))
        model = IsolationForest(
            n_estimators=200,
            contamination=0.05,
            random_state=42,
            max_samples=n_samples,
        )
        model.fit(feature_matrix)

    # ------------------------------------------------------------------
    # Persist to disk so future restarts skip retraining (non-fatal)
    # ------------------------------------------------------------------
    try:
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, pkl_path)
        logger.info("Saved IsolationForest for role=%s → %s", role, pkl_path)
    except Exception as exc:
        logger.warning("Failed to persist model for role=%s: %s", role, exc)

    _models[role] = model
    return model


# ---------------------------------------------------------------------------
# SECTION 6: Anomaly scoring
# ---------------------------------------------------------------------------

def score_event(features: dict, role: str, db: Session) -> float:
    """
    Score a feature vector with the role-specific IsolationForest.

    IsolationForest.decision_function returns positive values for normal
    observations and negative values for anomalies, centred roughly around 0.
    We shift and clip to [0, 1] so that 1.0 = maximally anomalous.

    Args:
        features: Feature dict from extract_features()
        role: Plain-string role name
        db: Database session (forwarded to get_or_train_model)

    Returns:
        Anomaly score in [0, 1]
    """
    feature_array = _features_to_array(features)
    model = get_or_train_model(role, db)
    raw_score = model.decision_function(feature_array)[0]
    anomaly_score = float(np.clip(0.5 - raw_score, 0.0, 1.0))
    return anomaly_score


# ---------------------------------------------------------------------------
# SECTION 7: SHAP explainability
# ---------------------------------------------------------------------------

def explain_event(features: dict, role: str, db: Session) -> List[dict]:
    """
    Return the top-3 SHAP feature attributions for the current event.

    Uses shap.TreeExplainer which is optimised for tree-based models.  Returns
    an empty list on any error so that an explanation failure never blocks alert
    persistence.

    Args:
        features: Feature dict from extract_features()
        role: Plain-string role name
        db: Database session

    Returns:
        List of up to 3 dicts: [{feature, value, shap}, …] sorted by |shap| desc
    """
    try:
        model = get_or_train_model(role, db)
        feature_array = _features_to_array(features)

        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(feature_array)

        # shap_values may be (1, 8) or a list of arrays (multi-output models)
        if isinstance(shap_values, list):
            shap_values = shap_values[0]

        # Flatten to 1-D: (1, 8) → (8,)
        values_1d: np.ndarray = (
            shap_values[0] if shap_values.ndim == 2 else shap_values.flatten()
        )

        attributions = [
            {
                "feature":     FEATURE_ORDER[i],
                "value":       float(features[FEATURE_ORDER[i]]),
                "shap":        float(values_1d[i]),
            }
            for i in range(len(FEATURE_ORDER))
        ]
        attributions.sort(key=lambda x: abs(x["shap"]), reverse=True)
        return attributions[:3]

    except Exception as exc:
        logger.warning("SHAP explanation failed (non-fatal): %s", exc)
        return []


# ---------------------------------------------------------------------------
# SECTION 7b: Rule-based fallback explanation (used when SHAP is unavailable)
# ---------------------------------------------------------------------------

def fallback_feature_explanation(
    features: dict,
    role: str,
    user_name: str,
    anomaly_score: float,
) -> str:
    """
    Produce a plain-English alert explanation directly from raw feature values
    when SHAP attribution is unavailable (e.g. explainer failure, empty result).

    Compares each feature against the per-role normal baseline in _ROLE_BASELINES
    and emits a human-readable phrase for every feature that is meaningfully
    elevated.  Falls back to a generic sentence only if no feature crosses its
    threshold — in practice this should be rare given the anomaly score already
    exceeded 0.50.

    Args:
        features:      Feature dict from extract_features().
        role:          Plain-string role name ("Doctor", "Admin", …).
        user_name:     Display name of the flagged user.
        anomaly_score: Normalised anomaly score (0–1).

    Returns:
        Single alert string, e.g.:
        "Alert — Alice [Nurse] scored 82% anomaly (rule-based). Detected:
         activity volume (61 actions/hr) was 3.1x above typical Nurse baseline
         (~20 actions/hr); performed actions inconsistent with Nurse role
         permissions."
    """
    baselines = _ROLE_BASELINES.get(role, {})
    parts: List[str] = []

    # --- Volume: actions_per_hour vs role baseline
    aph = features.get("actions_per_hour", 0.0)
    aph_base = baselines.get("actions_per_hour", 10.0)
    if aph > aph_base * 2:
        ratio = aph / aph_base if aph_base else float("inf")
        parts.append(
            f"activity volume ({aph:.0f} actions/hr) was {ratio:.1f}x above"
            f" typical {role} baseline (~{aph_base:.0f} actions/hr)"
        )

    # --- Breadth: unique_patients_accessed vs role baseline
    upa = features.get("unique_patients_accessed", 0.0)
    upa_base = baselines.get("unique_patients_accessed", 5.0)
    if upa > upa_base * 2:
        ratio = upa / upa_base if upa_base else float("inf")
        parts.append(
            f"accessed {upa:.0f} distinct patient records"
            f" ({ratio:.1f}x the typical {role} baseline of ~{upa_base:.0f})"
        )

    # --- Temporal: off_hours_flag
    if features.get("off_hours_flag", 0) >= 1:
        parts.append("access occurred outside normal operating hours (10 PM–6 AM UTC)")

    # --- Role integrity: cross_role_action_flag
    if features.get("cross_role_action_flag", 0) >= 1:
        parts.append(f"performed actions inconsistent with {role} role permissions")

    # --- Rapid edits: rapid_edit_flag
    if features.get("rapid_edit_flag", 0) >= 1:
        parts.append("modified the same record more than 3 times within 15 minutes")

    # --- Session length vs baseline
    sdm = features.get("session_duration_minutes", 0.0)
    sdm_base = baselines.get("session_duration_minutes", 40.0)
    if sdm > sdm_base * 3:
        parts.append(
            f"session lasted {sdm:.0f} minutes"
            f" ({sdm / sdm_base:.1f}x the typical {role} baseline of ~{sdm_base:.0f} min)"
        )

    # --- Untreated patient ratio (primarily Doctor-relevant)
    upr = features.get("untreated_patient_ratio", 0.0)
    if upr > 0.4:
        parts.append(
            f"{upr * 100:.0f}% of accessed patients had no prior appointment"
            f" with this user"
        )

    if not parts:
        parts = ["exhibited statistically anomalous behaviour across multiple signals"]

    joined = "; ".join(parts)
    return (
        f"Alert — {user_name} [{role}] scored {anomaly_score:.0%} anomaly"
        f" (rule-based explanation). Detected: {joined}."
    )


# ---------------------------------------------------------------------------
# SECTION 8: Natural-language explanation generator
# ---------------------------------------------------------------------------

def generate_explanation(
    user_name: str,
    role: str,
    anomaly_score: float,
    top_features: List[dict],
) -> str:
    """
    Produce a human-readable alert sentence from SHAP top-feature attribution.

    Each feature has a template lambda that returns a descriptive phrase only when
    the feature value is high enough to be meaningful.  Falls back to a generic
    phrase if no template fires.

    Args:
        user_name: Display name of the flagged user
        role: Plain-string role name ("Doctor", "Admin", …)
        anomaly_score: Normalised anomaly score (0–1)
        top_features: Output of explain_event()

    Returns:
        Single-sentence alert string
    """
    feature_messages: Dict[str, any] = {
        "actions_per_hour": lambda v: (
            f"performed {v:.0f} actions/hour ({v:.0f}x typical {role} activity)"
            if v > 5 else None
        ),
        "off_hours_flag": lambda v: (
            "accessed the system outside normal operating hours (10PM–6AM)"
            if v >= 1 else None
        ),
        "unique_patients_accessed": lambda v: (
            f"accessed {v:.0f} distinct patient records in 60 minutes"
            if v > 3 else None
        ),
        "untreated_patient_ratio": lambda v: (
            f"{v * 100:.0f}% of accessed patients have no prior appointment with this user"
            if v > 0.4 else None
        ),
        "record_type_entropy": lambda v: (
            f"performed an unusual mix of {v:.1f}-entropy action types"
            if v > 1.0 else None
        ),
        "rapid_edit_flag": lambda v: (
            "modified the same record more than 3 times within 15 minutes"
            if v >= 1 else None
        ),
        "cross_role_action_flag": lambda v: (
            f"performed actions inconsistent with {role} role permissions"
            if v >= 1 else None
        ),
        "session_duration_minutes": lambda v: (
            f"active for an unusually long session ({v:.0f} minutes)"
            if v > 120 else None
        ),
    }

    parts: List[str] = []
    for feat in top_features:
        fn = feature_messages.get(feat["feature"])
        if fn:
            msg = fn(feat["value"])
            if msg:
                parts.append(msg)

    if not parts:
        parts = ["exhibited statistically anomalous behavior patterns"]

    joined = "; ".join(parts)
    return f"Alert — {user_name} [{role}] scored {anomaly_score:.0%} anomaly. Detected: {joined}."


# ---------------------------------------------------------------------------
# SECTION 9: Severity classification
# ---------------------------------------------------------------------------

def classify_severity(anomaly_score: float) -> str:
    """
    Map a normalised anomaly score to a severity tier.

    Thresholds (inclusive lower bound):
        HIGH   ≥ 0.75
        MEDIUM ≥ 0.60
        LOW    < 0.60
    """
    if anomaly_score >= 0.75:
        return "HIGH"
    if anomaly_score >= 0.60:
        return "MEDIUM"
    return "LOW"


# ---------------------------------------------------------------------------
# SECTION 10a: Behavioral score persistence and trend detection
# ---------------------------------------------------------------------------

def persist_behavioral_score(
    db: Session,
    user_id: int,
    score: float,
    role: str,
) -> BehavioralScore:
    """
    Write a BehavioralScore row for every computed anomaly score.

    Called unconditionally from analyze_and_alert() before the alert
    threshold gate, so sub-threshold scores are also stored.

    Args:
        db:      Database session.
        user_id: ID of the scored user.
        score:   Normalised anomaly score in [0, 1].
        role:    Plain-string role name at time of scoring.

    Returns:
        The persisted BehavioralScore instance.
    """
    entry = BehavioralScore(
        user_id=user_id,
        score=score,
        computed_at=datetime.utcnow(),
        role=role,
    )
    db.add(entry)
    db.flush()   # get entry.id without closing the transaction
    logger.debug(
        "BehavioralScore persisted: id=%d user_id=%d score=%.3f",
        entry.id, user_id, score,
    )
    return entry


def check_sustained_elevation(
    db: Session,
    user_id: int,
    user_name: str,
    role: str,
) -> Optional[AnomalyAlert]:
    """
    Create a MEDIUM escalation alert when a user's last TREND_WINDOW scores
    are ALL above TREND_THRESHOLD, and no such alert has already been raised
    within the last TREND_DEDUP_DAYS days.

    The 7 scores must be the 7 most-recent consecutive entries — a single
    sub-threshold score in that window breaks the streak and suppresses the
    alert.

    Args:
        db:        Database session.
        user_id:   ID of the user to inspect.
        user_name: Display name used in the alert explanation.
        role:      Plain-string role name.

    Returns:
        A new AnomalyAlert (MEDIUM, already committed) if the trend fires,
        None otherwise.
    """
    # Fetch the last TREND_WINDOW scores ordered newest-first.
    recent_scores: List[BehavioralScore] = (
        db.query(BehavioralScore)
        .filter(BehavioralScore.user_id == user_id)
        .order_by(BehavioralScore.computed_at.desc())
        .limit(TREND_WINDOW)
        .all()
    )

    # Need exactly TREND_WINDOW entries and every one above threshold.
    if len(recent_scores) < TREND_WINDOW:
        return None
    if not all(s.score > TREND_THRESHOLD for s in recent_scores):
        return None

    # De-duplicate: skip if an escalation alert already exists in the last
    # TREND_DEDUP_DAYS days so a perpetually-elevated user only gets one alert
    # per rolling window.
    dedup_cutoff = datetime.utcnow() - timedelta(days=TREND_DEDUP_DAYS)
    existing: Optional[AnomalyAlert] = (
        db.query(AnomalyAlert)
        .filter(
            AnomalyAlert.user_id == user_id,
            AnomalyAlert.trigger_type == TRIGGER_SUSTAINED_TREND,
            AnomalyAlert.created_at >= dedup_cutoff,
        )
        .first()
    )
    if existing:
        logger.debug(
            "Sustained-elevation alert suppressed for user_id=%d (dedup, existing id=%d)",
            user_id, existing.id,
        )
        return None

    score_values = [round(s.score, 3) for s in recent_scores]
    explanation = (
        f"Alert — {user_name} [{role}] triggered a sustained elevated behaviour "
        f"escalation. The last {TREND_WINDOW} anomaly scores were all above "
        f"{TREND_THRESHOLD:.0%}: {score_values}. "
        f"No single score crossed the immediate-alert threshold, but the "
        f"persistent trend indicates gradual escalation."
    )

    alert = AnomalyAlert(
        user_id=user_id,
        anomaly_score=max(s.score for s in recent_scores),
        severity="MEDIUM",
        top_features=[],
        explanation=explanation,
        audit_entry_id=None,
        trigger_type=TRIGGER_SUSTAINED_TREND,
        is_acknowledged=False,
    )
    db.add(alert)
    db.flush()
    logger.info(
        "Sustained-elevation alert created: id=%d user_id=%d scores=%s",
        alert.id, user_id, score_values,
    )
    return alert


# ---------------------------------------------------------------------------
# SECTION 10: Main orchestrator (background-task entry point)
# ---------------------------------------------------------------------------

def analyze_and_alert(
    db: Session,
    user_id: int,
    audit_entry_id: int,
) -> Optional[AnomalyAlert]:
    """
    Full anomaly detection pipeline, safe to run as a FastAPI background task.

    The entire function is wrapped in try/except so that any ML or DB failure
    is silently logged and never affects the primary request or its transaction.

    Args:
        db: Database session
        user_id: ID of the user whose action triggered this analysis
        audit_entry_id: ID of the audit_chain row that triggered this call

    Returns:
        AnomalyAlert if the score exceeded the 0.50 threshold, None otherwise.
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning("analyze_and_alert: user_id=%d not found, skipping", user_id)
            return None

        role: str = user.role.value if hasattr(user.role, "value") else str(user.role)

        features = extract_features(db, user_id)
        anomaly_score = score_event(features, role, db)

        # Persist every score unconditionally (sub-threshold included).
        persist_behavioral_score(db, user_id, anomaly_score, role)

        # Check for sustained elevation across the last TREND_WINDOW scores.
        # This runs before the single-score threshold gate so it can fire even
        # when no individual score crosses 0.50.
        trend_alert = check_sustained_elevation(db, user_id, user.name, role)

        if anomaly_score < 0.50:
            # Commit the behavioral score (and any trend alert) then exit early.
            db.commit()
            return trend_alert

        top_features = explain_event(features, role, db)
        if top_features:
            explanation = generate_explanation(user.name, role, anomaly_score, top_features)
        else:
            # SHAP unavailable (explainer failed or returned empty) — fall back to
            # a rule-based plain-English description from raw feature values so the
            # admin alert never displays a blank or generic explanation.
            explanation = fallback_feature_explanation(features, role, user.name, anomaly_score)
        severity = classify_severity(anomaly_score)

        alert = AnomalyAlert(
            user_id=user_id,
            anomaly_score=anomaly_score,
            severity=severity,
            top_features=top_features,
            explanation=explanation,
            audit_entry_id=audit_entry_id,
            trigger_type=TRIGGER_SINGLE_EVENT,
            is_acknowledged=False,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        logger.info(
            "Anomaly alert created: id=%d user_id=%d severity=%s score=%.3f",
            alert.id,
            user_id,
            severity,
            anomaly_score,
        )
        return alert

    except Exception as exc:
        logger.error(
            "analyze_and_alert failed for user_id=%d audit_entry_id=%d: %s",
            user_id,
            audit_entry_id,
            exc,
            exc_info=True,
        )
        return None
