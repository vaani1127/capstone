"""
Tests for read-path audit chain logging.

Verifies that _log_read_audit writes exactly one AuditChain entry with the
correct record_type and user_id for each targeted GET endpoint.

All tests use an in-memory SQLite database — no live PostgreSQL required.
_log_read_audit now opens its own session via SessionLocal, so tests patch
medical_records.SessionLocal to redirect it to the test engine.
"""

import asyncio
import sys
import os
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, event as sa_event
from sqlalchemy.orm import sessionmaker, Session

from app.db.base import Base, import_models
import_models()

from app.models.audit_chain import AuditChain
from app.models.user import User, UserRole
import app.api.v1.endpoints.medical_records as mr_module
from app.api.v1.endpoints.medical_records import _log_read_audit

ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
)

@sa_event.listens_for(ENGINE, "connect")
def _set_sqlite_pragma(conn, _):
    conn.execute("PRAGMA foreign_keys=ON")

Base.metadata.create_all(ENGINE)
TestSession = sessionmaker(bind=ENGINE)


def _make_user(db: Session, name: str = "Tester", role: str = "Doctor") -> User:
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


def _run(coro):
    """Run a coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


class _AuditBase(unittest.TestCase):
    """
    Base class that rebuilds the schema, opens a session, and patches
    mr_module.SessionLocal so _log_read_audit uses the test engine.
    """

    def setUp(self):
        Base.metadata.drop_all(ENGINE)
        Base.metadata.create_all(ENGINE)
        self.db: Session = TestSession()
        # Patch SessionLocal in the medical_records module so _log_read_audit
        # opens sessions against the in-memory test engine, not PostgreSQL.
        self._patcher = patch.object(mr_module, "SessionLocal", TestSession)
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        self.db.close()


class TestLogReadAuditPatientRecords(_AuditBase):

    def test_creates_exactly_one_audit_entry(self):
        user = _make_user(self.db)
        self.db.commit()
        _run(_log_read_audit(42, "patient_records_viewed", {"patient_id": 42}, user.id))
        entries = self.db.query(AuditChain).all()
        self.assertEqual(len(entries), 1)

    def test_record_type_is_patient_records_viewed(self):
        user = _make_user(self.db)
        self.db.commit()
        _run(_log_read_audit(7, "patient_records_viewed", {"patient_id": 7}, user.id))
        entry = self.db.query(AuditChain).first()
        self.assertEqual(entry.record_type, "patient_records_viewed")

    def test_user_id_matches_accessor(self):
        user = _make_user(self.db)
        self.db.commit()
        _run(_log_read_audit(7, "patient_records_viewed", {"patient_id": 7}, user.id))
        entry = self.db.query(AuditChain).first()
        self.assertEqual(entry.user_id, user.id)

    def test_record_id_matches_patient_id(self):
        user = _make_user(self.db)
        self.db.commit()
        _run(_log_read_audit(99, "patient_records_viewed", {"patient_id": 99}, user.id))
        entry = self.db.query(AuditChain).first()
        self.assertEqual(entry.record_id, 99)

    def test_hash_chain_is_populated(self):
        user = _make_user(self.db)
        self.db.commit()
        _run(_log_read_audit(1, "patient_records_viewed", {"patient_id": 1}, user.id))
        entry = self.db.query(AuditChain).first()
        self.assertEqual(len(entry.hash), 64, "SHA-256 hash should be 64 hex chars")
        self.assertEqual(entry.previous_hash, "0", "Genesis block should chain from '0'")


class TestLogReadAuditRecordVersions(_AuditBase):

    def test_creates_exactly_one_audit_entry(self):
        user = _make_user(self.db)
        self.db.commit()
        _run(_log_read_audit(5, "medical_record_versions_viewed",
                             {"record_id": 5, "patient_id": 3}, user.id))
        entries = self.db.query(AuditChain).all()
        self.assertEqual(len(entries), 1)

    def test_record_type_is_medical_record_versions_viewed(self):
        user = _make_user(self.db)
        self.db.commit()
        _run(_log_read_audit(5, "medical_record_versions_viewed",
                             {"record_id": 5, "patient_id": 3}, user.id))
        entry = self.db.query(AuditChain).first()
        self.assertEqual(entry.record_type, "medical_record_versions_viewed")

    def test_user_id_matches_accessor(self):
        user = _make_user(self.db)
        self.db.commit()
        _run(_log_read_audit(5, "medical_record_versions_viewed",
                             {"record_id": 5, "patient_id": 3}, user.id))
        entry = self.db.query(AuditChain).first()
        self.assertEqual(entry.user_id, user.id)

    def test_record_id_matches_record_id_param(self):
        user = _make_user(self.db)
        self.db.commit()
        _run(_log_read_audit(17, "medical_record_versions_viewed",
                             {"record_id": 17, "patient_id": 3}, user.id))
        entry = self.db.query(AuditChain).first()
        self.assertEqual(entry.record_id, 17)


class TestLogReadAuditChaining(_AuditBase):
    """Two successive read events must form a two-link hash chain."""

    def test_second_entry_chains_from_first(self):
        user = _make_user(self.db)
        self.db.commit()
        _run(_log_read_audit(1, "patient_records_viewed", {"patient_id": 1}, user.id))
        _run(_log_read_audit(2, "patient_records_viewed", {"patient_id": 2}, user.id))
        entries = self.db.query(AuditChain).order_by(AuditChain.id).all()
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[1].previous_hash, entries[0].hash)

    def test_mixed_types_form_single_chain(self):
        """Read and version-view events share the same chain."""
        user = _make_user(self.db)
        self.db.commit()
        _run(_log_read_audit(1, "patient_records_viewed", {"patient_id": 1}, user.id))
        _run(_log_read_audit(5, "medical_record_versions_viewed",
                             {"record_id": 5, "patient_id": 1}, user.id))
        entries = self.db.query(AuditChain).order_by(AuditChain.id).all()
        self.assertEqual(entries[1].previous_hash, entries[0].hash)


class TestLogReadAuditErrorHandling(_AuditBase):
    """Failures must be logged, not silently swallowed."""

    def test_db_error_is_logged_not_raised(self):
        """A broken db must not propagate an exception to the caller."""
        with patch.object(mr_module, "create_audit_entry", side_effect=RuntimeError("db down")):
            # Should complete without raising
            try:
                _run(_log_read_audit(1, "patient_records_viewed", {"patient_id": 1}, 99))
            except Exception as exc:
                self.fail(f"_log_read_audit raised unexpectedly: {exc}")

    def test_error_log_includes_user_id(self):
        import logging
        with patch.object(mr_module, "create_audit_entry", side_effect=RuntimeError("boom")):
            with self.assertLogs("app.api.v1.endpoints.medical_records", level="ERROR") as cm:
                _run(_log_read_audit(5, "patient_records_viewed", {"patient_id": 5}, 42))
        # The error message must include the user_id so compliance teams can
        # identify whose access failed to audit.
        combined = " ".join(cm.output)
        self.assertIn("42", combined)
        self.assertIn("patient_records_viewed", combined)
        self.assertIn("5", combined)


if __name__ == "__main__":
    unittest.main(verbosity=2)
