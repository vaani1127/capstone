"""
Tests for appointment endpoints: CRUD, RBAC, queue management, cancellation rules.
"""
import pytest
from datetime import datetime, timedelta

from app.models.appointment import Appointment, AppointmentStatus, AppointmentType

APPTS = "/api/v1/appointments"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _insert_appointment(db, patient_id, doctor_id, hours_ahead=24, status=AppointmentStatus.SCHEDULED):
    appt = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        scheduled_time=datetime.utcnow() + timedelta(hours=hours_ahead),
        status=status,
        appointment_type=AppointmentType.SCHEDULED,
        queue_position=1,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt


# ---------------------------------------------------------------------------
# Create appointment
# ---------------------------------------------------------------------------

def test_create_appointment_success(client, patient_user, doctor_user, patient_headers, future_time):
    _, patient = patient_user
    _, doctor = doctor_user

    resp = client.post(f"{APPTS}/", json={
        "doctor_id": doctor.id,
        "scheduled_time": future_time.isoformat(),
    }, headers=patient_headers)

    assert resp.status_code == 201
    data = resp.json()
    assert data["patient_id"] == patient.id
    assert data["doctor_id"] == doctor.id
    assert data["status"] == "scheduled"
    assert data["queue_position"] == 1


def test_create_appointment_past_time_rejected(client, doctor_user, patient_headers):
    _, doctor = doctor_user
    past = (datetime.utcnow() - timedelta(hours=1)).isoformat()

    resp = client.post(f"{APPTS}/", json={
        "doctor_id": doctor.id,
        "scheduled_time": past,
    }, headers=patient_headers)

    assert resp.status_code == 422


def test_create_appointment_doctor_role_forbidden(client, doctor_user, doctor_headers, future_time):
    _, doctor = doctor_user

    resp = client.post(f"{APPTS}/", json={
        "doctor_id": doctor.id,
        "scheduled_time": future_time.isoformat(),
    }, headers=doctor_headers)

    assert resp.status_code == 403


def test_create_appointment_creates_audit_entry(client, patient_user, doctor_user, patient_headers, future_time, db):
    from app.models.audit_chain import AuditChain
    _, doctor = doctor_user

    resp = client.post(f"{APPTS}/", json={
        "doctor_id": doctor.id,
        "scheduled_time": future_time.isoformat(),
    }, headers=patient_headers)
    assert resp.status_code == 201

    appt_id = resp.json()["id"]
    entry = db.query(AuditChain).filter(
        AuditChain.record_id == appt_id,
        AuditChain.record_type == "appointment_created",
    ).first()
    assert entry is not None


def test_double_booking_rejected(client, patient_user, doctor_user, patient_headers, future_time):
    _, doctor = doctor_user

    client.post(f"{APPTS}/", json={
        "doctor_id": doctor.id,
        "scheduled_time": future_time.isoformat(),
    }, headers=patient_headers)

    resp = client.post(f"{APPTS}/", json={
        "doctor_id": doctor.id,
        "scheduled_time": future_time.isoformat(),
    }, headers=patient_headers)

    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# List appointments (role-based filtering)
# ---------------------------------------------------------------------------

