# HealthSaathi API Documentation

Complete API reference for the HealthSaathi FastAPI backend.

## Overview

**Base URL:** `http://localhost:8000/api/v1`
**Content-Type:** `application/json`

All protected endpoints require a valid JWT access token in the Authorization header:

```
Authorization: Bearer <access_token>
```

## Authentication Flow

1. **Register** a new account — `POST /auth/register` — returns user info only (no token)
2. **Login** with credentials — `POST /auth/login` — returns access + refresh tokens
3. Include the access token in `Authorization: Bearer` for all protected requests
4. When the access token expires, exchange the refresh token — `POST /auth/refresh`

### Token Details

| Token | Lifetime | Payload fields |
|-------|----------|----------------|
| Access | 60 minutes | `user_id`, `email`, `role`, `exp`, `type: "access"` |
| Refresh | 7 days | `user_id`, `exp`, `type: "refresh"` |

Algorithm: HS256 (configurable via `ALGORITHM` env var)

### Important: Register does not return a token

`POST /auth/register` returns a `UserResponse` (id, name, email, role, created_at).
Call `POST /auth/login` immediately after registration to obtain tokens.

## Common Error Codes

| Status | Meaning |
|--------|---------|
| 400 | Bad request — invalid data, duplicate resource, or conflicting update |
| 401 | Unauthenticated — missing, invalid, or expired token |
| 403 | Forbidden — authenticated but lacking required role |
| 404 | Resource not found |
| 409 | Conflict — e.g., double-booking a doctor's time slot |
| 413 | Request entity too large — body exceeds 10 MB |
| 422 | Validation error — e.g., past appointment time, missing required field |
| 500 | Unhandled server error (includes `request_id` for log correlation) |

### Standard Error Body

```json
{ "detail": "Human-readable error message" }
```

Unhandled 500 errors also include `request_id`:

```json
{ "detail": "Internal server error", "request_id": "550e8400-e29b-..." }
```

## Request Tracing

Every response includes an `X-Request-ID` header (UUID). Pass the same header on requests
to propagate your own trace ID. Use the value to correlate errors in server logs.

---

## Public Endpoints

### POST `/auth/register`

Register a new user account.

**Request:**
```json
{
  "name": "Dr. John Smith",
  "email": "john@example.com",
  "password": "SecurePass123",
  "role": "Doctor"
}
```

Roles: `Admin`, `Doctor`, `Nurse`, `Patient`
Password: minimum 8 characters, must include uppercase, lowercase, and digit.

**Response 201:**
```json
{
  "id": 1,
  "name": "Dr. John Smith",
  "email": "john@example.com",
  "role": "Doctor",
  "created_at": "2024-01-15T10:30:00"
}
```

### POST `/auth/login`

**Request:**
```json
{ "email": "john@example.com", "password": "SecurePass123" }
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": 1, "name": "Dr. John Smith", "email": "john@example.com", "role": "Doctor" }
}
```

### POST `/auth/refresh`

**Request:**
```json
{ "refresh_token": "eyJ..." }
```

**Response 200:**
```json
{ "access_token": "eyJ...", "refresh_token": "eyJ...", "token_type": "bearer" }
```

Only refresh tokens are accepted — passing an access token returns 401.

---

## Health Endpoints (no authentication)

### GET `/health`

Liveness probe. Always returns 200 while the process is alive.

```json
{ "status": "healthy", "version": "1.0.0", "database": "connected" }
```

### GET `/ready`

Readiness probe. Returns 503 when the database is unavailable.

```json
{ "status": "ready", "version": "1.0.0" }
```

503 body:
```json
{ "status": "not ready", "reason": "database unavailable" }
```

---

## Role-Based Access Control

| Role | Abbreviation in docs | Permissions summary |
|------|---------------------|---------------------|
| Admin | [A] | Full access including audit logs, user management |
| Doctor | [D] | Create/update medical records, manage own appointments |
| Nurse | [N] | Register walk-in patients, view queue |
| Patient | [P] | Book appointments, view own records |

**Staff** = Admin + Doctor + Nurse.

