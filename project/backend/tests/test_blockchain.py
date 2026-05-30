"""
Tests for blockchain/audit chain service and API endpoints.

Covers: hash generation, chain linkage, integrity verification,
tamper detection, flag_tampered_record, and the audit HTTP API.
"""
import pytest
from datetime import datetime

from app.models.audit_chain import AuditChain
from app.models.medical_record import MedicalRecord
from app.services.blockchain_service import (
    create_audit_entry,
    create_medical_record_audit_entry,
    flag_tampered_record,
    generate_hash,
    verify_chain_integrity,
    verify_record_integrity,
)

AUDIT = "/api/v1/audit"


# ---------------------------------------------------------------------------
# Hash generation (pure function — no DB needed)
# ---------------------------------------------------------------------------

def test_generate_hash_is_64_hex_chars():
    h = generate_hash({"k": "v"}, datetime(2024, 1, 1), user_id=1, previous_hash="0")
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_generate_hash_is_deterministic():
    args = ({"k": "v"}, datetime(2024, 6, 1, 12, 0), 42, "abc123")
    assert generate_hash(*args) == generate_hash(*args)


def test_generate_hash_differs_for_different_inputs():
    ts = datetime(2024, 1, 1)
    h1 = generate_hash({"n": 1}, ts, user_id=1, previous_hash="0")
    h2 = generate_hash({"n": 2}, ts, user_id=1, previous_hash="0")
    assert h1 != h2


# ---------------------------------------------------------------------------
# Audit entry creation
# ---------------------------------------------------------------------------

def test_create_audit_entry_genesis_block(db, patient_user):
    pat_user, _ = patient_user

    entry = create_audit_entry(db, record_id=100, record_type="test", record_data={"x": 1}, user_id=pat_user.id)
    db.commit()

    assert entry.id is not None
    assert entry.previous_hash == "0"
    assert len(entry.hash) == 64
    assert entry.is_tampered is False
    assert entry.record_type == "test"


def test_create_audit_entry_links_to_previous(db, patient_user):
    pat_user, _ = patient_user

    e1 = create_audit_entry(db, 1, "event", {"a": 1}, pat_user.id)
    e2 = create_audit_entry(db, 2, "event", {"b": 2}, pat_user.id)
    db.commit()

    assert e2.previous_hash == e1.hash


def test_create_medical_record_audit_entry(db, patient_user, doctor_user):
    pat_user, patient = patient_user
    doc_user, doctor = doctor_user

    record = MedicalRecord(
        patient_id=patient.id,
        doctor_id=doctor.id,
        consultation_notes="Notes",
        version_number=1,
        created_by=doc_user.id,
    )
    db.add(record)
    db.flush()

    entry = create_medical_record_audit_entry(db, record, doc_user.id)
    db.commit()

    assert entry.record_id == record.id
    assert entry.record_type == "medical_record"


# ---------------------------------------------------------------------------
# Integrity verification
# ---------------------------------------------------------------------------

def _make_medical_record(db, patient, doctor, doc_user, notes="Test notes"):
    record = MedicalRecord(
        patient_id=patient.id,
        doctor_id=doctor.id,
        consultation_notes=notes,
        version_number=1,
        created_by=doc_user.id,
    )
    db.add(record)
    db.flush()
    create_medical_record_audit_entry(db, record, doc_user.id)
    db.commit()
    return record


def test_verify_record_integrity_valid(db, patient_user, doctor_user):
    pat_user, patient = patient_user
    doc_user, doctor = doctor_user

    record = _make_medical_record(db, patient, doctor, doc_user)
    assert verify_record_integrity(db, record.id) is True


def test_verify_record_no_audit_entry_raises(db):
    with pytest.raises(ValueError, match="No audit"):
        verify_record_integrity(db, record_id=99999)