def test_list_appointments_patient_sees_only_own(client, patient_user, doctor_user, patient_headers, db):
    _, patient = patient_user
    _, doctor = doctor_user
    _insert_appointment(db, patient.id, doctor.id)

    resp = client.get(f"{APPTS}/", headers=patient_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["patient_id"] == patient.id


def test_list_appointments_doctor_sees_only_own(client, patient_user, doctor_user, doctor_headers, db):
    _, patient = patient_user
    _, doctor = doctor_user
    _insert_appointment(db, patient.id, doctor.id)

    resp = client.get(f"{APPTS}/", headers=doctor_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert all(a["doctor_id"] == doctor.id for a in data)


def test_list_appointments_admin_sees_all(client, patient_user, doctor_user, admin_headers, db):
    _, patient = patient_user
    _, doctor = doctor_user
    _insert_appointment(db, patient.id, doctor.id)

    resp = client.get(f"{APPTS}/", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


# ---------------------------------------------------------------------------
# Cancellation
# ---------------------------------------------------------------------------

def test_cancel_appointment_success(client, patient_user, doctor_user, patient_headers, db):
    _, patient = patient_user
    _, doctor = doctor_user
    appt = _insert_appointment(db, patient.id, doctor.id, hours_ahead=24)

    resp = client.delete(f"{APPTS}/{appt.id}", headers=patient_headers)
    assert resp.status_code == 204


def test_cancel_within_2h_window_rejected(client, patient_user, doctor_user, patient_headers, db):
    _, patient = patient_user
    _, doctor = doctor_user
    appt = _insert_appointment(db, patient.id, doctor.id, hours_ahead=1)

    resp = client.delete(f"{APPTS}/{appt.id}", headers=patient_headers)
    assert resp.status_code == 400
    assert "2 hour" in resp.json()["detail"].lower() or "2-hour" in resp.json()["detail"].lower()


def test_cancel_already_cancelled_rejected(client, patient_user, doctor_user, patient_headers, db):
    _, patient = patient_user
    _, doctor = doctor_user
    appt = _insert_appointment(db, patient.id, doctor.id, status=AppointmentStatus.CANCELLED)

    resp = client.delete(f"{APPTS}/{appt.id}", headers=patient_headers)
    assert resp.status_code == 400


def test_patient_cannot_cancel_others_appointment(client, patient_user, doctor_user, db):
    from app.models.user import User, UserRole
    from app.models.patient import Patient
    from app.core.security import get_password_hash, create_access_token

    _, patient = patient_user
    _, doctor = doctor_user
    appt = _insert_appointment(db, patient.id, doctor.id, hours_ahead=48)

    # Create a second patient
    user2 = User(
        name="Other Patient",
        email="other@test.com",
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

    resp = client.delete(f"{APPTS}/{appt.id}", headers=headers)
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# General update endpoint (PUT /{id})
# ---------------------------------------------------------------------------

def test_update_appointment_reschedule(client, patient_user, doctor_user, patient_headers, db, future_time):
    _, patient = patient_user
    _, doctor = doctor_user
    appt = _insert_appointment(db, patient.id, doctor.id)

    new_time = future_time + timedelta(hours=2)
    resp = client.put(f"{APPTS}/{appt.id}", json={
        "scheduled_time": new_time.isoformat(),
    }, headers=patient_headers)

    assert resp.status_code == 200
    assert "scheduled_time" in resp.json()


def test_update_appointment_empty_body_rejected(client, patient_user, doctor_user, patient_headers, db):
    _, patient = patient_user
    _, doctor = doctor_user
    appt = _insert_appointment(db, patient.id, doctor.id)

    resp = client.put(f"{APPTS}/{appt.id}", json={}, headers=patient_headers)
    assert resp.status_code == 400


def test_update_appointment_both_fields_rejected(client, patient_user, doctor_user, patient_headers, db, future_time):
    _, patient = patient_user
    _, doctor = doctor_user
    appt = _insert_appointment(db, patient.id, doctor.id)

    resp = client.put(f"{APPTS}/{appt.id}", json={
        "scheduled_time": future_time.isoformat(),
        "status": "checked_in",
    }, headers=patient_headers)
    assert resp.status_code == 400


def test_patient_cannot_update_status_via_put(client, patient_user, doctor_user, patient_headers, db):
    _, patient = patient_user
    _, doctor = doctor_user
    appt = _insert_appointment(db, patient.id, doctor.id)

    resp = client.put(f"{APPTS}/{appt.id}", json={"status": "checked_in"}, headers=patient_headers)
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Status update (PATCH /{id}/status)
# ---------------------------------------------------------------------------

def test_status_update_checked_in_by_doctor(client, patient_user, doctor_user, doctor_headers, db):
    _, patient = patient_user
    _, doctor = doctor_user
    appt = _insert_appointment(db, patient.id, doctor.id)

    resp = client.patch(f"{APPTS}/{appt.id}/status", json={"status": "checked_in"}, headers=doctor_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "checked_in"


def test_status_update_patient_forbidden(client, patient_user, doctor_user, patient_headers, db):
    _, patient = patient_user
    _, doctor = doctor_user
    appt = _insert_appointment(db, patient.id, doctor.id)

    resp = client.patch(f"{APPTS}/{appt.id}/status", json={"status": "checked_in"}, headers=patient_headers)
    assert resp.status_code == 403


def test_status_update_invalid_status_rejected(client, patient_user, doctor_user, doctor_headers, db):
    _, patient = patient_user
    _, doctor = doctor_user
    appt = _insert_appointment(db, patient.id, doctor.id)

    # "cancelled" is not a valid transition via status-update endpoint
    resp = client.patch(f"{APPTS}/{appt.id}/status", json={"status": "cancelled"}, headers=doctor_headers)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Walk-in registration
# ---------------------------------------------------------------------------

def test_walk_in_registration_by_nurse(client, doctor_user, nurse_headers):
    _, doctor = doctor_user

    resp = client.post(f"{APPTS}/walk-in", json={
        "doctor_id": doctor.id,
        "patient_name": "Walk In Patient",
        "patient_email": "walkin@test.com",
        "patient_phone": "9876543210",
    }, headers=nurse_headers)

    assert resp.status_code == 201
    data = resp.json()
    assert data["appointment_type"] == "walk_in"
    assert data["status"] == "scheduled"


def test_walk_in_registration_by_admin(client, doctor_user, admin_headers):
    _, doctor = doctor_user

    resp = client.post(f"{APPTS}/walk-in", json={
        "doctor_id": doctor.id,
        "patient_name": "Admin Walk In",
    }, headers=admin_headers)

    assert resp.status_code == 201


def test_walk_in_patient_forbidden(client, doctor_user, patient_headers):
    _, doctor = doctor_user

    resp = client.post(f"{APPTS}/walk-in", json={
        "doctor_id": doctor.id,
        "patient_name": "Unauthorized",
    }, headers=patient_headers)

    assert resp.status_code == 403


def test_walk_in_doctor_forbidden(client, doctor_user, doctor_headers):
    _, doctor = doctor_user

    resp = client.post(f"{APPTS}/walk-in", json={
        "doctor_id": doctor.id,
        "patient_name": "Unauthorized",
    }, headers=doctor_headers)

    assert resp.status_code == 403