---

## User Endpoints

### GET `/users/me` — Any authenticated user

Returns the current user's profile.

### GET `/users` — [A] Admin only

Returns all users.

### GET `/users/doctors` — Any authenticated user

Returns all registered doctor profiles. Used by patients when booking appointments.

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 5,
    "name": "Dr. Rajesh Kumar",
    "specialization": "Cardiology",
    "license_number": "MCI-12345",
    "average_consultation_duration": 15
  }
]
```

---

## Appointment Endpoints

### GET `/appointments` — Any authenticated user

Returns appointments filtered by role:

| Caller role | What they see |
|------------|---------------|
| Patient | Their own appointments only |
| Doctor | Appointments assigned to them |
| Nurse / Admin | All appointments |

### POST `/appointments/` — [P] Patient only

Book a new appointment.

**Request:**
```json
{
  "doctor_id": 1,
  "scheduled_time": "2024-06-15T10:00:00",
  "appointment_type": "regular"
}
```

`scheduled_time` must be in the future (422 if not).
Returns 409 if the doctor is already booked at that time.

**Response 201:** `AppointmentWithDetails` object.

### PUT `/appointments/{id}` — Any authenticated user (ownership checked)

Update either the scheduled time or the status — provide exactly one field.

**Request — reschedule (Patient, Doctor, Nurse, Admin):**
```json
{ "scheduled_time": "2024-06-20T14:00:00" }
```

Patient can only reschedule their own appointment.
Staff can reschedule any appointment.

**Request — status update (Doctor, Nurse, Admin only; Patient → 403):**
```json
{ "status": "checked_in" }
```

Providing both fields returns 400. Providing neither returns 400.

Status workflow: `scheduled` → `checked_in` → `in_progress` → `completed` / `cancelled`

**Response 200:** `AppointmentWithDetails`

### DELETE `/appointments/{id}` — Any authenticated user (ownership checked)

Cancel an appointment.

- Patient can cancel their own appointment if > 2 hours remain.
- Staff can cancel any appointment.
- Returns 400 if already cancelled or within the 2-hour window.

### POST `/appointments/walk-in` — [N][D][A] Staff only

Register a walk-in patient. Creates a new Patient user if no matching record exists.

**Request:**
```json
{
  "patient_name": "Jane Doe",
  "doctor_id": 1,
  "appointment_type": "walk_in",
  "scheduled_time": "2024-06-15T10:30:00"
}
```

---

## Queue Endpoints

### GET `/queue/status` — Any authenticated user

Queue status across all doctors.

### GET `/queue/doctor/{doctor_id}` — Any authenticated user

Queue for a specific doctor (ordered by queue position).

---

## Medical Record Endpoints

### POST `/medical-records/` — [D] Doctor only

Create a medical record for a completed appointment.

**Request:**
```json
{
  "appointment_id": 42,
  "consultation_notes": "Patient reports persistent headache...",
  "diagnosis": "Tension headache",
  "prescription": "Ibuprofen 400mg as needed"
}
```

- The appointment must belong to the requesting doctor.
- One record per appointment — returns 400 if a record already exists.
- Creates an audit chain entry automatically.

**Response 201:** `ConsultationNoteResponse`

### POST `/medical-records/consultation-notes` — [D] Doctor only

Alternative endpoint for creating consultation notes (same validation as above).

### GET `/medical-records/patient/{patient_id}` — [P][D][A]

Access control:

| Caller | Condition |
|--------|-----------|
| Patient | Can only read their own records |
| Doctor | Can only read records of patients they have treated |
| Admin | Can read any patient's records |
| Nurse | 403 |

### PUT `/medical-records/{id}` — [D] Doctor only (creator only)

Update an existing medical record. Creates a new version — prior versions are retained.

### GET `/medical-records/{id}/versions` — Same access rules as GET by patient

Fetch the full version history of a record.

### GET `/medical-records/me` — [P] Patient only

Shortcut to retrieve the current patient's own records.

---

## Audit Endpoints — [A] Admin only

### GET `/audit/logs`

Paginated audit log with optional filters:

| Query param | Description |
|-------------|-------------|
| `record_type` | Filter by entity type (e.g., `appointment_created`, `medical_record`) |
| `start_date` | ISO date string |
| `end_date` | ISO date string |
| `page` | Page number (default 1) |
| `page_size` | Items per page (default 20, max 100) |

### GET `/audit/tampering-alerts`

Returns all audit chain entries where `is_tampered = true`.

### POST `/audit/verify/{record_id}`

Verify the integrity of a single audit chain entry.

**Response 200 — valid:**
```json
{ "is_valid": true, "record_id": 42, "message": "Record integrity verified" }
```

**Response 200 — tampered:**
```json
{ "is_valid": false, "record_id": 42, "message": "Record integrity check failed" }
```

The entry is automatically flagged (`is_tampered = true`) when tampering is detected.

**Response 404:** record not found.

### GET `/audit/chain-integrity`

Verify the entire audit chain from genesis block to current.

**Response 200:**
```json
{
  "is_valid": true,
  "total_blocks": 157,
  "invalid_blocks": [],
  "message": "Chain integrity verified"
}
```

### GET `/audit/export`

Export audit logs as JSON or CSV.

| Query param | Values |
|-------------|--------|
| `format` | `json` (default), `csv` |

---

## Anomaly Detection Endpoints — [A] Admin only

Powered by an IsolationForest model trained per user role (Doctor / Nurse / Patient / Admin) on the last 30 days of audit activity. Eight behavioural features are extracted from each audit event and scored; SHAP TreeExplainer provides top-3 feature attribution for every alert. Scoring runs as a background task after every medical record write or appointment mutation — safe to fail without affecting the primary request.

### GET `/anomaly/alerts`

Paginated list of anomaly alerts with optional filters.

| Query param | Description |
|-------------|-------------|
| `page` | Page number (default 1) |
| `page_size` | Items per page (default 20, max 100) |
| `severity` | Optional filter: `LOW`, `MEDIUM`, or `HIGH` |
| `is_acknowledged` | Optional filter: `true` or `false` |

**Response 200:**
```json
{
  "total": 42,
  "page": 1,
  "page_size": 20,
  "alerts": [
    {
      "id": 7,
      "user_id": 3,
      "anomaly_score": 0.81,
      "severity": "HIGH",
      "top_features": [
        { "feature": "off_hours_flag", "value": 1.0, "contribution": 0.42 },
        { "feature": "rapid_edit_flag", "value": 1.0, "contribution": 0.27 },
        { "feature": "unique_patients_accessed", "value": 14.0, "contribution": 0.18 }
      ],
      "explanation": "User accessed 14 distinct patients outside regular hours with rapid successive edits.",
      "audit_entry_id": 204,
      "is_acknowledged": false,
      "acknowledged_by": null,
      "acknowledged_at": null,
      "created_at": "2024-06-15T02:34:11"
    }
  ]
}
```

### GET `/anomaly/alerts/{id}`

Single anomaly alert by ID.

**Response 200:** same shape as a single alert object in the list above.

**Response 404:** alert not found.

### POST `/anomaly/alerts/{id}/acknowledge`

Mark an alert as acknowledged by the requesting admin. Sets `is_acknowledged = true`,
`acknowledged_by` to the admin's user ID, and `acknowledged_at` to the current UTC timestamp.

**Response 200:**
```json
{
  "id": 7,
  "is_acknowledged": true,
  "acknowledged_by": 1,
  "acknowledged_at": "2024-06-15T09:12:00"
}
```

**Response 404:** alert not found.

### GET `/anomaly/stats`

Summary statistics for the anomaly dashboard.

**Response 200:**
```json
{
  "total_alerts": 42,
  "high_severity": 5,
  "medium_severity": 13,
  "low_severity": 24,
  "unacknowledged": 18,
  "last_24h": 3
}
```

### WS `/anomaly/ws/admin`

Admin-only WebSocket that pushes real-time anomaly alerts. Only `MEDIUM` and `HIGH`
severity alerts are broadcast; `LOW` alerts are available via the REST endpoints only.

**Authentication:** Pass the access token as a query parameter:

```
ws://localhost:8000/api/v1/anomaly/ws/admin?token=eyJ...
```

If the token is missing, invalid, or belongs to a non-admin user, the server closes the
connection with code 1008 (Policy Violation).

**Messages received (JSON):**

```json
{
  "type": "anomaly_alert",
  "severity": "HIGH",
  "alert_id": 8,
  "user_id": 3,
  "anomaly_score": 0.81,
  "explanation": "User accessed 14 distinct patients outside regular hours with rapid successive edits.",
  "top_features": [
    { "feature": "off_hours_flag", "value": 1.0, "contribution": 0.42 },
    { "feature": "rapid_edit_flag", "value": 1.0, "contribution": 0.27 },
    { "feature": "unique_patients_accessed", "value": 14.0, "contribution": 0.18 }
  ],
  "timestamp": "2024-06-15T02:34:11"
}
```

#### Behavioural Features Scored

| Feature | Description |
|---------|-------------|
| `actions_per_hour` | Rate of audit-logged actions in the current session window |
| `unique_patients_accessed` | Distinct patient records touched in the window |
| `off_hours_flag` | 1 if action occurred outside 07:00–21:00 local time |
| `untreated_patient_ratio` | Fraction of accessed patients with no prior appointment with this user |
| `record_type_entropy` | Shannon entropy over `record_type` values — high entropy suggests unusual breadth |
| `rapid_edit_flag` | 1 if two or more edits to the same record occurred within 60 seconds |
| `cross_role_action_flag` | 1 if the action type is atypical for the user's assigned role |
| `session_duration_minutes` | Duration of the inferred session in minutes |

Severity thresholds (anomaly score 0–1): `< 0.60` → LOW · `< 0.75` → MEDIUM · `≥ 0.75` → HIGH.
Alerts are only persisted when the score exceeds 0.50.

---

## WebSocket Endpoint

### WS `/api/v1/ws/{doctor_id}`

Real-time queue updates for a specific doctor's queue.

**Authentication:** Pass the access token as a query parameter:

```
ws://localhost:8000/api/v1/ws/1?token=eyJ...
```

If the token is missing or invalid, the server closes the connection with code 1008 (Policy Violation).

**Messages received (JSON):**

```json
{
  "type": "queue_update",
  "doctor_id": 1,
  "queue": [
    { "position": 1, "patient_name": "...", "status": "in_progress" },
    { "position": 2, "patient_name": "...", "status": "checked_in" }
  ]
}
```

The server broadcasts to all connected clients for a doctor whenever an appointment
status changes or the queue position is updated.

---

## Audit Chain Architecture

All write operations that change patient data create an audit chain entry automatically:

| Trigger | `record_type` value |
|---------|---------------------|
| Medical record created/updated | `medical_record` |
| Appointment booked | `appointment_created` |
| Appointment cancelled | `appointment_cancelled` |
| Appointment rescheduled | `appointment_rescheduled` |
| Appointment status changed | `appointment_status_updated` |
| Walk-in registered | `walk_in_registered` |

Each entry stores:
- `record_id` — ID of the affected entity
- `record_type` — entity type (polymorphic)
- `record_data` — JSON snapshot of relevant fields at time of change
- `hash` — SHA-256 of `record_id + record_type + record_data + previous_hash`
- `previous_hash` — hash of the prior entry (genesis block uses `"0"`)
- `created_by` — user ID who triggered the action
- `is_tampered` — set to `true` by `/audit/verify/{id}` if hash mismatch detected

---

## RBAC Dependency Reference (for backend contributors)

```python
from app.core.dependencies import (
    get_current_user,   # Any authenticated user
    require_admin,      # Admin only
    require_doctor,     # Doctor only
    require_nurse,      # Nurse only
    require_patient,    # Patient only
    require_staff,      # Admin + Doctor + Nurse
)
```

---

For interactive testing, visit http://localhost:8000/api/docs
