"""
Tests for Alert Narrator — template-based narrative generation for anomaly alerts.

Covers:
  1. Single-event narratives (per-feature templates)
  2. Sustained-trend narratives
  3. Identity-drift narratives
  4. Fallback for unmapped feature combinations
  5. Narrative always populated on alert creation (via narrate_alert)
"""

import sys
import os
import unittest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.alert_narrator import narrate_alert


class TestSingleEventNarratives(unittest.TestCase):
    """Single-event narratives with feature-specific templates."""

    def test_high_actions_per_hour_narrative(self):
        """High access volume spike gets feature-specific narrative."""
        narrative = narrate_alert(
            trigger_type="single_event",
            top_features=[
                {"feature": "actions_per_hour", "value": 18.0, "shap": 0.25}
            ],
            user_name="Alice",
            user_role="Nurse",
            extra_context={"score": 0.65, "baseline": 6.0}
        )
        self.assertIn("actions/hour", narrative.lower())
        self.assertIn("Alice", narrative)
        self.assertIn("Nurse", narrative)
        self.assertGreater(len(narrative), 20)

    def test_patient_access_spike_narrative(self):
        """High unique-patient access spike gets feature-specific narrative."""
        narrative = narrate_alert(
            trigger_type="single_event",
            top_features=[
                {"feature": "unique_patients_accessed", "value": 25, "shap": 0.30}
            ],
            user_name="Bob",
            user_role="Doctor",
            extra_context={"score": 0.58, "baseline": 5}
        )
        self.assertIn("patient", narrative.lower())
        self.assertIn("Bob", narrative)
        self.assertIn("Doctor", narrative)

    def test_off_hours_access_narrative(self):
        """Off-hours access gets feature-specific narrative."""
        narrative = narrate_alert(
            trigger_type="single_event",
            top_features=[
                {"feature": "off_hours_flag", "value": 1, "shap": 0.40}
            ],
            user_name="Charlie",
            user_role="Nurse",
            extra_context={"score": 0.72}
        )
        self.assertIn("off-hours", narrative.lower())
        self.assertIn("Charlie", narrative)

    def test_rapid_edits_narrative(self):
        """Rapid edits get feature-specific narrative."""
        narrative = narrate_alert(
            trigger_type="single_event",
            top_features=[
                {"feature": "rapid_edit_flag", "value": 1, "shap": 0.35}
            ],
            user_name="Diana",
            user_role="Doctor",
            extra_context={"score": 0.62}
        )
        self.assertIn("rapid", narrative.lower())
        self.assertIn("Diana", narrative)


class TestSustainedTrendNarrative(unittest.TestCase):
    """Sustained-trend alert narratives."""

    def test_sustained_trend_narrative(self):
        """Sustained trend gets appropriate narrative."""
        narrative = narrate_alert(
            trigger_type="sustained_trend",
            top_features=[],
            user_name="Eve",
            user_role="Admin",
            extra_context={
                "score_count": 7,
                "timestamp": "2026-08-01T10:00:00"
            }
        )
        self.assertIn("7", narrative)
        self.assertIn("consecutive", narrative.lower())
        self.assertIn("Eve", narrative)
        self.assertIn("Admin", narrative)


class TestIdentityDriftNarrative(unittest.TestCase):
    """Identity-drift alert narratives."""

    def test_identity_drift_narrative(self):
        """Identity drift gets appropriate narrative with role transition."""
        narrative = narrate_alert(
            trigger_type="identity_drift",
            top_features=[
                {"feature": "cross_role_drift", "value": 20.0, "shap": 0.36}
            ],
            user_name="Frank",
            user_role="Nurse",
            extra_context={
                "target_role": "Doctor",
                "privilege_gap": 1,
                "initial_distance": 50.0,
                "current_distance": 20.0,
                "importance": 0.36
            }
        )
        self.assertIn("Frank", narrative)
        self.assertIn("Nurse", narrative)
        self.assertIn("Doctor", narrative)
        self.assertIn("privilege", narrative.lower())
        self.assertIn("50.0", narrative)
        self.assertIn("20.0", narrative)
        self.assertIn("0.36", narrative)


