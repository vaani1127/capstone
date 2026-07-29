"""
Tests for the rule-based fallback explanation in anomaly_service.

Covers:
  1. fallback_feature_explanation() directly — each trigger condition.
  2. explain_event() returning [] when shap.TreeExplainer raises, confirming
     the fallback path is reachable from analyze_and_alert().
"""

import types
import unittest
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Import the functions under test
# ---------------------------------------------------------------------------
import sys
import os

# Allow running from project/backend without a full FastAPI app context
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.anomaly_service import (
    _ROLE_BASELINES,
    analyze_and_alert,
    explain_event,
    fallback_feature_explanation,
    FEATURE_ORDER,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_features(**overrides) -> dict:
    """Return a zeroed feature dict with optional overrides."""
    base = {k: 0.0 for k in FEATURE_ORDER}
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# 1. Direct unit tests for fallback_feature_explanation()
# ---------------------------------------------------------------------------

class TestFallbackExplanationContent(unittest.TestCase):

    def test_returns_non_empty_string(self):
        features = _make_features(
            actions_per_hour=68.0,
            unique_patients_accessed=52.0,
            session_duration_minutes=259.0,
            untreated_patient_ratio=0.80,
            rapid_edit_flag=1.0,
        )
        result = fallback_feature_explanation(features, "Admin", "Alice", 0.82)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 40)

    def test_actions_per_hour_elevated_nurse(self):
        """61 actions/hr is ~3x the Nurse baseline of ~20."""
        features = _make_features(actions_per_hour=61.0)
        result = fallback_feature_explanation(features, "Nurse", "Bob", 0.75)
        self.assertIn("actions/hr", result)
        self.assertIn("Nurse", result)
        baseline = _ROLE_BASELINES["Nurse"]["actions_per_hour"]
        self.assertIn(f"~{baseline:.0f}", result)

    def test_off_hours_flag_mentioned(self):
        features = _make_features(off_hours_flag=1.0, actions_per_hour=5.0)
        result = fallback_feature_explanation(features, "Doctor", "Carol", 0.60)
        self.assertIn("10 PM", result)

    def test_cross_role_action_flag_nurse(self):
        features = _make_features(cross_role_action_flag=1.0)
        result = fallback_feature_explanation(features, "Nurse", "Dave", 0.70)
        self.assertIn("inconsistent with Nurse role permissions", result)

    def test_rapid_edit_flag(self):
        features = _make_features(rapid_edit_flag=1.0)
        result = fallback_feature_explanation(features, "Doctor", "Eve", 0.65)
        self.assertIn("more than 3 times", result)

    def test_session_duration_elevated(self):
        """259 min is ~6.5x the Patient baseline of ~40 min (threshold: 3x)."""
        features = _make_features(session_duration_minutes=259.0)
        result = fallback_feature_explanation(features, "Patient", "Frank", 0.80)
        self.assertIn("259 minutes", result)

    def test_untreated_patient_ratio_doctor(self):
        features = _make_features(untreated_patient_ratio=0.82)
        result = fallback_feature_explanation(features, "Doctor", "Grace", 0.78)
        self.assertIn("no prior appointment", result)

    def test_all_features_zero_still_returns_string(self):
        """Zero features should trigger the generic fallback phrase."""
        features = _make_features()
        result = fallback_feature_explanation(features, "Admin", "Harry", 0.55)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 10)
        self.assertIn("Harry", result)
        self.assertIn("Admin", result)

    def test_unknown_role_does_not_raise(self):
        """An unrecognised role should not crash — baselines default gracefully."""
        features = _make_features(actions_per_hour=90.0)
        result = fallback_feature_explanation(features, "SuperAdmin", "Ivan", 0.90)
        self.assertIsInstance(result, str)

    def test_score_and_username_in_output(self):
        features = _make_features(off_hours_flag=1.0)
        result = fallback_feature_explanation(features, "Nurse", "Julia", 0.83)
        self.assertIn("Julia", result)
        self.assertIn("83%", result)

    def test_rule_based_label_present(self):
        """Fallback output should be distinguishable from SHAP output."""
        features = _make_features(cross_role_action_flag=1.0)
        result = fallback_feature_explanation(features, "Patient", "Ken", 0.72)
        self.assertIn("rule-based", result)


# ---------------------------------------------------------------------------
# 2. Integration: explain_event() returns [] when SHAP raises → fallback fires
# ---------------------------------------------------------------------------

