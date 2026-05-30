"""
Tests for medical record endpoints: creation, versioning, RBAC access control.
"""
import pytest
from datetime import datetime, timedelta

from app.core.security import get_password_hash, create_access_token
from app.models.appointment import Appointment, AppointmentStatus, AppointmentType
from app.models.audit_chain import AuditChain
from app.models.medical_record import MedicalRecord

RECORDS = "/api/v1/medical-records"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_appointment(db, patient_id, doctor_id, hours_ahead=24):
    appt = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        scheduled_time=datetime.utcnow() + timedelta(hours=hours_ahead),
        status=AppointmentStatus.IN_PROGRESS,
        appointment_type=AppointmentType.SCHEDULED,
        queue_position=1,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt


def _make_second_doctor(db):
    from app.models.doctor import Doctor
    from app.models.user import User, UserRole

    user = User(
        name="Other Doctor",
        email="otherdoc@test.com",
        password_hash=get_password_hash("TestPass123"),
        role=UserRole.DOCTOR,
    )
    db.add(user)
    db.commit()

    doc = Doctor(
        user_id=user.id,
        specialization="Neurology",
        license_number="DOC002",
        average_consultation_duration=20,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    db.refresh(user)

    token = create_access_token({"user_id": user.id, "email": user.email, "role": "Doctor"})
    return user, doc, {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# POST /consultation-notes
# ---------------------------------------------------------------------------

def test_create_consultation_note_success(client, patient_user, doctor_user, doctor_headers, db):
    _, patient = patient_user
    _, doctor = doctor_user
    appt = _make_appointment(db, patient.id, doctor.id)

    resp = client.post(f"{RECORDS}/consultation-notes", json={
        "appointment_id": appt.id,
        "consultation_notes": "Patient has mild fever.",
        "diagnosis": "Viral infection",
    }, headers=doctor_headers)

    assert resp.status_code == 201
    data = resp.json()
    assert data["consultation_notes"] == "Patient has mild fever."
    assert data["diagnosis"] == "Viral infection"
    assert data["version_number"] == 1
    assert data["doctor_id"] == doctor.id


def test_create_consultation_note_creates_audit_entry(client, patient_user, doctor_user, doctor_headers, db):
    _, patient = patient_user
    _, doctor = doctor_user
    appt = _make_appointment(db, patient.id, doctor.id)

    resp = client.post(f"{RECORDS}/consultation-notes", json={
        "appointment_id": appt.id,
        "consultation_notes": "Audit test note.",
    }, headers=doctor_headers)
    assert resp.status_code == 201

    record_id = resp.json()["id"]
    entry = db.query(AuditChain).filter(
        AuditChain.record_id == record_id,
        AuditChain.record_type == "medical_record",
    ).first()
    assert entry is not None


def test_create_consultation_note_patient_forbidden(client, patient_user, doctor_user, patient_headers, db):
    _, patient = patient_user
    _, doctor = doctor_user
    appt = _make_appointment(db, patient.id, doctor.id)

    resp = client.post(f"{RECORDS}/consultation-notes", json={
        "appointment_id": appt.id,
        "consultation_notes": "Unauthorized.",
    }, headers=patient_headers)

    assert resp.status_code == 403


def test_create_consultation_note_wrong_doctor_forbidden(client, patient_user, doctor_user, db):
    _, patient = patient_user
    _, doctor = doctor_user
    appt = _make_appointment(db, patient.id, doctor.id)

    _, _, other_headers = _make_second_doctor(db)

    resp = client.post(f"{RECORDS}/consultation-notes", json={
        "appointment_id": appt.id,
        "consultation_notes": "Not my patient.",
    }, headers=other_headers)

    assert resp.status_code == 403


def test_duplicate_consultation_note_rejected(client, patient_user, doctor_user, doctor_headers, db):
    _, patient = patient_user
    _, doctor = doctor_user
    appt = _make_appointment(db, patient.id, doctor.id)

    payload = {
        "appointment_id": appt.id,
        "consultation_notes": "First note.",
    }
    client.post(f"{RECORDS}/consultation-notes", json=payload, headers=doctor_headers)
    resp = client.post(f"{RECORDS}/consultation-notes", json=payload, headers=doctor_headers)

    assert resp.status_code == 400
    assert "already exists" in resp.json()["detail"].lower()


def test_consultation_note_appointment_not_found(client, doctor_headers):
    resp = client.post(f"{RECORDS}/consultation-notes", json={
        "appointment_id": 99999,
        "consultation_notes": "For ghost appointment.",
    }, headers=doctor_headers)

    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST / (general create)
# ---------------------------------------------------------------------------

def test_create_medical_record_success(client, patient_user, doctor_user, doctor_headers, db):
    _, patient = patient_user
    _, doctor = doctor_user
    appt = _make_appointment(db, patient.id, doctor.id)

    resp = client.post(f"{RECORDS}/", json={
        "appointment_id": appt.id,
        "consultation_notes": "Full record notes.",
        "diagnosis": "Hypertension",
        "prescription": "Amlodipine 5mg once daily",
    }, headers=doctor_headers)

    assert resp.status_code == 201
    data = resp.json()
    assert data["prescription"] == "Amlodipine 5mg once daily"
    assert data["diagnosis"] == "Hypertension"
    assert data["version_number"] == 1


def test_create_medical_record_audit_entry_created(client, patient_user, doctor_user, doctor_headers, db):
    _, patient = patient_user
    _, doctor = doctor_user
    appt = _make_appointment(db, patient.id, doctor.id)

    resp = client.post(f"{RECORDS}/", json={
        "appointment_id": appt.id,
        "consultation_notes": "Blockchain test.",
    }, headers=doctor_headers)
    assert resp.status_code == 201

    record_id = resp.json()["id"]
    entry = db.query(AuditChain).filter(
        AuditChain.record_id == record_id,
        AuditChain.record_type == "medical_record",
    ).first()
    assert entry is not None


def test_create_medical_record_duplicate_rejected(client, patient_user, doctor_user, doctor_headers, db):
    _, patient = patient_user
    _, doctor = doctor_user
    appt = _make_appointment(db, patient.id, doctor.id)

    payload = {"appointment_id": appt.id, "consultation_notes": "Note."}
    client.post(f"{RECORDS}/", json=payload, headers=doctor_headers)
    resp = client.post(f"{RECORDS}/", json=payload, headers=doctor_headers)

    assert resp.status_code == 400


def test_create_medical_record_patient_forbidden(client, patient_user, doctor_user, patient_headers, db):
    _, patient = patient_user
    _, doctor = doctor_user
    appt = _make_appointment(db, patient.id, doctor.id)

    resp = client.post(f"{RECORDS}/", json={
        "appointment_id": appt.id,
        "consultation_notes": "Unauthorized.",
    }, headers=patient_headers)

    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /patient/{patient_id} — RBAC
# ---------------------------------------------------------------------------

def test_patient_views_own_records(client, patient_user, doctor_user, patient_headers, db):
    _, patient = patient_user
    _, doctor = doctor_user
    appt = _make_appointment(db, patient.id, doctor.id)

    record = MedicalRecord(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_id=appt.id,
        consultation_notes="Patient's record.",
        version_number=1,
        created_by=doctor.user_id,
    )
    db.add(record)
    db.commit()

    resp = client.get(f"{RECORDS}/patient/{patient.id}", headers=patient_headers)
    assert resp.status_code == 200
    records = resp.json()
    assert len(records) == 1
    assert records[0]["patient_id"] == patient.id


def test_patient_cannot_view_others_records(client, patient_user, doctor_user, db):
    from app.models.patient import Patient
    from app.models.user import User, UserRole

    _, patient = patient_user
    _, doctor = doctor_user

    user2 = User(
        name="Other Patient",
        email="other_pat@test.com",
        password_hash=get_password_hash("TestPass123"),
        role=UserRole.PATIENT,
    )
    db.add(user2)
    db.commit()
    pat2 = Patient(user_id=user2.id)
    db.add(pat2)
    db.commit()

    token = create_access_token({"user_id": user2.id, "email": user2.email, "role": "Patient"})
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get(f"{RECORDS}/patient/{patient.id}", headers=headers)
    assert resp.status_code == 403


def test_doctor_can_view_treated_patient_records(client, patient_user, doctor_user, doctor_headers, db):
    _, patient = patient_user
    _, doctor = doctor_user

    appt = _make_appointment(db, patient.id, doctor.id)
    record = MedicalRecord(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_id=appt.id,
        consultation_notes="Treated notes.",
        version_number=1,
        created_by=doctor.user_id,
    )
    db.add(record)
    db.commit()

    resp = client.get(f"{RECORDS}/patient/{patient.id}", headers=doctor_headers)
    assert resp.status_code == 200


def test_doctor_cannot_view_untreated_patient_records(client, patient_user, doctor_user, db):
    _, patient = patient_user
    _, doctor = doctor_user

    # No medical records for this doctor-patient pair
    _, _, other_doctor_headers = _make_second_doctor(db)

    resp = client.get(f"{RECORDS}/patient/{patient.id}", headers=other_doctor_headers)
    assert resp.status_code == 403


def test_nurse_cannot_view_medical_records(client, patient_user, nurse_headers):
    _, patient = patient_user

    resp = client.get(f"{RECORDS}/patient/{patient.id}", headers=nurse_headers)
    assert resp.status_code == 403


def test_admin_can_view_any_records(client, patient_user, doctor_user, admin_headers, db):
    _, patient = patient_user
    _, doctor = doctor_user

    resp = client.get(f"{RECORDS}/patient/{patient.id}", headers=admin_headers)
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /me
# ---------------------------------------------------------------------------

def test_get_my_records_patient_success(client, patient_user, doctor_user, patient_headers, db):
    _, patient = patient_user
    _, doctor = doctor_user
    appt = _make_appointment(db, patient.id, doctor.id)

    record = MedicalRecord(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_id=appt.id,
        consultation_notes="My record.",
        version_number=1,
        created_by=doctor.user_id,
    )
    db.add(record)
    db.commit()

    resp = client.get(f"{RECORDS}/me", headers=patient_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_my_records_non_patient_forbidden(client, doctor_headers):
    resp = client.get(f"{RECORDS}/me", headers=doctor_headers)
    assert resp.status_code == 403
