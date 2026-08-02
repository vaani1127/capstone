"""
Unit tests for Feature C: Adaptive Contamination Auto-Tuning.

Tests verify:
1. compute_adaptive_contamination() function behavior
2. Regression test: flag-OFF produces identical baseline scores
3. Flag-ON behavior: adaptive values scale correctly with log count
"""

import os
import json
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add backend to path
import sys
sys.path.insert(0, 'd:/My Workspace/capstone work/Capstone/project/backend')

from app.db.base import Base, import_models
from app.models.user import User
from app.models.audit_chain import AuditChain
from app.services.anomaly_service import (
    compute_adaptive_contamination,
    score_event,
    DEFAULT_CONTAMINATION,
)

import_models()

# Test database
TEST_DATABASE_URL = 'postgresql://postgres:devpassword@localhost:5432/healthsaathi_dev'


class TestAdaptiveContamination:
    """Test adaptive contamination feature."""

    @pytest.fixture(scope="class")
    def db(self):
        """Create test database session."""
        engine = create_engine(TEST_DATABASE_URL, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    def test_compute_adaptive_contamination_below_threshold(self):
        """Low log count → contamination below default."""
        log_count = 100
        threshold = 500
        expected = DEFAULT_CONTAMINATION * (100 / 500)  # 0.08 * 0.2 = 0.016

        result = compute_adaptive_contamination(
            role="Doctor",
            log_count_last_n_days=log_count,
            default_contamination=DEFAULT_CONTAMINATION,
            log_count_threshold=threshold
        )

        assert result == pytest.approx(expected, rel=1e-4)
        assert result < DEFAULT_CONTAMINATION

    def test_compute_adaptive_contamination_at_threshold(self):
        """Log count at threshold → contamination equals default."""
        log_count = 500
        threshold = 500

        result = compute_adaptive_contamination(
            role="Doctor",
            log_count_last_n_days=log_count,
            default_contamination=DEFAULT_CONTAMINATION,
            log_count_threshold=threshold
        )

        assert result == DEFAULT_CONTAMINATION

    def test_compute_adaptive_contamination_above_threshold(self):
        """High log count → contamination equals default."""
        log_count = 1000
        threshold = 500

        result = compute_adaptive_contamination(
            role="Nurse",
            log_count_last_n_days=log_count,
            default_contamination=DEFAULT_CONTAMINATION,
            log_count_threshold=threshold
        )

        assert result == DEFAULT_CONTAMINATION

    def test_compute_adaptive_contamination_zero_logs(self):
        """Zero logs → returns minimum (0.001), not zero."""
        log_count = 0
        threshold = 500

        result = compute_adaptive_contamination(
            role="Admin",
            log_count_last_n_days=log_count,
            default_contamination=DEFAULT_CONTAMINATION,
            log_count_threshold=threshold
        )

        # 0 logs: 0.08 * (0 / 500) = 0.0 → clamped to min 0.001
        assert result == 0.001

    def test_compute_adaptive_contamination_midpoint(self):
        """Mid-range log count → linear interpolation."""
        log_count = 250
        threshold = 500
        expected = DEFAULT_CONTAMINATION * 0.5  # 0.08 * 0.5 = 0.04

        result = compute_adaptive_contamination(
            role="Patient",
            log_count_last_n_days=log_count,
            default_contamination=DEFAULT_CONTAMINATION,
            log_count_threshold=threshold
        )

        assert result == pytest.approx(expected, rel=1e-4)

    def test_regression_flag_off_baseline_match(self, db):
        """Flag OFF (default) → scores match saved baseline exactly."""
        # Load baseline
        baseline_file = (
            "C:\\Users\\DELL\\AppData\\Local\\Temp\\claude\\d--My-Workspace-capstone-work-Capstone\\"
            "f035ccbe-f9c3-44ca-922b-56884e17d3e5\\scratchpad\\baseline_scores_pre_feature_c.json"
        )

        assert os.path.exists(baseline_file), f"Baseline file not found: {baseline_file}"

        with open(baseline_file, 'r') as f:
            baseline_scores = json.load(f)

        # Verify environment flag is OFF (default)
        auto_tune = os.getenv("AUTO_TUNE_CONTAMINATION", "false").lower() in ("true", "1", "yes")
        assert not auto_tune, "AUTO_TUNE_CONTAMINATION must be OFF (default) for regression test"

        # Score the same roles again
        roles_to_test = ["Admin", "Doctor", "Nurse", "Patient"]
        feature_vector = {
            "actions_per_hour": 5.0,
            "unique_patients_accessed": 3,
            "off_hours_flag": 0,
            "untreated_patient_ratio": 0.0,
            "record_type_entropy": 0.0,
            "rapid_edit_flag": 0,
            "cross_role_action_flag": 0,
            "session_duration_minutes": 40.0,
        }

        tolerance = 1e-6  # Strict tolerance for regression test

        for role in roles_to_test:
            if role not in baseline_scores:
                pytest.skip(f"Baseline missing role {role}")

            user = db.query(User).filter(User.role == role).first()
            if not user:
                pytest.skip(f"No test user for role {role}")

            score = score_event(features=feature_vector, role=role, db=db)
            baseline_value = baseline_scores[role]["anomaly_score"]

            # Must match to very high precision
            assert abs(float(score) - baseline_value) < tolerance, (
                f"[{role}] Score mismatch: got {score:.6f}, expected {baseline_value:.6f}"
            )

    def test_adaptive_values_scale_linearly(self):
        """Verify contamination values scale linearly within threshold."""
        threshold = 1000
        default = 0.08

        # Test points
        test_cases = [
            (0, 0.001),      # Zero → minimum (0.001)
            (100, default * 0.1),
            (250, default * 0.25),
            (500, default * 0.5),
            (750, default * 0.75),
            (1000, default),      # At threshold → reaches default
            (2000, default),       # Beyond threshold → stays at default
        ]

        for log_count, expected_approx in test_cases:
            result = compute_adaptive_contamination(
                role="Doctor",
                log_count_last_n_days=log_count,
                default_contamination=default,
                log_count_threshold=threshold
            )

            # For zero-logs case, expect clamped minimum
            if log_count == 0:
                assert result == 0.001
            # For at-or-above-threshold cases, expect default
            elif log_count >= threshold:
                assert result == default
            # For in-range cases, expect linear interpolation
            else:
                assert result == pytest.approx(expected_approx, rel=1e-4)