class TestExplainEventFallbackPath(unittest.TestCase):

    def _dummy_model(self):
        """Minimal sklearn-like object that satisfies get_or_train_model."""
        m = MagicMock()
        m.estimators_ = []   # shap.TreeExplainer checks this attribute
        return m

    def test_explain_event_returns_empty_on_shap_exception(self):
        """
        Monkey-patch shap.TreeExplainer to raise, confirm explain_event()
        returns [] rather than propagating the exception.
        """
        features = _make_features(actions_per_hour=68.0, unique_patients_accessed=52.0)
        db_mock  = MagicMock()

        with patch("app.services.anomaly_service.get_or_train_model",
                   return_value=self._dummy_model()), \
             patch("shap.TreeExplainer",
                   side_effect=RuntimeError("Simulated SHAP failure")):

            result = explain_event(features, "Admin", db_mock)

        self.assertEqual(result, [], "explain_event must return [] when SHAP raises")

    def test_fallback_fires_and_is_readable_after_shap_failure(self):
        """
        Simulate the full path: SHAP fails → explain_event returns [] →
        fallback_feature_explanation produces a non-empty, readable string.
        This mirrors what analyze_and_alert() does when top_features is [].
        """
        features = _make_features(
            actions_per_hour=68.0,
            unique_patients_accessed=52.0,
            session_duration_minutes=259.0,
            untreated_patient_ratio=0.80,
        )
        db_mock = MagicMock()

        with patch("app.services.anomaly_service.get_or_train_model",
                   return_value=self._dummy_model()), \
             patch("shap.TreeExplainer",
                   side_effect=RuntimeError("Simulated SHAP failure")):

            top_features = explain_event(features, "Admin", db_mock)

        # This is the exact branch in analyze_and_alert()
        self.assertEqual(top_features, [])

        explanation = fallback_feature_explanation(features, "Admin", "TestUser", 0.82)

        self.assertGreater(len(explanation), 50,
                           "Fallback explanation should be a meaningful sentence")
        self.assertIn("TestUser", explanation)
        self.assertIn("Admin", explanation)
        # Should mention the obviously elevated features
        self.assertIn("actions/hr", explanation)
        self.assertNotIn("exhibited statistically anomalous behavior patterns",
                         explanation,
                         "Fallback should produce specific text, not the old generic phrase")

        print("\n--- Fallback explanation output ---")
        print(explanation)
        print("-----------------------------------")


# ---------------------------------------------------------------------------
# 3. End-to-end: analyze_and_alert() routes to the fallback when SHAP fails
# ---------------------------------------------------------------------------

class TestAnalyzeAndAlertFallbackWiring(unittest.TestCase):
    """
    Confirms that the if/else branch added to analyze_and_alert() correctly
    routes to fallback_feature_explanation() when explain_event() returns [].

    Mocking strategy
    ----------------
    - extract_features  → anomalous feature dict (actions_per_hour=68, etc.)
    - score_event       → 0.82  (above the 0.50 alert threshold)
    - get_or_train_model → dummy model (satisfies explain_event's model lookup)
    - shap.TreeExplainer → raises RuntimeError  (forces explain_event to return [])
    - db                → MagicMock whose .refresh() side_effect sets alert.id=1
                          so the logger.info("%d", alert.id) line does not crash
                          and the function returns the alert rather than None
    """

    def _build_db_mock(self, user_name: str = "Alice", role_value: str = "Admin"):
        """Return a db MagicMock wired to return a plausible User object."""
        user_mock = MagicMock()
        user_mock.id = 1
        user_mock.name = user_name
        # role can be either an enum (has .value) or a plain string
        user_mock.role = MagicMock()
        user_mock.role.value = role_value

        db = MagicMock()
        # db.query(User).filter(...).first() → user_mock
        db.query.return_value.filter.return_value.first.return_value = user_mock
        # db.refresh(alert) must set alert.id so the logger line doesn't blow up
        db.refresh.side_effect = lambda obj: setattr(obj, "id", 1)
        return db

    def _anomalous_features(self):
        return _make_features(
            actions_per_hour=68.0,
            unique_patients_accessed=52.0,
            session_duration_minutes=259.0,
            untreated_patient_ratio=0.80,
            rapid_edit_flag=1.0,
        )

    def test_analyze_and_alert_uses_fallback_when_shap_raises(self):
        """
        Core wiring test: when shap.TreeExplainer raises, analyze_and_alert()
        must store a rule-based explanation, not the old generic phrase.
        """
        db = self._build_db_mock(user_name="Alice", role_value="Admin")

        dummy_model = MagicMock()
        dummy_model.estimators_ = []

        with patch("app.services.anomaly_service.extract_features",
                   return_value=self._anomalous_features()), \
             patch("app.services.anomaly_service.score_event",
                   return_value=0.82), \
             patch("app.services.anomaly_service.get_or_train_model",
                   return_value=dummy_model), \
             patch("shap.TreeExplainer",
                   side_effect=RuntimeError("Simulated SHAP failure")):

            alert = analyze_and_alert(db=db, user_id=1, audit_entry_id=99)

        # Function must return an alert, not None
        self.assertIsNotNone(
            alert,
            "analyze_and_alert() returned None — the fallback path may have crashed; "
            "check that db.refresh sets alert.id so the logger line doesn't raise"
        )

        explanation = alert.explanation

        # Must carry the rule-based marker added by fallback_feature_explanation()
        self.assertIn(
            "rule-based",
            explanation,
            f"Expected 'rule-based' in explanation, got: {explanation!r}"
        )

        # Must NOT fall through to the old generic SHAP-failure phrase
        self.assertNotIn(
            "exhibited statistically anomalous behavior patterns",
            explanation,
            f"Got the old generic phrase instead of the rule-based fallback: {explanation!r}"
        )

        # Spot-check: elevated features should be mentioned by name
        self.assertIn("actions/hr", explanation)
        self.assertIn("Alice", explanation)
        self.assertIn("Admin", explanation)

        print("\n--- analyze_and_alert() fallback explanation ---")
        print(explanation)
        print("------------------------------------------------")


if __name__ == "__main__":
    unittest.main(verbosity=2)
