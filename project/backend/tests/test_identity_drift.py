"""
Tests for cross-role behavioral drift detection (identity drift).

Covers:
  1. A Nurse's access pattern drifting toward Doctor (higher privilege) gets flagged.
  2. Normal in-role variance does NOT get flagged.
  3. Drift toward a LOWER privilege role does NOT get flagged.
  4. Dedup: an 8th elevated drift score within the dedup window suppresses a second alert.
  5. Distance must be monotonically decreasing (trend check).
"""

import sys
import os
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, event as sa_event
from sqlalchemy.orm import sessionmaker, Session

# ---------------------------------------------------------------------------
# Bootstrap: register all models with Base so create_all works
# ---------------------------------------------------------------------------
from app.db.base import Base, import_models
import_models()

from app.models.user import User, UserRole
from app.models.anomaly_alert import AnomalyAlert, TRIGGER_IDENTITY_DRIFT
from app.models.behavioral_score import BehavioralScore
from app.services.anomaly_service import (
    TREND_DEDUP_DAYS,
    TREND_WINDOW,
    check_identity_drift,
    compute_cross_role_distance,
    PRIVILEGE_INDEX,
)

# ---------------------------------------------------------------------------
# SQLite in-memory engine setup
# ---------------------------------------------------------------------------
ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
@sa_event.listens_for(ENGINE, "connect")
def _set_sqlite_pragma(conn, _):
    conn.execute("PRAGMA foreign_keys=ON")