def test_verify_record_detects_tampering(db, patient_user, doctor_user):
    pat_user, patient = patient_user
    doc_user, doctor = doctor_user

    record = _make_medical_record(db, patient, doctor, doc_user)

    # Directly tamper with stored record_data in audit chain
    audit = (
        db.query(AuditChain)
        .filter(AuditChain.record_id == record.id, AuditChain.record_type == "medical_record")
        .first()
    )
    audit.record_data = {"consultation_notes": "TAMPERED"}
    db.commit()

    assert verify_record_integrity(db, record.id) is False


# ---------------------------------------------------------------------------
# flag_tampered_record
# ---------------------------------------------------------------------------

def test_flag_tampered_record_sets_is_tampered(db, patient_user, doctor_user):
    pat_user, patient = patient_user
    doc_user, doctor = doctor_user

    record = _make_medical_record(db, patient, doctor, doc_user)
    flag_tampered_record(db, record.id, "medical_record")

    audit = (
        db.query(AuditChain)
        .filter(AuditChain.record_id == record.id, AuditChain.record_type == "medical_record")
        .order_by(AuditChain.id.desc())
        .first()
    )
    assert audit.is_tampered is True


# ---------------------------------------------------------------------------
# Chain integrity
# ---------------------------------------------------------------------------

def test_verify_chain_integrity_empty_chain(db):
    result = verify_chain_integrity(db)
    assert result["is_valid"] is True
    assert result["total_blocks"] == 0


def test_verify_chain_integrity_valid_chain(db, patient_user):
    pat_user, _ = patient_user

    create_audit_entry(db, 10, "ev", {"n": 1}, pat_user.id)
    create_audit_entry(db, 11, "ev", {"n": 2}, pat_user.id)
    create_audit_entry(db, 12, "ev", {"n": 3}, pat_user.id)
    db.commit()

    result = verify_chain_integrity(db)
    assert result["is_valid"] is True
    assert result["total_blocks"] == 3


def test_verify_chain_integrity_detects_broken_link(db, patient_user):
    pat_user, _ = patient_user

    e1 = create_audit_entry(db, 20, "ev", {"x": 1}, pat_user.id)
    e2 = create_audit_entry(db, 21, "ev", {"x": 2}, pat_user.id)
    db.commit()

    # Break the chain by corrupting entry2's previous_hash
    e2.previous_hash = "0000000000000000000000000000000000000000000000000000000000000000"
    db.commit()

    result = verify_chain_integrity(db)
    assert result["is_valid"] is False


# ---------------------------------------------------------------------------
# Audit HTTP API
# ---------------------------------------------------------------------------

def test_audit_verify_endpoint_valid_record(client, patient_user, doctor_user, admin_headers, db):
    pat_user, patient = patient_user
    doc_user, doctor = doctor_user

    record = _make_medical_record(db, patient, doctor, doc_user)

    resp = client.post(f"{AUDIT}/verify/{record.id}", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is True
    assert data["record_id"] == record.id


def test_audit_verify_endpoint_missing_record_returns_404(client, admin_headers):
    resp = client.post(f"{AUDIT}/verify/99999", headers=admin_headers)
    assert resp.status_code == 404


def test_audit_verify_requires_admin(client, patient_headers):
    resp = client.post(f"{AUDIT}/verify/1", headers=patient_headers)
    assert resp.status_code == 403


def test_chain_integrity_endpoint(client, patient_user, admin_headers, db):
    pat_user, _ = patient_user

    create_audit_entry(db, 1, "test", {"y": 1}, pat_user.id)
    db.commit()

    resp = client.get(f"{AUDIT}/chain-integrity", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is True
    assert data["total_blocks"] >= 1


def test_chain_integrity_requires_admin(client, doctor_headers):
    resp = client.get(f"{AUDIT}/chain-integrity", headers=doctor_headers)
    assert resp.status_code == 403


def test_audit_logs_endpoint_accessible_by_admin(client, admin_headers):
    resp = client.get(f"{AUDIT}/logs", headers=admin_headers)
    assert resp.status_code == 200


def test_audit_logs_requires_admin(client, patient_headers):
    resp = client.get(f"{AUDIT}/logs", headers=patient_headers)
    assert resp.status_code == 403
