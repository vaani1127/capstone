# HealthSaathi Data Models

SQLAlchemy ORM models for the HealthSaathi healthcare management system.

## Models Overview

### User Model (`user.py`)
- **Table**: `users`
- **Purpose**: Authentication and role-based access control
- **Key Fields**: name, email, password_hash, role
- **Roles**: Admin, Doctor, Nurse, Patient
- **Relationships**: patient, doctor, medical_records_created, audit_entries

### Patient Model (`patient.py`)
- **Table**: `patients`
- **Purpose**: Patient demographic and contact information
- **Key Fields**: user_id, date_of_birth, gender, phone, address, blood_group
- **Relationships**: user, appointments, medical_records

### Doctor Model (`doctor.py`)
- **Table**: `doctors`
- **Purpose**: Doctor credentials and consultation metrics
- **Key Fields**: user_id, specialization, license_number, average_consultation_duration
- **Relationships**: user, appointments, medical_records

### Appointment Model (`appointment.py`)
- **Table**: `appointments`
- **Purpose**: Appointment scheduling and queue management
- **Key Fields**: patient_id, doctor_id, scheduled_time, status, appointment_type, queue_position
- **Statuses**: scheduled, checked_in, in_progress, completed, cancelled
- **Types**: scheduled, walk_in
- **Relationships**: patient, doctor, medical_records

### MedicalRecord Model (`medical_record.py`)
- **Table**: `medical_records`
- **Purpose**: Consultation notes, diagnoses, and prescriptions with versioning
- **Key Fields**: patient_id, doctor_id, appointment_id, consultation_notes, diagnosis, prescription, version_number, parent_record_id, created_by
- **Relationships**: patient, doctor, appointment, creator, parent_record, child_records

### AuditChain Model (`audit_chain.py`)
- **Table**: `audit_chain`
- **Purpose**: Blockchain-inspired audit trail for tamper detection
- **Key Fields**: record_id, record_type, record_data, hash, previous_hash, timestamp, user_id, is_tampered
- **Relationships**: user

## Usage

```python
from app.models import User, Patient, Doctor, Appointment, MedicalRecord, AuditChain
from app.models.user import UserRole
from app.models.appointment import AppointmentStatus, AppointmentType

# Create a new user
user = User(
    name="Dr. John Smith",
    email="john.smith@hospital.com",
    password_hash="hashed_password",
    role=UserRole.DOCTOR
)

# Create a doctor profile
doctor = Doctor(
    user_id=user.id,
    specialization="Cardiology",
    license_number="LIC123456",
    average_consultation_duration=20
)
```

## Database Schema Alignment

All models are designed to match the database schema defined in `database/schema.sql`:
- Column names and types match exactly
- Foreign key relationships are properly defined
- Indexes are inherited from the database schema
- Enums match CHECK constraints in the database

## Relationships

The models use SQLAlchemy relationships for easy navigation:
- `User` ↔ `Patient` (one-to-one)
- `User` ↔ `Doctor` (one-to-one)
- `Patient` ↔ `Appointment` (one-to-many)
- `Doctor` ↔ `Appointment` (one-to-many)
- `Appointment` ↔ `MedicalRecord` (one-to-many)
- `MedicalRecord` ↔ `MedicalRecord` (parent-child for versioning)
- `User` ↔ `AuditChain` (one-to-many)

## Notes

- All models inherit from `Base` which provides `id`, `created_at`, and `updated_at` fields
- Enums are defined as Python Enum classes for type safety
- Cascade delete is configured where appropriate
- All models include proper `__repr__` methods for debugging