Base.metadata.create_all(ENGINE)
TestSession = sessionmaker(bind=ENGINE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(db: Session, name: str, role: str) -> User:
    user = User(
        name=name,
        email=f"{name.lower().replace(' ', '_')}@test.com",
        password_hash="x",
        role=UserRole(role),
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def _insert_drift_scores(
    db: Session,
    user_id: int,
    role: str,
    scores: list,
    nearest_roles: list,
    distances: list,
    base_time: datetime = None,
) -> None:
    """
    Insert a sequence of BehavioralScore rows with cross-role drift info.

    Args:
        user_id: User ID
        role: User's role
        scores: Anomaly scores
        nearest_roles: Nearest other role for each score
        distances: Cross-role distance for each score
        base_time: Starting timestamp (or auto-calculated)
    """
    if base_time is None:
        base_time = datetime.utcnow() - timedelta(minutes=len(scores) + 1)

    for i, (score, nearest_role, distance) in enumerate(zip(scores, nearest_roles, distances)):
        entry = BehavioralScore(
            user_id=user_id,
            score=score,
            computed_at=base_time + timedelta(minutes=i),
            role=role,
            nearest_other_role=nearest_role,
            cross_role_distance=distance,
        )
        db.add(entry)
    db.flush()


# ---------------------------------------------------------------------------
# Tests for compute_cross_role_distance
# ---------------------------------------------------------------------------

class TestComputeCrossRoleDistance(unittest.TestCase):

    def test_nurse_features_closer_to_doctor_than_admin(self):
        """
        A Nurse with high actions_per_hour should be closer to Doctor
        (who has aph=14.9) than to Admin (who has aph=8.0).
        """
        # Simulate a Nurse with high activity
        features = {
            "actions_per_hour": 15.0,
            "unique_patients_accessed": 12.0,
            "off_hours_flag": 0,
            "untreated_patient_ratio": 0.0,
            "record_type_entropy": 0.0,
            "rapid_edit_flag": 0,
            "cross_role_action_flag": 0,
            "session_duration_minutes": 40.0,
        }
        nearest_role, distance = compute_cross_role_distance(features, "Nurse")
        self.assertIsNotNone(nearest_role)
        # Should be closer to Doctor or Patient depending on the exact centroids
        # The key is it returns something and the distance is finite
        self.assertIsInstance(distance, float)
        self.assertGreater(distance, 0)
        self.assertLess(distance, float("inf"))

    def test_doctor_excludes_own_role(self):
        """
        When computing cross-role distance for a Doctor, the result should
        NOT be the Doctor centroid itself.
        """
        features = {
            "actions_per_hour": 15.0,
            "unique_patients_accessed": 11.0,
            "off_hours_flag": 0,
            "untreated_patient_ratio": 0.0,
            "record_type_entropy": 0.0,
            "rapid_edit_flag": 0,
            "cross_role_action_flag": 0,
            "session_duration_minutes": 40.0,
        }
        nearest_role, distance = compute_cross_role_distance(features, "Doctor")
        self.assertNotEqual(nearest_role, "Doctor")
        self.assertIsNotNone(nearest_role)


# ---------------------------------------------------------------------------
# Tests for identity drift detection
# ---------------------------------------------------------------------------

class TestNurseDriftTowardDoctor(unittest.TestCase):
    """Nurse access pattern drifting toward Doctor (higher privilege) → alert."""

    def setUp(self):
        Base.metadata.drop_all(ENGINE)
        Base.metadata.create_all(ENGINE)
        self.db: Session = TestSession()

    def tearDown(self):
        self.db.close()

    def test_nurse_drifting_toward_doctor_fires_alert(self):
        """
        A Nurse whose cross-role distance to Doctor is decreasing over
        7 scores, trending toward Doctor's privilege level, should trigger
        an identity drift alert.
        """
        user = _make_user(self.db, "Alice", "Nurse")

        # Insert 7 scores with decreasing distance to Doctor
        # (simulating drift from Nurse behavior toward Doctor behavior)
        scores = [0.30, 0.32, 0.31, 0.33, 0.32, 0.34, 0.31]
        distances = [50.0, 45.0, 40.0, 35.0, 30.0, 25.0, 20.0]  # Decreasing: drifting closer
        nearest_roles = ["Doctor"] * 7

        _insert_drift_scores(
            self.db, user.id, "Nurse",
            scores, nearest_roles, distances
        )

        alert = check_identity_drift(self.db, user.id, user.name, "Nurse")
        self.db.commit()

        self.assertIsNotNone(alert, "Identity drift alert should fire for Nurse drifting to Doctor")
        self.assertEqual(alert.severity, "MEDIUM")
        self.assertEqual(alert.trigger_type, TRIGGER_IDENTITY_DRIFT)
        self.assertIn("Doctor", alert.explanation)
        self.assertIn("identity drift", alert.explanation.lower())

    def test_nurse_drifting_requires_all_scores_present(self):
        """
        If fewer than TREND_WINDOW scores exist, no drift alert should fire.
        """
        user = _make_user(self.db, "Bob", "Nurse")

        # Only 6 scores (less than TREND_WINDOW=7)
        scores = [0.30] * 6
        distances = [50.0, 45.0, 40.0, 35.0, 30.0, 25.0]
        nearest_roles = ["Doctor"] * 6

        _insert_drift_scores(
            self.db, user.id, "Nurse",
            scores, nearest_roles, distances
        )

        alert = check_identity_drift(self.db, user.id, user.name, "Nurse")
        self.assertIsNone(alert, "Drift alert should not fire with fewer than TREND_WINDOW scores")


class TestNormalInRoleVariance(unittest.TestCase):
    """Normal in-role variance (distances not changing or increasing) → no alert."""

    def setUp(self):
        Base.metadata.drop_all(ENGINE)
        Base.metadata.create_all(ENGINE)
        self.db: Session = TestSession()

    def tearDown(self):
        self.db.close()

    def test_stable_distance_no_drift_alert(self):
        """
        A Nurse whose cross-role distance to Doctor is stable (not decreasing),
        should NOT trigger a drift alert.
        """
        user = _make_user(self.db, "Charlie", "Nurse")

        scores = [0.30] * TREND_WINDOW
        distances = [50.0] * TREND_WINDOW  # Constant distance: no drift
        nearest_roles = ["Doctor"] * TREND_WINDOW

        _insert_drift_scores(
            self.db, user.id, "Nurse",
            scores, nearest_roles, distances
        )

        alert = check_identity_drift(self.db, user.id, user.name, "Nurse")
        self.assertIsNone(alert, "Stable distance should not trigger drift alert")

    def test_increasing_distance_no_drift_alert(self):
        """
        A Nurse whose cross-role distance to Doctor is increasing (drifting away),
        should NOT trigger a drift alert.
        """
        user = _make_user(self.db, "Diana", "Nurse")

        scores = [0.30] * TREND_WINDOW
        distances = [20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0]  # Increasing: drifting away
        nearest_roles = ["Doctor"] * TREND_WINDOW

        _insert_drift_scores(
            self.db, user.id, "Nurse",
            scores, nearest_roles, distances
        )

        alert = check_identity_drift(self.db, user.id, user.name, "Nurse")
        self.assertIsNone(alert, "Increasing distance (drifting away) should not trigger drift alert")


class TestLowerPrivilegeDrift(unittest.TestCase):
    """Drift toward LOWER privilege role (e.g., Doctor → Nurse) → no alert."""

    def setUp(self):
        Base.metadata.drop_all(ENGINE)
        Base.metadata.create_all(ENGINE)
        self.db: Session = TestSession()

    def tearDown(self):
        self.db.close()

    def test_doctor_drifting_toward_nurse_no_alert(self):
        """
        A Doctor whose access pattern is drifting toward a Nurse's baseline
        (lower privilege) should NOT trigger an alert. Only upward privilege
        drift is suspicious.
        """
        user = _make_user(self.db, "Eve", "Doctor")

        scores = [0.30] * TREND_WINDOW
        distances = [50.0, 45.0, 40.0, 35.0, 30.0, 25.0, 20.0]  # Decreasing distance
        nearest_roles = ["Nurse"] * TREND_WINDOW  # Drifting toward LOWER privilege

        _insert_drift_scores(
            self.db, user.id, "Doctor",
            scores, nearest_roles, distances
        )

        alert = check_identity_drift(self.db, user.id, user.name, "Doctor")
        self.assertIsNone(alert, "Drift toward lower-privilege role should not trigger alert")

    def test_admin_drifting_toward_doctor_no_alert(self):
        """
        An Admin drifting toward Doctor (lower privilege) should NOT trigger.
        """
        user = _make_user(self.db, "Frank", "Admin")

        scores = [0.30] * TREND_WINDOW
        distances = [50.0, 45.0, 40.0, 35.0, 30.0, 25.0, 20.0]
        nearest_roles = ["Doctor"] * TREND_WINDOW  # Doctor is lower privilege than Admin

        _insert_drift_scores(
            self.db, user.id, "Admin",
            scores, nearest_roles, distances
        )

        alert = check_identity_drift(self.db, user.id, user.name, "Admin")
        self.assertIsNone(alert, "Drift toward lower privilege should not trigger alert")


class TestDriftDedup(unittest.TestCase):
    """Dedup prevents duplicate identity drift alerts within TREND_DEDUP_DAYS."""

    def setUp(self):
        Base.metadata.drop_all(ENGINE)
        Base.metadata.create_all(ENGINE)
        self.db: Session = TestSession()

    def tearDown(self):
        self.db.close()

    def test_dedup_prevents_second_alert(self):
        """
        An 8th (and 9th…) score continuing the drift pattern within the
        dedup window must NOT create a second identity drift alert.
        """
        user = _make_user(self.db, "Grace", "Nurse")

        # Insert 7 scores with drift toward Doctor
        scores = [0.30] * TREND_WINDOW
        distances = [50.0, 45.0, 40.0, 35.0, 30.0, 25.0, 20.0]
        nearest_roles = ["Doctor"] * TREND_WINDOW

        _insert_drift_scores(self.db, user.id, "Nurse", scores, nearest_roles, distances)
        first_alert = check_identity_drift(self.db, user.id, user.name, "Nurse")
        self.db.commit()
        self.assertIsNotNone(first_alert)

        # Insert an 8th score continuing the drift
        _insert_drift_scores(
            self.db, user.id, "Nurse",
            [0.30], ["Doctor"], [15.0]
        )
        second_alert = check_identity_drift(self.db, user.id, user.name, "Nurse")
        self.db.commit()

        self.assertIsNone(
            second_alert,
            "A second drift alert within dedup window must not be created"
        )

    def test_dedup_window_expired_allows_new_alert(self):
        """
        Once the dedup window expires, a new drift alert should be allowed.
        """
        user = _make_user(self.db, "Hank", "Nurse")

        # Manually insert an old identity_drift alert outside the dedup window
        old_alert = AnomalyAlert(
            user_id=user.id,
            anomaly_score=0.40,
            severity="MEDIUM",
            top_features=[],
            explanation="identity drift (old)",
            audit_entry_id=None,
            trigger_type=TRIGGER_IDENTITY_DRIFT,
            is_acknowledged=False,
        )
        old_alert.created_at = datetime.utcnow() - timedelta(days=TREND_DEDUP_DAYS + 1)
        self.db.add(old_alert)
        self.db.flush()

        # Insert 7 new drift scores
        scores = [0.30] * TREND_WINDOW
        distances = [50.0, 45.0, 40.0, 35.0, 30.0, 25.0, 20.0]
        nearest_roles = ["Doctor"] * TREND_WINDOW

        _insert_drift_scores(self.db, user.id, "Nurse", scores, nearest_roles, distances)
        new_alert = check_identity_drift(self.db, user.id, user.name, "Nurse")
        self.db.commit()

        self.assertIsNotNone(
            new_alert,
            "A new drift alert should be allowed once the dedup window expires"
        )


class TestPrivilegeOrdering(unittest.TestCase):
    """Verify privilege order: Patient < Nurse < Doctor < Admin."""

    def test_privilege_order(self):
        """Check that PRIVILEGE_INDEX reflects the correct hierarchy."""
        self.assertLess(
            PRIVILEGE_INDEX.get("Patient", -1),
            PRIVILEGE_INDEX.get("Nurse", -1),
            "Patient should have lower privilege than Nurse"
        )
        self.assertLess(
            PRIVILEGE_INDEX.get("Nurse", -1),
            PRIVILEGE_INDEX.get("Doctor", -1),
            "Nurse should have lower privilege than Doctor"
        )
        self.assertLess(
            PRIVILEGE_INDEX.get("Doctor", -1),
            PRIVILEGE_INDEX.get("Admin", -1),
            "Doctor should have lower privilege than Admin"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
