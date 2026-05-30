# Database Setup Guide

Complete guide for database setup and schema management.

## Quick Start

**From the `backend/` directory:**

```bash
cd backend

# Step 1: Create database and apply schema
python setup_tables.py

# Step 2: Load test data (optional)
python load_test_data.py
```

## Setup Scripts

### setup_tables.py

Creates all required database tables from the schema file.

**Location:** `backend/setup_tables.py`

**Usage:**
```bash
cd backend
python setup_tables.py
```

**What it does:**
- Connects to your configured database (Neon or local PostgreSQL)
- Reads `database/schema.sql`
- Executes all DDL statements to create tables
- Verifies table creation

**Output:**
```
✅ Found 7 tables:
   ✅ users
   ✅ patients
   ✅ doctors
   ✅ appointments
   ✅ medical_records
   ✅ audit_chain
   ✅ anomaly_alerts
✅ All required tables exist!
```

### load_test_data.py

Loads sample test data into the database.

**Location:** `backend/load_test_data.py`

**Usage:**
```bash
cd backend
python load_test_data.py
```

**What it does:**
- Reads `database/sample_data.sql`
- Inserts test users, patients, doctors, appointments, and medical records
- Displays record counts

**Output:**
```
✅ Test data loaded successfully!

📊 Data Summary:
  Users: 10
  Patients: 4
  Doctors: 3
  Appointments: 8
  Medical Records: 3
```

## Database Schema

## Database Schema

### Tables Overview

| Table | Purpose | Key Fields |
|-------|---------|------------|
| **users** | Authentication & RBAC | email, password_hash, role, created_at |
| **patients** | Patient demographics | user_id, date_of_birth, phone, blood_group |
| **doctors** | Doctor info & metrics | user_id, specialization, avg_consultation_duration |
| **appointments** | Scheduling & queue | patient_id, doctor_id, status, queue_position |
| **medical_records** | Clinical data & versioning | patient_id, diagnosis, prescription, version_number |
| **audit_chain** | Blockchain integrity | record_id, hash, previous_hash, is_tampered |
| **anomaly_alerts** | ML behavioural anomaly detection | user_id, anomaly_score, severity, top_features, is_acknowledged |

### Key Features

**Role-Based Access Control**
- Admin (system administration)
- Doctor (medical records, appointments)
- Nurse (walk-in registration, queue)
- Patient (booking, medical history)

**Queue Management**
- Real-time queue position calculation
- Appointment status workflow (scheduled → checked_in → in_progress → completed)
- Average consultation duration tracking for wait time estimation

**Medical Records Versioning**
- Complete audit trail
- Parent-child relationship for tracking changes
- Immutable history of modifications

**Blockchain Integrity**
- SHA-256 hash chain for tamper detection
- Previous hash verification
- Tampering alert system
- Comprehensive audit logs

**Behavioural Anomaly Detection**
- `anomaly_alerts` table stores ML-generated anomaly scores per user action
- `severity` column: `LOW` / `MEDIUM` / `HIGH` (CHECK constraint)
- `top_features` (JSONB) stores SHAP-attributed feature contributions for explainability
- `audit_entry_id` FK links each alert to the triggering audit chain block (nullable, SET NULL on delete)
- `is_acknowledged`, `acknowledged_by`, `acknowledged_at` support admin triage workflow
- Alembic migration: `alembic/versions/003_add_anomaly_alerts_table.py`

## Common Database Queries

### Authentication

```sql
-- Find user by email
SELECT * FROM users WHERE email = 'user@example.com';

-- Get user with role
SELECT id, name, email, role FROM users 
WHERE email = 'user@example.com' AND role = 'Doctor';
```

### Queue Management

```sql
-- Get current queue for a doctor
SELECT a.*, p.name as patient_name
FROM appointments a
JOIN patients p ON a.patient_id = p.id
WHERE a.doctor_id = ? 
  AND a.status IN ('checked_in', 'in_progress')
ORDER BY a.queue_position;

-- Calculate estimated wait time
SELECT 
    a.queue_position,
    d.average_consultation_duration,
    (a.queue_position * d.average_consultation_duration) as estimated_wait_minutes
FROM appointments a
JOIN doctors d ON a.doctor_id = d.id
WHERE a.id = ?;
```

### Medical Records

```sql
-- Get patient's complete history
SELECT mr.*, d.specialization, u.name as doctor_name
FROM medical_records mr
JOIN doctors d ON mr.doctor_id = d.id
JOIN users u ON d.user_id = u.id
WHERE mr.patient_id = ?
ORDER BY mr.created_at DESC;

-- Get record version history
SELECT id, version_number, created_at, updated_at
FROM medical_records
WHERE parent_record_id = ? OR id = ?
ORDER BY version_number;
```

### Audit Trail

```sql
-- Get audit logs for record
SELECT * FROM audit_chain
WHERE record_id = ?
ORDER BY timestamp DESC;

-- Find tampered records
SELECT * FROM audit_chain
WHERE is_tampered = TRUE
ORDER BY timestamp DESC;

-- Verify hash chain integrity
SELECT 
    id, hash, previous_hash,
    LAG(hash) OVER (ORDER BY id) as expected_previous_hash,
    CASE WHEN LAG(hash) OVER (ORDER BY id) != previous_hash THEN TRUE ELSE FALSE END as integrity_check
FROM audit_chain
ORDER BY id;
```

## Troubleshooting

**Connection Error: "failed: fe_sendauth: no password supplied"**
- Check DATABASE_URL in .env file
- Ensure password is correct if using local PostgreSQL
- For Neon: Use the full connection string with credentials

**"No tables found" after setup_tables.py**
- Check that database connection is working: `python setup_tables.py` will verify
- Check .env DATABASE_URL is correct
- For local PostgreSQL: Ensure server is running

**"Relation does not exist" when running queries**
- Run `python setup_tables.py` from backend directory
- Verify all 7 tables exist

**Foreign key constraint violation**
- Ensure parent records exist before inserting child records
- Check cascade settings in schema

**Test data not loading (load_test_data.py)**
- Ensure setup_tables.py ran successfully first
- Check database has write permissions
- Verify sample_data.sql file exists

---
