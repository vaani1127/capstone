"""
Tests for BehavioralScore persistence and sustained-elevation trend detection.

Covers:
  1. Seven scores all <= 0.35 — no escalation alert.
  2. Exactly 7 consecutive scores > 0.35 — one MEDIUM escalation alert.
  3. An 8th consecutive elevated score within the 7-day dedup window — no
     second alert.
  4. A single sub-threshold score breaking a streak — resets it (the 7 must
     be the 7 most-recent consecutive entries, not any 7 out of N).

All tests use an in-memory SQLite database so they run without a live
PostgreSQL instance.  SQLite doesn't support RETURNING, so we flush and
refresh to get IDs.
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
from app.models.anomaly_alert import AnomalyAlert, TRIGGER_SINGLE_EVENT, TRIGGER_SUSTAINED_TREND
from app.models.behavioral_score import BehavioralScore
from app.services.anomaly_service import (
    TREND_DEDUP_DAYS,
    TREND_THRESHOLD,
    TREND_WINDOW,
    check_sustained_elevation,
    persist_behavioral_score,
)

# ---------------------------------------------------------------------------
# SQLite in-memory engine setup
# ---------------------------------------------------------------------------
# Use check_same_thread=False for test compatibility.
ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
# SQLite does not enforce FK constraints by default — enable them.
@sa_event.listens_for(ENGINE, "connect")
def _set_sqlite_pragma(conn, _):
    conn.execute("PRAGMA foreign_keys=ON")

Base.metadata.create_all(ENGINE)
TestSession = sessionmaker(bind=ENGINE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(db: Session, name: str = "TestUser", role: str = "Admin") -> User:
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


def _insert_scores(
    db: Session,
    user_id: int,
    role: str,
    scores: list,
    base_time: datetime = None,
) -> None:
    """Insert a sequence of BehavioralScore rows with 1-minute spacing."""
    if base_time is None:
        base_time = datetime.utcnow() - timedelta(minutes=len(scores) + 1)
    for i, score in enumerate(scores):
        entry = BehavioralScore(
            user_id=user_id,
            score=score,
            computed_at=base_time + timedelta(minutes=i),
            role=role,
        )
        db.add(entry)
    db.flush()


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestPersistBehavioralScore(unittest.TestCase):

    def setUp(self):
        Base.metadata.drop_all(ENGINE)
        Base.metadata.create_all(ENGINE)
        self.db: Session = TestSession()

    def tearDown(self):
        self.db.close()

    def test_score_is_stored(self):
        user = _make_user(self.db)
        entry = persist_behavioral_score(self.db, user.id, 0.42, "Admin")
        self.db.commit()
        stored = self.db.query(BehavioralScore).filter_by(user_id=user.id).all()
        self.assertEqual(len(stored), 1)
        self.assertAlmostEqual(stored[0].score, 0.42, places=4)

    def test_sub_threshold_score_is_stored(self):
        """Scores well below the alert threshold must still be persisted."""
        user = _make_user(self.db)
        persist_behavioral_score(self.db, user.id, 0.10, "Nurse")
        self.db.commit()
        stored = self.db.query(BehavioralScore).filter_by(user_id=user.id).all()
        self.assertEqual(len(stored), 1)


class TestNoEscalationBelowThreshold(unittest.TestCase):
    """Seven scores all at or below 0.35 must not fire an escalation alert."""

    def setUp(self):
        Base.metadata.drop_all(ENGINE)
        Base.metadata.create_all(ENGINE)
        self.db: Session = TestSession()

    def tearDown(self):
        self.db.close()

    def test_seven_scores_at_threshold_no_alert(self):
        user = _make_user(self.db)
        # Scores exactly equal to TREND_THRESHOLD are NOT above it (strict >).
        _insert_scores(self.db, user.id, "Admin",
                       [TREND_THRESHOLD] * TREND_WINDOW)
        result = check_sustained_elevation(self.db, user.id, user.name, "Admin")
        self.assertIsNone(result, "Scores == threshold should not trigger escalation")

    def test_seven_scores_below_threshold_no_alert(self):
        user = _make_user(self.db)
        _insert_scores(self.db, user.id, "Admin",
                       [0.20, 0.25, 0.30, 0.28, 0.22, 0.31, 0.29])
        result = check_sustained_elevation(self.db, user.id, user.name, "Admin")
        self.assertIsNone(result)

    def test_fewer_than_seven_scores_no_alert(self):
        user = _make_user(self.db)
        _insert_scores(self.db, user.id, "Admin", [0.80] * (TREND_WINDOW - 1))
        result = check_sustained_elevation(self.db, user.id, user.name, "Admin")
        self.assertIsNone(result, "Fewer than TREND_WINDOW scores should not trigger")


class TestEscalationFiresOnSevenConsecutive(unittest.TestCase):
    """Exactly 7 consecutive scores above 0.35 → one MEDIUM alert."""

    def setUp(self):
        Base.metadata.drop_all(ENGINE)
        Base.metadata.create_all(ENGINE)
        self.db: Session = TestSession()

    def tearDown(self):
        self.db.close()

    def test_exactly_seven_elevated_scores_creates_alert(self):
        user = _make_user(self.db)
        elevated = [0.36, 0.38, 0.40, 0.37, 0.39, 0.41, 0.36]
        _insert_scores(self.db, user.id, "Admin", elevated)

        alert = check_sustained_elevation(self.db, user.id, user.name, "Admin")
        self.db.commit()

        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, "MEDIUM")
        self.assertIn("sustained elevated", alert.explanation)
        self.assertIn(str(TREND_WINDOW), alert.explanation)
        self.assertEqual(alert.trigger_type, TRIGGER_SUSTAINED_TREND)

    def test_alert_explanation_contains_score_list(self):
        user = _make_user(self.db)
        _insert_scores(self.db, user.id, "Doctor",
                       [0.40, 0.42, 0.43, 0.41, 0.44, 0.42, 0.40])
        alert = check_sustained_elevation(self.db, user.id, user.name, "Doctor")
        self.assertIsNotNone(alert)
        # Explanation should list the actual scores so the admin can review them.
        self.assertIn("0.4", alert.explanation)

    def test_alert_user_id_matches(self):
        user = _make_user(self.db)
        _insert_scores(self.db, user.id, "Nurse", [0.38] * TREND_WINDOW)
        alert = check_sustained_elevation(self.db, user.id, user.name, "Nurse")
        self.assertIsNotNone(alert)
        self.assertEqual(alert.user_id, user.id)


class TestDedupPreventsSecondAlert(unittest.TestCase):
    """
    An 8th (or 9th…) elevated score within the 7-day dedup window must NOT
    create a second escalation alert.
    """

    def setUp(self):
        Base.metadata.drop_all(ENGINE)
        Base.metadata.create_all(ENGINE)
        self.db: Session = TestSession()

    def tearDown(self):
        self.db.close()

    def test_eighth_elevated_score_no_duplicate(self):
        user = _make_user(self.db)
        # Insert 7 elevated scores and fire the first alert.
        _insert_scores(self.db, user.id, "Admin", [0.40] * TREND_WINDOW)
        first_alert = check_sustained_elevation(self.db, user.id, user.name, "Admin")
        self.db.commit()
        self.assertIsNotNone(first_alert)

        # Insert an 8th elevated score (now 8 in the window).
        _insert_scores(self.db, user.id, "Admin", [0.41])
        second_alert = check_sustained_elevation(self.db, user.id, user.name, "Admin")
        self.db.commit()

        self.assertIsNone(
            second_alert,
            "A second escalation alert must not be created within the dedup window"
        )

    def test_dedup_window_expired_allows_new_alert(self):
        """
        An escalation alert older than TREND_DEDUP_DAYS should not block a
        new one — the dedup check uses created_at >= cutoff.
        """
        user = _make_user(self.db)

        # Manually insert an old escalation alert outside the dedup window.
        old_alert = AnomalyAlert(
            user_id=user.id,
            anomaly_score=0.40,
            severity="MEDIUM",
            top_features=[],
            explanation="sustained elevated behaviour escalation (old)",
            audit_entry_id=None,
            is_acknowledged=False,
        )
        old_alert.created_at = datetime.utcnow() - timedelta(days=TREND_DEDUP_DAYS + 1)
        self.db.add(old_alert)
        self.db.flush()

        _insert_scores(self.db, user.id, "Admin", [0.40] * TREND_WINDOW)
        new_alert = check_sustained_elevation(self.db, user.id, user.name, "Admin")
        self.assertIsNotNone(
            new_alert,
            "An escalation alert should be allowed once the dedup window has expired"
        )


class TestStreakMustBeConsecutive(unittest.TestCase):
    """
    The 7 scores must be the 7 most-recent ones — a single sub-threshold score
    inserted between elevated ones breaks the streak.
    """

    def setUp(self):
        Base.metadata.drop_all(ENGINE)
        Base.metadata.create_all(ENGINE)
        self.db: Session = TestSession()

    def tearDown(self):
        self.db.close()

    def test_low_score_in_last_seven_breaks_streak(self):
        """
        6 elevated + 1 low score (most recent) → last 7 contain a low → no alert.
        """
        user = _make_user(self.db)
        # 6 elevated scores, then one sub-threshold score as the most recent
        scores = [0.40, 0.42, 0.38, 0.41, 0.39, 0.43,  # elevated
                  0.20]                                   # sub-threshold (newest)
        _insert_scores(self.db, user.id, "Admin", scores)
        result = check_sustained_elevation(self.db, user.id, user.name, "Admin")
        self.assertIsNone(
            result,
            "A sub-threshold score as the most-recent entry must break the streak"
        )

    def test_low_score_older_than_seven_does_not_break_streak(self):
        """
        1 old low score + 7 recent elevated scores → last 7 are all elevated →
        alert fires.  The old low score is outside the TREND_WINDOW window.
        """
        user = _make_user(self.db)
        base = datetime.utcnow() - timedelta(minutes=20)
        # Old sub-threshold score (minute 0)
        old_low = BehavioralScore(
            user_id=user.id, score=0.10, role="Admin",
            computed_at=base,
        )
        self.db.add(old_low)
        # 7 recent elevated scores (minutes 10–16)
        for i in range(TREND_WINDOW):
            self.db.add(BehavioralScore(
                user_id=user.id, score=0.40, role="Admin",
                computed_at=base + timedelta(minutes=10 + i),
            ))
        self.db.flush()

        result = check_sustained_elevation(self.db, user.id, user.name, "Admin")
        self.assertIsNotNone(
            result,
            "An old low score outside the last-7 window must not suppress the alert"
        )

    def test_low_score_at_position_four_breaks_streak(self):
        """
        Scores: [elevated x3, LOW, elevated x3] — the LOW is inside the last 7.
        """
        user = _make_user(self.db)
        scores = [0.40, 0.42, 0.41,  # positions 7,6,5 (oldest of the 7)
                  0.20,              # position 4 — sub-threshold
                  0.38, 0.39, 0.37]  # positions 3,2,1 (most recent)
        _insert_scores(self.db, user.id, "Admin", scores)
        result = check_sustained_elevation(self.db, user.id, user.name, "Admin")
        self.assertIsNone(
            result,
            "A sub-threshold score at any position within the last 7 must break the streak"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