class TestNarrativeFallback(unittest.TestCase):
    """Fallback narrative for unmapped feature combinations."""

    def test_unmapped_feature_fallback(self):
        """Unmapped (trigger_type, feature) pair uses generic fallback."""
        narrative = narrate_alert(
            trigger_type="single_event",
            top_features=[
                {"feature": "unknown_future_feature", "value": 99.9, "shap": 0.88}
            ],
            user_name="Grace",
            user_role="Patient",
            extra_context={"score": 0.80}
        )
        # Should still have user info even though feature is unmapped
        self.assertIn("Grace", narrative)
        self.assertIn("Patient", narrative)
        self.assertGreater(len(narrative), 20)

    def test_empty_top_features_fallback(self):
        """Empty top_features list uses generic fallback."""
        narrative = narrate_alert(
            trigger_type="single_event",
            top_features=[],
            user_name="Henry",
            user_role="Doctor",
            extra_context={"score": 0.55}
        )
        self.assertIn("Henry", narrative)
        self.assertIn("Doctor", narrative)
        self.assertGreater(len(narrative), 20)


class TestNarrativeContentQuality(unittest.TestCase):
    """Narrative content quality and consistency checks."""

    def test_narrative_is_single_sentence(self):
        """Each narrative should be a reasonably concise single sentence."""
        narrative = narrate_alert(
            trigger_type="single_event",
            top_features=[
                {"feature": "actions_per_hour", "value": 20.0, "shap": 0.25}
            ],
            user_name="Iris",
            user_role="Nurse",
            extra_context={"score": 0.65, "baseline": 6.0}
        )
        # Should end with period (single sentence)
        self.assertTrue(narrative.endswith("."))
        # Should not be excessively long
        self.assertLess(len(narrative), 500)

    def test_all_trigger_types_produce_narrative(self):
        """All three trigger types should produce non-empty narratives."""
        for trigger_type in ["single_event", "sustained_trend", "identity_drift"]:
            if trigger_type == "identity_drift":
                extra = {
                    "target_role": "Doctor",
                    "privilege_gap": 1,
                    "initial_distance": 50.0,
                    "current_distance": 20.0,
                    "importance": 0.36
                }
            else:
                extra = {"score": 0.65}

            narrative = narrate_alert(
                trigger_type=trigger_type,
                top_features=[{"feature": "test_feature", "value": 1.0, "shap": 0.1}]
                if trigger_type != "sustained_trend"
                else [],
                user_name="Test User",
                user_role="Doctor",
                extra_context=extra
            )
            self.assertIsNotNone(narrative)
            self.assertGreater(len(narrative), 0)
            self.assertIn("Test User", narrative)

    def test_narrative_includes_key_context(self):
        """Narrative should include user name and role at minimum."""
        test_cases = [
            ("single_event", [{"feature": "actions_per_hour", "value": 20.0, "shap": 0.25}]),
            ("sustained_trend", []),
            ("identity_drift", [{"feature": "cross_role_drift", "value": 20.0, "shap": 0.36}])
        ]

        for trigger_type, features in test_cases:
            extra = {"score": 0.65}
            if trigger_type == "identity_drift":
                extra = {
                    "target_role": "Doctor",
                    "privilege_gap": 1,
                    "initial_distance": 50.0,
                    "current_distance": 20.0,
                    "importance": 0.36
                }

            narrative = narrate_alert(
                trigger_type=trigger_type,
                top_features=features,
                user_name="TestUser",
                user_role="Nurse",
                extra_context=extra
            )
            # Always has user name and role
            self.assertIn("TestUser", narrative, f"Missing user name in {trigger_type}")
            self.assertIn("Nurse", narrative, f"Missing role in {trigger_type}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
