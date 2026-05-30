"""
Tests for authentication endpoints: register, login, token refresh.
"""
import pytest

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def test_register_success(client):
    resp = client.post(REGISTER, json={
        "name": "New User",
        "email": "newuser@test.com",
        "password": "SecurePass1",
        "role": "Patient",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newuser@test.com"
    assert data["role"] == "Patient"
    assert "id" in data
    assert "password_hash" not in data


def test_register_all_roles(client):
    for role in ("Admin", "Doctor", "Nurse", "Patient"):
        resp = client.post(REGISTER, json={
            "name": f"User {role}",
            "email": f"user_{role.lower()}@test.com",
            "password": "SecurePass1",
            "role": role,
        })
        assert resp.status_code == 201, f"Registration failed for role {role}"
        assert resp.json()["role"] == role


def test_register_duplicate_email_returns_400(client):
    payload = {
        "name": "Duplicate",
        "email": "dup@test.com",
        "password": "SecurePass1",
        "role": "Patient",
    }
    client.post(REGISTER, json=payload)
    resp = client.post(REGISTER, json=payload)
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


def test_register_weak_password_no_uppercase(client):
    resp = client.post(REGISTER, json={
        "name": "User",
        "email": "weak1@test.com",
        "password": "password1",
        "role": "Patient",
    })
    assert resp.status_code == 422


def test_register_weak_password_no_digit(client):
    resp = client.post(REGISTER, json={
        "name": "User",
        "email": "weak2@test.com",
        "password": "Password",
        "role": "Patient",
    })
    assert resp.status_code == 422


def test_register_invalid_role(client):
    resp = client.post(REGISTER, json={
        "name": "User",
        "email": "badrole@test.com",
        "password": "SecurePass1",
        "role": "SuperAdmin",
    })
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def test_login_success(client, patient_user):
    user, _ = patient_user
    resp = client.post(LOGIN, json={"email": user.email, "password": "TestPass123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["id"] == user.id
    assert data["user"]["role"] == "Patient"


def test_login_wrong_password(client, patient_user):
    user, _ = patient_user
    resp = client.post(LOGIN, json={"email": user.email, "password": "WrongPass1"})
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post(LOGIN, json={"email": "nobody@test.com", "password": "SomePass1"})
    assert resp.status_code == 401


def test_login_returns_valid_bearer_token(client, patient_user):
    """Token returned by login must work as a bearer credential."""
    user, _ = patient_user
    login = client.post(LOGIN, json={"email": user.email, "password": "TestPass123"})
    token = login.json()["access_token"]

    resp = client.get("/api/v1/appointments/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Token refresh
# ---------------------------------------------------------------------------

def test_refresh_token_succeeds(client, patient_user):
    user, _ = patient_user
    login = client.post(LOGIN, json={"email": user.email, "password": "TestPass123"})
    refresh_token = login.json()["refresh_token"]

    resp = client.post(REFRESH, json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["id"] == user.id


def test_refresh_using_access_token_rejected(client, patient_headers):
    """Access tokens must not be accepted as refresh tokens."""
    access_token = patient_headers["Authorization"].split(" ")[1]
    resp = client.post(REFRESH, json={"refresh_token": access_token})
    assert resp.status_code == 401
    assert "type" in resp.json()["detail"].lower()


def test_refresh_with_garbage_token_rejected(client):
    resp = client.post(REFRESH, json={"refresh_token": "not.a.jwt.at.all"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Unauthenticated access
# ---------------------------------------------------------------------------

def test_protected_endpoint_requires_auth(client):
    resp = client.get("/api/v1/appointments/")
    # FastAPI / HTTPBearer returns 403 when no Authorization header is present
    assert resp.status_code in (401, 403)
