"""
Pytest configuration and shared fixtures for HealthSaathi test suite.

Sets environment variables BEFORE importing any app module, then wires up
an in-memory SQLite database via StaticPool so every test runs in isolation.
"""
import os

# --- MUST be set before any app module is imported ---
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-unit-tests-only-32chars"
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("ALLOWED_ORIGINS", "*")

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# App imports (after env vars are set)
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.core.security import get_password_hash, create_access_token
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.appointment import Appointment, AppointmentStatus, AppointmentType
from app.models.medical_record import MedicalRecord
from app.models.audit_chain import AuditChain

# ---------------------------------------------------------------------------
# Test database engine — StaticPool keeps a single connection so all sessions
# share the same in-memory SQLite database.
# ---------------------------------------------------------------------------
_SQLITE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    _SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)

# Create schema once at module load
Base.metadata.create_all(bind=test_engine)


# ---------------------------------------------------------------------------
# Override get_db to use the test engine for every HTTP request
# ---------------------------------------------------------------------------
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# ---------------------------------------------------------------------------
# Session-scoped HTTP test client (lifespan runs once per test session)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Function-scoped DB session for direct fixture data setup
# ---------------------------------------------------------------------------
@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Auto-clean all tables after every test
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def clear_db():
    yield
    session = TestingSessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
    finally:
        session.close()


# ---------------------------------------------------------------------------
# User / profile fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def patient_user(db):
    user = User(
        name="Test Patient",
        email="patient@test.com",
        password_hash=get_password_hash("TestPass123"),
        role=UserRole.PATIENT,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    patient = Patient(user_id=user.id)
    db.add(patient)
    db.commit()
    db.refresh(patient)

    return user, patient


@pytest.fixture
def doctor_user(db):
    user = User(
        name="Test Doctor",
        email="doctor@test.com",
        password_hash=get_password_hash("TestPass123"),
        role=UserRole.DOCTOR,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    doctor = Doctor(
        user_id=user.id,
        specialization="General Medicine",
        license_number="DOC001",
        average_consultation_duration=15,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)

    return user, doctor


@pytest.fixture
def admin_user(db):
    user = User(
        name="Test Admin",
        email="admin@test.com",
        password_hash=get_password_hash("TestPass123"),
        role=UserRole.ADMIN,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def nurse_user(db):
    user = User(
        name="Test Nurse",
        email="nurse@test.com",
        password_hash=get_password_hash("TestPass123"),
        role=UserRole.NURSE,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Auth header helpers
# ---------------------------------------------------------------------------
def _make_headers(user: User) -> dict:
    token = create_access_token(
        data={"user_id": user.id, "email": user.email, "role": user.role.value}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def patient_headers(patient_user):
    user, _ = patient_user
    return _make_headers(user)


@pytest.fixture
def doctor_headers(doctor_user):
    user, _ = doctor_user
    return _make_headers(user)


@pytest.fixture
def admin_headers(admin_user):
    return _make_headers(admin_user)


@pytest.fixture
def nurse_headers(nurse_user):
    return _make_headers(nurse_user)


# ---------------------------------------------------------------------------
# Convenience time fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def future_time():
    return datetime.utcnow() + timedelta(hours=24)
