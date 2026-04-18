# HealthSaathi API Documentation

Complete API reference with authentication, endpoints, and security requirements.

## Overview

**Base URL:** `http://localhost:8000/api/v1`  
**API Version:** v1  
**Content Type:** `application/json`

All protected endpoints require a valid JWT access token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## Authentication Flow

1. **Register** a new user account (`POST /auth/register`)
2. **Login** with credentials to receive access and refresh tokens (`POST /auth/login`)
3. Include the **access token** in Authorization header for all protected endpoints
4. When access token expires, use refresh token to get a new one (`POST /auth/refresh`)

### Token Details

- **Access Token:** Valid for 30 minutes
- **Refresh Token:** Valid for 7 days
- **Algorithm:** HS256
- **Type:** Bearer

### Token Payload

```json
{
  "user_id": 123,
  "email": "user@example.com",
  "role": "Doctor",
  "exp": 1234567890,
  "type": "access"
}
```

## Common Error Codes

| Status | Error | Description |
|--------|-------|-------------|
| 400 | Bad Request | Invalid request data or validation error |
| 401 | Unauthorized | Missing, invalid, or expired token |
| 403 | Forbidden | User lacks required permissions |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Resource conflict (e.g., double-booking) |
| 500 | Server Error | Unexpected server error |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Public Endpoints (No Authentication)

### 1. Register User

**POST** `/auth/register`

Register a new user account with role assignment.

**Request:**
```json
{
  "name": "Dr. John Smith",
  "email": "john@example.com",
  "password": "SecurePass123",
  "role": "Doctor"
}
```

**Response (201):**
```json
{
  "id": 1,
  "name": "Dr. John Smith",
  "email": "john@example.com",
  "role": "Doctor",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 2. Login

**POST** `/auth/login`

Authenticate user and receive JWT tokens.

**Request:**
```json
{
  "email": "john@example.com",
  "password": "SecurePass123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "Dr. John Smith",
    "email": "john@example.com",
    "role": "Doctor"
  }
}
```

### 3. Refresh Token

**POST** `/auth/refresh`

Obtain a new access token using a refresh token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

## Protected Endpoints

### Role-Based Access Control

The system supports four user roles:
- **Admin** - Full system access, user management, audit logs
- **Doctor** - Medical record creation, appointment management
- **Nurse** - Walk-in registration, queue management
- **Patient** - View own records, book appointments

### User Management

**GET** `/users/me` (Any authenticated user)  
Get current user info

**GET** `/users` (Admin only)  
List all users

### Appointments

**GET** `/appointments` (Any user - filtered by role)
- Patient: own appointments
- Doctor: appointments assigned to them
- Nurse/Admin: all appointments

**POST** `/appointments` (Patient only)  
Book new appointment

**PUT** `/appointments/{id}` (Any user - ownership verified)  
Update appointment

**DELETE** `/appointments/{id}` (Any user - ownership verified)  
Cancel appointment

**POST** `/appointments/walk-in` (Staff only)  
Register walk-in patient

### Queue Management

**GET** `/queue/status` (Any authenticated user)  
Get queue status for all doctors

**GET** `/queue/doctor/{id}` (Any authenticated user)  
Get queue for specific doctor

### Medical Records

**GET** `/medical-records/patient/{id}` (Authorized access)
- Patient can view own records
- Doctor can view records of treated patients
- Admin can view all

**POST** `/medical-records` (Doctor only)  
Create new medical record

**PUT** `/medical-records/{id}` (Doctor who created - only)  
Update medical record

**GET** `/medical-records/{id}/versions` (Authorized access)  
Get record version history

### Audit Endpoints

**GET** `/audit/logs` (Admin only)  
Get audit logs with filtering

**GET** `/audit/tampering-alerts` (Admin only)  
Get tampering alerts

**POST** `/audit/verify/{id}` (Admin only)  
Manually verify record integrity

## Endpoint Protection in Code

### Single Role Protection

```python
from app.core.dependencies import require_doctor

@router.post("/medical-records")
async def create_record(
    current_user: User = Depends(require_doctor)
):
    # Only doctors can access
    pass
```

### Multiple Role Protection

```python
from app.core.dependencies import require_staff

@router.post("/walk-in")
async def register_walk_in(
    current_user: User = Depends(require_staff)
):
    # Admin, Doctor, or Nurse can access
    pass
```

### Custom Authorization

```python
from app.core.dependencies import get_current_user

@router.get("/appointments")
async def list_appointments(
    current_user: User = Depends(get_current_user)
):
    # All authenticated users can access
    # Results filtered based on role
    if current_user.role == UserRole.PATIENT:
        return get_patient_appointments(current_user.id)
    else:
        return get_all_appointments()
```

## Security Best Practices

### Token Management
- Access tokens are short-lived (15-30 minutes)
- Refresh tokens should be rotated on each refresh
- Store tokens securely in mobile app encrypted storage

### Password Security
- Passwords hashed with bcrypt (cost factor 12)
- Minimum 8 characters with uppercase, lowercase, and digits
- No plaintext passwords stored or logged

### HTTPS
- Always use HTTPS in production
- SSL/TLS certificates required

---

For interactive API testing, visit http://localhost:8000/api/docs
