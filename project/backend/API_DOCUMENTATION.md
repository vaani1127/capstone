# HealthSaathi API Documentation

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Common Error Codes](#common-error-codes)
4. [Authentication Endpoints](#authentication-endpoints)
5. [User Management Endpoints](#user-management-endpoints)
6. [Appointment Endpoints](#appointment-endpoints)
7. [Queue Management Endpoints](#queue-management-endpoints)
8. [Medical Records Endpoints](#medical-records-endpoints)
9. [Audit Endpoints](#audit-endpoints)
10. [WebSocket Endpoints](#websocket-endpoints)

---

## Overview

**Base URL:** `http://localhost:8000/api/v1`

**API Version:** v1

**Content Type:** `application/json`

All API endpoints (except authentication) require a valid JWT access token in the Authorization header.

---

## Authentication

### Authentication Flow

1. **Register** a new user account
2. **Login** with credentials to receive access and refresh tokens
3. Include the **access token** in the `Authorization` header for all protected endpoints:
   ```
   Authorization: Bearer <access_token>
   ```
4. When the access token expires, use the **refresh token** to obtain a new access token

### Token Details

- **Access Token:** Valid for 30 minutes (configurable)
- **Refresh Token:** Valid for 7 days (configurable)
- **Algorithm:** HS256
- **Token Type:** Bearer

### Token Payload Structure

```json
{
  "user_id": 123,
  "email": "user@example.com",
  "role": "Doctor",
  "exp": 1234567890,
  "type": "access"
}
```

---

## Common Error Codes


| Status Code | Error Type | Description |
|-------------|------------|-------------|
| 400 | Bad Request | Invalid request data or validation error |
| 401 | Unauthorized | Missing, invalid, or expired authentication token |
| 403 | Forbidden | User lacks required permissions for the resource |
| 404 | Not Found | Requested resource does not exist |
| 409 | Conflict | Resource conflict (e.g., double-booking, duplicate email) |
| 500 | Internal Server Error | Unexpected server error |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Authentication Endpoints

### 1. Register User

**Endpoint:** `POST /auth/register`

**Description:** Register a new user account with role assignment.

**Authentication:** None required

**Request Body:**

```json
{
  "name": "Dr. John Smith",
  "email": "john.smith@example.com",
  "password": "SecurePass123",
  "role": "Doctor"
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | User's full name (1-255 characters) |
| email | string | Yes | Valid email address |
| password | string | Yes | Password (min 8 chars, must contain uppercase, lowercase, and digit) |
| role | string | Yes | User role: `Admin`, `Doctor`, `Nurse`, or `Patient` |

**Success Response (201 Created):**

```json
{
  "id": 1,
  "name": "Dr. John Smith",
  "email": "john.smith@example.com",
  "role": "Doctor",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**

- **400 Bad Request:** Email already registered or password validation failed
- **500 Internal Server Error:** Database error

---

### 2. Login

**Endpoint:** `POST /auth/login`

**Description:** Authenticate user and receive JWT tokens.

**Authentication:** None required

**Request Body:**

```json
{
  "email": "john.smith@example.com",
  "password": "SecurePass123"
}
```

**Success Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "Dr. John Smith",
    "email": "john.smith@example.com",
    "role": "Doctor",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

**Error Responses:**

- **401 Unauthorized:** Invalid email or password

---

### 3. Refresh Token

**Endpoint:** `POST /auth/refresh`

**Description:** Obtain a new access token using a refresh token.

**Authentication:** None required (refresh token in body)

**Request Body:**

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "Dr. John Smith",
    "email": "john.smith@example.com",
    "role": "Doctor",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

**Error Responses:**

- **401 Unauthorized:** Invalid or expired refresh token

---

## User Management Endpoints

### 1. Get Current User

**Endpoint:** `GET /users/me`

**Description:** Get information about the currently authenticated user.

**Authentication:** Required (any role)

**Request Headers:**

```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**

```json
{
  "id": 1,
  "name": "Dr. John Smith",
  "email": "john.smith@example.com",
  "role": "Doctor",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid token

---

### 2. List All Users

**Endpoint:** `GET /users/`

**Description:** List all users in the system.

**Authentication:** Required (Admin only)

**Request Headers:**

```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**

```json
[
  {
    "id": 1,
    "name": "Dr. John Smith",
    "email": "john.smith@example.com",
    "role": "Doctor",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  {
    "id": 2,
    "name": "Jane Doe",
    "email": "jane.doe@example.com",
    "role": "Patient",
    "created_at": "2024-01-15T11:00:00Z",
    "updated_at": "2024-01-15T11:00:00Z"
  }
]
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid token
- **403 Forbidden:** User is not an Admin

---

## Appointment Endpoints


### 1. List Appointments

**Endpoint:** `GET /appointments/`

**Description:** List appointments with role-based filtering.

**Authentication:** Required (any role)

**Authorization:**
- **Patients:** See only their own appointments
- **Doctors:** See only appointments assigned to them
- **Nurses/Admins:** See all appointments (with optional filters)

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| patient_id | integer | No | Filter by patient ID (Admin/Nurse only) |
| doctor_id | integer | No | Filter by doctor ID (Admin/Nurse only) |
| status | string | No | Filter by status: `scheduled`, `checked_in`, `in_progress`, `completed`, `cancelled` |
| start_date | datetime | No | Filter by start date (ISO format) |
| end_date | datetime | No | Filter by end date (ISO format) |

**Example Request:**

```
GET /appointments/?status=scheduled&start_date=2024-01-15T00:00:00Z
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**

```json
[
  {
    "id": 1,
    "patient_id": 5,
    "doctor_id": 2,
    "scheduled_time": "2024-01-15T14:00:00Z",
    "status": "scheduled",
    "appointment_type": "scheduled",
    "queue_position": 3,
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z",
    "patient_name": "Jane Doe",
    "doctor_name": "Dr. John Smith",
    "doctor_specialization": "Cardiology",
    "estimated_wait_time": 45
  }
]
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid token
- **403 Forbidden:** Patient/Doctor trying to access other users' appointments
- **404 Not Found:** Patient/Doctor record not found for current user

---

### 2. Create Appointment

**Endpoint:** `POST /appointments/`

**Description:** Book a new appointment (Patient only).

**Authentication:** Required (Patient role)

**Request Body:**

```json
{
  "doctor_id": 2,
  "scheduled_time": "2024-01-15T14:00:00Z"
}
```

**Success Response (201 Created):**

```json
{
  "id": 1,
  "patient_id": 5,
  "doctor_id": 2,
  "scheduled_time": "2024-01-15T14:00:00Z",
  "status": "scheduled",
  "appointment_type": "scheduled",
  "queue_position": 3,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z",
  "patient_name": "Jane Doe",
  "doctor_name": "Dr. John Smith",
  "doctor_specialization": "Cardiology",
  "estimated_wait_time": 45
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid token
- **403 Forbidden:** User is not a Patient
- **404 Not Found:** Doctor or patient record not found
- **409 Conflict:** Doctor not available at requested time (double-booking prevented)

---

### 3. Reschedule Appointment

**Endpoint:** `PUT /appointments/{appointment_id}/reschedule`

**Description:** Reschedule an appointment to a new time.

**Authentication:** Required (any role)

**Authorization:** Patient must own the appointment, or user must be staff (Doctor/Nurse/Admin)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| appointment_id | integer | ID of the appointment to reschedule |

**Request Body:**

```json
{
  "new_scheduled_time": "2024-01-15T16:00:00Z"
}
```

**Success Response (200 OK):**

```json
{
  "id": 1,
  "patient_id": 5,
  "doctor_id": 2,
  "scheduled_time": "2024-01-15T16:00:00Z",
  "status": "scheduled",
  "appointment_type": "scheduled",
  "queue_position": 5,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T12:00:00Z",
  "patient_name": "Jane Doe",
  "doctor_name": "Dr. John Smith",
  "doctor_specialization": "Cardiology",
  "estimated_wait_time": 75
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid token
- **403 Forbidden:** User not authorized to reschedule this appointment
- **404 Not Found:** Appointment not found
- **400 Bad Request:** Appointment already cancelled or completed
- **409 Conflict:** Doctor not available at requested time

---

### 4. Cancel Appointment

**Endpoint:** `DELETE /appointments/{appointment_id}`

**Description:** Cancel an appointment (must be at least 2 hours before scheduled time).

**Authentication:** Required (any role)

**Authorization:** Patient must own the appointment, or user must be staff (Doctor/Nurse/Admin)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| appointment_id | integer | ID of the appointment to cancel |

**Success Response (204 No Content)**

**Error Responses:**

- **401 Unauthorized:** Missing or invalid token
- **403 Forbidden:** User not authorized to cancel this appointment
- **404 Not Found:** Appointment not found
- **400 Bad Request:** Appointment already cancelled or within 2-hour window

---

### 5. Update Appointment Status

**Endpoint:** `PATCH /appointments/{appointment_id}/status`

**Description:** Update appointment status (Doctor/Nurse/Admin only).

**Authentication:** Required (Doctor, Nurse, or Admin role)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| appointment_id | integer | ID of the appointment to update |

**Request Body:**

```json
{
  "status": "checked_in"
}
```

**Valid Status Transitions:**

- `scheduled` → `checked_in` (patient arrives)
- `checked_in` → `in_progress` (consultation starts)
- `in_progress` → `completed` (consultation ends)

**Success Response (200 OK):**

```json
{
  "id": 1,
  "patient_id": 5,
  "doctor_id": 2,
  "scheduled_time": "2024-01-15T14:00:00Z",
  "status": "checked_in",
  "appointment_type": "scheduled",
  "queue_position": 3,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T13:55:00Z",
  "patient_name": "Jane Doe",
  "doctor_name": "Dr. John Smith",
  "doctor_specialization": "Cardiology",
  "estimated_wait_time": 45
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid token
- **403 Forbidden:** User not authorized (not Doctor/Nurse/Admin)
- **404 Not Found:** Appointment not found
- **400 Bad Request:** Invalid status transition

---

### 6. Register Walk-In Patient

**Endpoint:** `POST /appointments/walk-in`

**Description:** Register a walk-in patient and create immediate appointment (Admin/Nurse only).

**Authentication:** Required (Admin or Nurse role)

**Request Body:**

```json
{
  "doctor_id": 2,
  "patient_name": "John Doe",
  "patient_email": "john.doe@example.com",
  "patient_phone": "+1234567890",
  "date_of_birth": "1990-05-15T00:00:00Z",
  "gender": "Male",
  "address": "123 Main St, City",
  "blood_group": "O+"
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| doctor_id | integer | Yes | ID of the doctor to assign |
| patient_name | string | Yes | Patient's full name |
| patient_email | string | No | Patient's email (used to check for existing patient) |
| patient_phone | string | No | Patient's phone number |
| date_of_birth | datetime | No | Patient's date of birth |
| gender | string | No | Patient's gender |
| address | string | No | Patient's address |
| blood_group | string | No | Patient's blood group |

**Success Response (201 Created):**

```json
{
  "id": 10,
  "patient_id": 15,
  "doctor_id": 2,
  "scheduled_time": "2024-01-15T13:45:00Z",
  "status": "checked_in",
  "appointment_type": "walk_in",
  "queue_position": 4,
  "created_at": "2024-01-15T13:45:00Z",
  "updated_at": "2024-01-15T13:45:00Z",
  "patient_name": "John Doe",
  "doctor_name": "Dr. John Smith",
  "doctor_specialization": "Cardiology",
  "estimated_wait_time": 60
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid token
- **403 Forbidden:** User not authorized (not Admin or Nurse)
- **404 Not Found:** Doctor not found

---

## Queue Management Endpoints


### 1. Get Queue Status for All Doctors

**Endpoint:** `GET /queue/status`

**Description:** Get real-time queue status for all doctors.

**Authentication:** Required (any role)

**Success Response (200 OK):**

```json
[
  {
    "doctor_id": 2,
    "doctor_name": "Dr. John Smith",
    "doctor_specialization": "Cardiology",
    "queue_length": 5,
    "average_wait_time": 75
  },
  {
    "doctor_id": 3,
    "doctor_name": "Dr. Sarah Johnson",
    "doctor_specialization": "Pediatrics",
    "queue_length": 3,
    "average_wait_time": 45
  }
]
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| doctor_id | integer | Doctor's ID |
| doctor_name | string | Doctor's full name |
| doctor_specialization | string | Doctor's specialization |
| queue_length | integer | Number of patients in queue |
| average_wait_time | integer | Average estimated wait time in minutes |

**Error Responses:**

- **401 Unauthorized:** Missing or invalid token

---

### 2. Get Queue for Specific Doctor

**Endpoint:** `GET /queue/doctor/{doctor_id}`

**Description:** Get detailed queue information for a specific doctor.

**Authentication:** Required (any role)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| doctor_id | integer | ID of the doctor |

**Success Response (200 OK):**

```json
{
  "doctor_id": 2,
  "doctor_name": "Dr. John Smith",
  "doctor_specialization": "Cardiology",
  "average_consultation_duration": 15,
  "total_queue_length": 5,
  "patients": [
    {
      "appointment_id": 1,
      "patient_id": 5,
      "patient_name": "Jane Doe",
      "queue_position": 1,
      "estimated_wait_time": 15,
      "status": "in_progress",
      "scheduled_time": "2024-01-15T14:00:00Z"
    },
    {
      "appointment_id": 2,
      "patient_id": 6,
      "patient_name": "John Smith",
      "queue_position": 2,
      "estimated_wait_time": 30,
      "status": "checked_in",
      "scheduled_time": "2024-01-15T14:15:00Z"
    }
  ]
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| doctor_id | integer | Doctor's ID |
| doctor_name | string | Doctor's full name |
| doctor_specialization | string | Doctor's specialization |
| average_consultation_duration | integer | Average consultation duration in minutes |
| total_queue_length | integer | Total number of patients in queue |
| patients | array | List of patients in queue with details |

**Error Responses:**

- **401 Unauthorized:** Missing or invalid token
- **404 Not Found:** Doctor not found

---

## Medical Records Endpoints

### 1. Get Patient Medical Records

**Endpoint:** `GET /medical-records/patient/{patient_id}`

**Description:** Get all medical records for a patient (latest versions only).

**Authentication:** Required (any role)

**Authorization:**
- **Patients:** Can view only their own records
- **Doctors:** Can view records of patients they have treated
- **Admins:** Can view all records
- **Nurses:** Cannot view medical records

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| patient_id | integer | ID of the patient |

**Success Response (200 OK):**

```json
[
  {
    "id": 1,
    "patient_id": 5,
    "patient_name": "Jane Doe",
    "doctor_id": 2,
    "doctor_name": "Dr. John Smith",
    "appointment_id": 1,
    "consultation_notes": "Patient presented with chest pain. ECG normal.",
    "diagnosis": "Anxiety-related chest pain",
    "prescription": "Medication: Alprazolam\nDosage: 0.25mg\nFrequency: Twice daily\nDuration: 2 weeks",
    "version_number": 1,
    "parent_record_id": null,
    "created_by": 2,
    "created_at": "2024-01-15T14:30:00Z",
    "is_tampered": false
  }
]
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Medical record ID |
| patient_id | integer | Patient's ID |
| patient_name | string | Patient's full name |
| doctor_id | integer | Doctor's ID |
| doctor_name | string | Doctor's full name |
| appointment_id | integer | Associated appointment ID |
| consultation_notes | string | Consultation notes |
| diagnosis | string | Medical diagnosis |
| prescription | string | Prescription details |
| version_number | integer | Version number of the record |
| parent_record_id | integer | ID of previous version (if updated) |
| created_by | integer | User ID who created this record |
| created_at | datetime | Creation timestamp |
| is_tampered | boolean | Whether tampering was detected |

**Error Responses:**

- **401 Unauthorized:** Missing or invalid token
- **403 Forbidden:** User not authorized to view these records
- **404 Not Found:** Patient not found

---

### 2. Create Consultation Note

**Endpoint:** `POST /medical-records/consultation-notes`

**Description:** Create a new consultation note (Doctor only).

**Authentication:** Required (Doctor role)

**Authorization:** Doctor must be assigned to the appointment

**Request Body:**

```json
{
  "appointment_id": 1,
  "consultation_notes": "Patient presented with chest pain. ECG normal. Vital signs stable.",
  "diagnosis": "Anxiety-related chest pain"
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| appointment_id | integer | Yes | ID of the appointment |
| consultation_notes | string | Yes | Consultation notes (min 1 character) |
| diagnosis | string | No | Medical diagnosis |

**Success Response (201 Created):**

```json
{
  "id": 1,
  "patient_id": 5,
  "doctor_id": 2,
  "appointment_id": 1,
  "consultation_notes": "Patient presented with chest pain. ECG normal. Vital signs stable.",
  "diagnosis": "Anxiety-related chest pain",
  "prescription": null,
  "version_number": 1,
  "parent_record_id": null,
  "created_by": 2,
  "created_at": "2024-01-15T14:30:00Z"
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid token
- **403 Forbidden:** User not a Doctor or not assigned to appointment
- **404 Not Found:** Appointment or doctor record not found
- **400 Bad Request:** Consultation note already exists for this appointment

---

### 3. Update Consultation Note

**Endpoint:** `PUT /medical-records/consultation-notes/{record_id}`

**Description:** Update a consultation note (creates new version, Doctor only).

**Authentication:** Required (Doctor role)

**Authorization:** Only the doctor who created the original record can update it

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| record_id | integer | ID of the medical record to update |

**Request Body:**

```json
{
  "consultation_notes": "Updated notes: Patient responded well to treatment.",
  "diagnosis": "Anxiety-related chest pain - resolved"
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| consultation_notes | string | No | Updated consultation notes |
| diagnosis | string | No | Updated diagnosis |
| prescription | string | No | Updated prescription |

**Note:** At least one field must be provided for update.

**Success Response (200 OK):**

```json
{
  "id": 2,
  "patient_id": 5,
  "doctor_id": 2,
  "appointment_id": 1,
  "consultation_notes": "Updated notes: Patient responded well to treatment.",
  "diagnosis": "Anxiety-related chest pain - resolved",
  "prescription": null,
  "version_number": 2,
  "parent_record_id": 1,
  "created_by": 2,
  "created_at": "2024-01-16T10:00:00Z"
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid token
- **403 Forbidden:** User not a Doctor or didn't create the original record
- **404 Not Found:** Medical record not found
- **400 Bad Request:** No fields provided for update

---

### 4. Create Prescription

**Endpoint:** `POST /medical-records/prescriptions`

**Description:** Create a new prescription (Doctor only).

**Authentication:** Required (Doctor role)

**Authorization:** Doctor must be assigned to the appointment

**Request Body:**

```json
{
  "appointment_id": 1,
  "medication": "Alprazolam",
  "dosage": "0.25mg",
  "frequency": "Twice daily",
  "duration": "2 weeks"
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| appointment_id | integer | Yes | ID of the appointment |
| medication | string | Yes | Medication name |
| dosage | string | Yes | Dosage information |
| frequency | string | Yes | Frequency of medication |
| duration | string | Yes | Duration of treatment |

**Success Response (201 Created):**

```json
{
  "id": 1,
  "patient_id": 5,
  "doctor_id": 2,
  "appointment_id": 1,
  "consultation_notes": null,
  "diagnosis": null,
  "prescription": "Medication: Alprazolam\nDosage: 0.25mg\nFrequency: Twice daily\nDuration: 2 weeks",
  "version_number": 1,
  "parent_record_id": null,
  "created_by": 2,
  "created_at": "2024-01-15T14:30:00Z"
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid token
- **403 Forbidden:** User not a Doctor or not assigned to appointment
- **404 Not Found:** Appointment or doctor record not found
- **400 Bad Request:** Medical record already exists for this appointment

---

### 5. Update Prescription

**Endpoint:** `PUT /medical-records/prescriptions/{record_id}`

**Description:** Update a prescription (creates new version, Doctor only).

**Authentication:** Required (Doctor role)

**Authorization:** Only the doctor who created the original record can update it

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| record_id | integer | ID of the medical record to update |

**Request Body:**

```json
{
  "medication": "Alprazolam",
  "dosage": "0.5mg",
  "frequency": "Once daily",
  "duration": "1 week"
}
```

**Success Response (200 OK):**

```json
{
  "id": 2,
  "patient_id": 5,
  "doctor_id": 2,
  "appointment_id": 1,
  "consultation_notes": null,
  "diagnosis": null,
  "prescription": "Medication: Alprazolam\nDosage: 0.5mg\nFrequency: Once daily\nDuration: 1 week",
  "version_number": 2,
  "parent_record_id": 1,
  "created_by": 2,
  "created_at": "2024-01-16T10:00:00Z"
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid token
- **403 Forbidden:** User not a Doctor or didn't create the original record
- **404 Not Found:** Medical record not found

---

### 6. Get Record Version History

**Endpoint:** `GET /medical-records/{record_id}/versions`

**Description:** Get all versions of a medical record.

**Authentication:** Required (any role)

**Authorization:** Same access rules as viewing records

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| record_id | integer | ID of any version of the medical record |

**Success Response (200 OK):**

```json
[
  {
    "id": 1,
    "patient_id": 5,
    "patient_name": "Jane Doe",
    "doctor_id": 2,
    "doctor_name": "Dr. John Smith",
    "appointment_id": 1,
    "consultation_notes": "Patient presented with chest pain.",
    "diagnosis": "Anxiety-related chest pain",
    "prescription": null,
    "version_number": 1,
    "parent_record_id": null,
    "created_by": 2,
    "created_by_name": "Dr. John Smith",
    "created_at": "2024-01-15T14:30:00Z",
    "is_tampered": false
  },
  {
    "id": 2,
    "patient_id": 5,
    "patient_name": "Jane Doe",
    "doctor_id": 2,
    "doctor_name": "Dr. John Smith",
    "appointment_id": 1,
    "consultation_notes": "Updated notes: Patient responded well to treatment.",
    "diagnosis": "Anxiety-related chest pain - resolved",
    "prescription": null,
    "version_number": 2,
    "parent_record_id": 1,
    "created_by": 2,
    "created_by_name": "Dr. John Smith",
    "created_at": "2024-01-16T10:00:00Z",
    "is_tampered": false
  }
]
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid token
- **403 Forbidden:** User not authorized to view these records
- **404 Not Found:** Medical record not found

---

## Audit Endpoints


### 1. Get Audit Logs

**Endpoint:** `GET /audit/logs`

**Description:** Get audit logs with optional filtering and pagination (Admin only).

**Authentication:** Required (Admin role)

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| start_date | datetime | No | Filter by start date (ISO format) |
| end_date | datetime | No | Filter by end date (ISO format) |
| user_id | integer | No | Filter by user ID |
| record_type | string | No | Filter by record type (e.g., `medical_record`, `appointment`) |
| page | integer | No | Page number (default: 1, min: 1) |
| page_size | integer | No | Items per page (default: 20, max: 100) |

**Example Request:**

```
GET /audit/logs?start_date=2024-01-01T00:00:00Z&record_type=medical_record&page=1&page_size=20
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**

```json
{
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8,
  "logs": [
    {
      "id": 1,
      "record_id": 1,
      "record_type": "medical_record",
      "record_data": {
        "patient_id": 5,
        "doctor_id": 2,
        "consultation_notes": "Patient presented with chest pain."
      },
      "hash": "a1b2c3d4e5f6...",
      "previous_hash": "0",
      "timestamp": "2024-01-15T14:30:00Z",
      "user_id": 2,
      "is_tampered": false,
      "user_name": "Dr. John Smith",
      "user_email": "john.smith@example.com"
    }
  ]
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| total | integer | Total number of audit logs matching filters |
| page | integer | Current page number |
| page_size | integer | Number of items per page |
| total_pages | integer | Total number of pages |
| logs | array | Array of audit log entries |

**Audit Log Entry Fields:**

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Audit entry ID |
| record_id | integer | ID of the record being audited |
| record_type | string | Type of record (e.g., `medical_record`) |
| record_data | object | Snapshot of record data at time of creation |
| hash | string | SHA-256 hash of the record |
| previous_hash | string | Hash of previous audit entry (blockchain link) |
| timestamp | datetime | When the audit entry was created |
| user_id | integer | ID of user who performed the action |
| is_tampered | boolean | Whether tampering was detected |
| user_name | string | Name of user who performed the action |
| user_email | string | Email of user who performed the action |

**Error Responses:**

- **401 Unauthorized:** Missing or invalid token
- **403 Forbidden:** User is not an Admin

---

### 2. Get Tampering Alerts

**Endpoint:** `GET /audit/tampering-alerts`

**Description:** Get all records flagged for tampering (Admin only).

**Authentication:** Required (Admin role)

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| sort_by | string | No | Sort order: `timestamp` (default) or `severity` |

**Success Response (200 OK):**

```json
[
  {
    "id": 15,
    "record_id": 5,
    "record_type": "medical_record",
    "hash": "a1b2c3d4e5f6...",
    "timestamp": "2024-01-15T14:30:00Z",
    "user_id": 2,
    "user_name": "Dr. John Smith",
    "user_email": "john.smith@example.com"
  }
]
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Audit entry ID |
| record_id | integer | ID of the tampered record |
| record_type | string | Type of record |
| hash | string | Stored hash value |
| timestamp | datetime | When tampering was detected |
| user_id | integer | ID of user associated with the record |
| user_name | string | Name of user |
| user_email | string | Email of user |

**Error Responses:**

- **401 Unauthorized:** Missing or invalid token
- **403 Forbidden:** User is not an Admin

---

### 3. Export Audit Logs

**Endpoint:** `GET /audit/export`

**Description:** Export audit logs in CSV or JSON format (Admin only).

**Authentication:** Required (Admin role)

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| format | string | No | Export format: `json` (default) or `csv` |
| start_date | datetime | No | Filter by start date (ISO format) |
| end_date | datetime | No | Filter by end date (ISO format) |
| user_id | integer | No | Filter by user ID |
| record_type | string | No | Filter by record type |

**Example Request:**

```
GET /audit/export?format=csv&start_date=2024-01-01T00:00:00Z
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**

**For JSON format:**
- Content-Type: `application/json`
- Content-Disposition: `attachment; filename=audit_logs_YYYYMMDD_HHMMSS.json`

```json
[
  {
    "id": 1,
    "record_id": 1,
    "record_type": "medical_record",
    "record_data": {...},
    "hash": "a1b2c3d4e5f6...",
    "previous_hash": "0",
    "timestamp": "2024-01-15T14:30:00Z",
    "user_id": 2,
    "is_tampered": false,
    "user_name": "Dr. John Smith",
    "user_email": "john.smith@example.com"
  }
]
```

**For CSV format:**
- Content-Type: `text/csv`
- Content-Disposition: `attachment; filename=audit_logs_YYYYMMDD_HHMMSS.csv`

```csv
id,record_id,record_type,record_data,hash,previous_hash,timestamp,user_id,user_name,user_email,is_tampered
1,1,medical_record,"{...}",a1b2c3d4e5f6...,0,2024-01-15T14:30:00Z,2,Dr. John Smith,john.smith@example.com,false
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid token
- **403 Forbidden:** User is not an Admin
- **400 Bad Request:** Invalid format parameter

---

## WebSocket Endpoints

### WebSocket Connection

**Endpoint:** `ws://localhost:8000/api/v1/ws`

**Description:** WebSocket endpoint for real-time communication.

**Authentication:** Required (JWT token as query parameter)

**Connection URL:**

```
ws://localhost:8000/api/v1/ws?token=<access_token>
```

**Authentication:**
- JWT access token must be provided as a query parameter
- Connection will be rejected if token is invalid or expired
- Close code 1008 (Policy Violation) returned on authentication failure

**Connection Lifecycle:**

1. Client connects with JWT token in query parameter
2. Server authenticates and accepts connection
3. Server sends welcome message
4. Connection added to pool by user_id
5. Server can broadcast real-time updates
6. Client can send messages (acknowledged by server)
7. Connection closed on disconnect or error

**Welcome Message (from server):**

```json
{
  "event": "connected",
  "data": {
    "message": "WebSocket connection established",
    "user_id": 1,
    "user_email": "john.smith@example.com"
  },
  "timestamp": null
}
```

**Message Format:**

All messages are JSON with the following structure:

```json
{
  "event": "event_type",
  "data": {...},
  "timestamp": "2024-01-15T14:30:00Z"
}
```

**Event Types:**

| Event | Direction | Description |
|-------|-----------|-------------|
| connected | Server → Client | Connection established successfully |
| queue_update | Server → Client | Queue status changed for a doctor |
| appointment_status | Server → Client | Appointment status changed |
| message_received | Server → Client | Acknowledgment of client message |

**Queue Update Event Example:**

```json
{
  "event": "queue_update",
  "data": {
    "doctor_id": 2,
    "queue_length": 5,
    "patients": [
      {
        "appointment_id": 1,
        "patient_name": "Jane Doe",
        "queue_position": 1,
        "estimated_wait_time": 15
      }
    ]
  },
  "timestamp": "2024-01-15T14:30:00Z"
}
```

**Appointment Status Event Example:**

```json
{
  "event": "appointment_status",
  "data": {
    "appointment_id": 1,
    "status": "in_progress",
    "patient_id": 5,
    "doctor_id": 2
  },
  "timestamp": "2024-01-15T14:30:00Z"
}
```

**Client Message Acknowledgment:**

When client sends a message, server responds with:

```json
{
  "event": "message_received",
  "data": {
    "message": "Message received",
    "received_data": "<client_message>"
  },
  "timestamp": null
}
```

**Error Handling:**

- **Authentication Failure:** Connection closed with code 1008
- **Connection Error:** Connection closed with code 1011 (Internal Error)
- **Normal Disconnect:** Connection closed gracefully

---

### WebSocket Status

**Endpoint:** `GET /ws/status`

**Description:** Get WebSocket server status and connection statistics.

**Authentication:** None required

**Success Response (200 OK):**

```json
{
  "status": "operational",
  "active_users": 15,
  "total_connections": 15,
  "connected_user_ids": [1, 2, 5, 7, 10, 12, 15, 18, 20, 22, 25, 28, 30, 32, 35]
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| status | string | Server status (`operational`) |
| active_users | integer | Number of unique users connected |
| total_connections | integer | Total number of active connections |
| connected_user_ids | array | List of user IDs currently connected |

---

## Appendix: Role-Based Access Control

### Role Permissions Summary

| Endpoint | Admin | Doctor | Nurse | Patient |
|----------|-------|--------|-------|---------|
| **Authentication** |
| POST /auth/register | ✓ | ✓ | ✓ | ✓ |
| POST /auth/login | ✓ | ✓ | ✓ | ✓ |
| POST /auth/refresh | ✓ | ✓ | ✓ | ✓ |
| **Users** |
| GET /users/me | ✓ | ✓ | ✓ | ✓ |
| GET /users/ | ✓ | ✗ | ✗ | ✗ |
| **Appointments** |
| GET /appointments/ | ✓ (all) | ✓ (own) | ✓ (all) | ✓ (own) |
| POST /appointments/ | ✗ | ✗ | ✗ | ✓ |
| PUT /appointments/{id}/reschedule | ✓ | ✓ | ✓ | ✓ (own) |
| DELETE /appointments/{id} | ✓ | ✓ | ✓ | ✓ (own) |
| PATCH /appointments/{id}/status | ✓ | ✓ | ✓ | ✗ |
| POST /appointments/walk-in | ✓ | ✗ | ✓ | ✗ |
| **Queue** |
| GET /queue/status | ✓ | ✓ | ✓ | ✓ |
| GET /queue/doctor/{id} | ✓ | ✓ | ✓ | ✓ |
| **Medical Records** |
| GET /medical-records/patient/{id} | ✓ (all) | ✓ (treated) | ✗ | ✓ (own) |
| POST /medical-records/consultation-notes | ✗ | ✓ | ✗ | ✗ |
| PUT /medical-records/consultation-notes/{id} | ✗ | ✓ (own) | ✗ | ✗ |
| POST /medical-records/prescriptions | ✗ | ✓ | ✗ | ✗ |
| PUT /medical-records/prescriptions/{id} | ✗ | ✓ (own) | ✗ | ✗ |
| GET /medical-records/{id}/versions | ✓ (all) | ✓ (treated) | ✗ | ✓ (own) |
| **Audit** |
| GET /audit/logs | ✓ | ✗ | ✗ | ✗ |
| GET /audit/tampering-alerts | ✓ | ✗ | ✗ | ✗ |
| GET /audit/export | ✓ | ✗ | ✗ | ✗ |
| **WebSocket** |
| WS /ws | ✓ | ✓ | ✓ | ✓ |
| GET /ws/status | ✓ | ✓ | ✓ | ✓ |

**Legend:**
- ✓ = Allowed
- ✗ = Forbidden
- (all) = Can access all records
- (own) = Can only access own records
- (treated) = Can only access records of patients they have treated

---

## Appendix: Blockchain Integrity

### How It Works

1. **Hash Generation:** When a medical record is created or updated, a SHA-256 hash is generated
2. **Hash Input:** `record_data + timestamp + user_id + previous_hash`
3. **Audit Chain:** Each hash entry links to the previous hash (blockchain structure)
4. **Genesis Block:** First entry has `previous_hash = "0"`
5. **Verification:** On record access, hash is recomputed and compared with stored hash
6. **Tamper Detection:** Hash mismatch triggers tampering alert and flags the record

### Integrity Verification Process

```
1. Fetch audit entry for record
2. Fetch actual record data from database
3. Recompute hash using: SHA-256(record_data + timestamp + user_id + previous_hash)
4. Compare recomputed hash with stored hash
5. If mismatch:
   - Log tampering alert
   - Flag audit entry as tampered (is_tampered = true)
   - Return tampering status to client
6. If match:
   - Record integrity verified
```

### Security Guarantees

- **Immutability:** Audit chain entries cannot be deleted or modified
- **Traceability:** All record modifications are logged with user and timestamp
- **Tamper Detection:** Any unauthorized modification is immediately detected
- **Version Control:** All record versions are preserved and linked

---

## Appendix: Example Workflows

### Workflow 1: Patient Books Appointment

1. **Patient registers** (if new): `POST /auth/register`
2. **Patient logs in**: `POST /auth/login`
3. **Patient views available doctors**: `GET /queue/status`
4. **Patient books appointment**: `POST /appointments/`
5. **Patient receives confirmation** with queue position and estimated wait time

### Workflow 2: Walk-In Patient Registration

1. **Nurse logs in**: `POST /auth/login`
2. **Nurse registers walk-in patient**: `POST /appointments/walk-in`
3. **System creates patient record** (if new) and appointment
4. **Nurse receives** queue position and estimated wait time
5. **Queue updates broadcast** via WebSocket to all connected clients

### Workflow 3: Doctor Consultation

1. **Doctor logs in**: `POST /auth/login`
2. **Doctor views queue**: `GET /queue/doctor/{doctor_id}`
3. **Nurse checks in patient**: `PATCH /appointments/{id}/status` (status: `checked_in`)
4. **Doctor starts consultation**: `PATCH /appointments/{id}/status` (status: `in_progress`)
5. **Doctor creates consultation note**: `POST /medical-records/consultation-notes`
6. **Doctor creates prescription**: `POST /medical-records/prescriptions`
7. **Doctor completes consultation**: `PATCH /appointments/{id}/status` (status: `completed`)
8. **System updates queue** and broadcasts changes via WebSocket

### Workflow 4: Patient Views Medical History

1. **Patient logs in**: `POST /auth/login`
2. **Patient views medical records**: `GET /medical-records/patient/{patient_id}`
3. **Patient views version history**: `GET /medical-records/{record_id}/versions`
4. **System verifies integrity** and flags any tampered records

### Workflow 5: Admin Audits System

1. **Admin logs in**: `POST /auth/login`
2. **Admin views audit logs**: `GET /audit/logs?start_date=...&end_date=...`
3. **Admin checks tampering alerts**: `GET /audit/tampering-alerts`
4. **Admin exports audit logs**: `GET /audit/export?format=csv`

---

## Support

For questions or issues with the API, please contact the development team.

**Last Updated:** January 2024

**API Version:** 1.0.0
