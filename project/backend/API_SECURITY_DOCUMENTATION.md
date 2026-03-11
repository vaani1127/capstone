# API Security Documentation

## Overview

All API endpoints in HealthSaathi are protected with JWT-based authentication and role-based authorization (RBAC). This document details the security requirements for each endpoint.

## Authentication

All protected endpoints require a valid JWT access token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Public Endpoints (No Authentication Required)

- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Token refresh
- `GET /api/v1/` - API root

## Role-Based Access Control

The system supports four user roles:
- **Admin** - Full system access, user management, audit logs
- **Doctor** - Medical record creation, appointment management
- **Nurse** - Walk-in registration, queue management
- **Patient** - View own records, book appointments

## Endpoint Security Matrix

### Authentication Endpoints (`/api/v1/auth`)

| Endpoint | Method | Authentication | Required Role | Description |
|----------|--------|----------------|---------------|-------------|
| `/register` | POST | ❌ None | None | Register new user |
| `/login` | POST | ❌ None | None | Login and get tokens |
| `/refresh` | POST | ❌ None | None | Refresh access token |

### User Management Endpoints (`/api/v1/users`)

| Endpoint | Method | Authentication | Required Role | Description |
|----------|--------|----------------|---------------|-------------|
| `/me` | GET | ✅ Required | Any | Get current user info |
| `/` | GET | ✅ Required | Admin | List all users |

**Authorization Logic:**
- `/me` - Any authenticated user can view their own information
- `/` - Only Admins can list all users

### Appointment Endpoints (`/api/v1/appointments`)

| Endpoint | Method | Authentication | Required Role | Description |
|----------|--------|----------------|---------------|-------------|
| `/` | GET | ✅ Required | Any | List appointments (filtered by role) |
| `/` | POST | ✅ Required | Patient | Book new appointment |
| `/{id}` | PUT | ✅ Required | Any | Update appointment |
| `/{id}` | DELETE | ✅ Required | Any | Cancel appointment |
| `/walk-in` | POST | ✅ Required | Admin, Doctor, Nurse | Register walk-in patient |

**Authorization Logic:**
- `GET /` - Returns appointments based on role:
  - **Patient**: Only their own appointments
  - **Doctor**: Appointments assigned to them
  - **Nurse/Admin**: All appointments
- `POST /` - Only Patients can book appointments
- `PUT /{id}` - Patients can update their own appointments; Staff can update any
- `DELETE /{id}` - Patients can cancel their own appointments; Staff can cancel any
- `POST /walk-in` - Only Staff (Admin, Doctor, Nurse) can register walk-ins

### Queue Management Endpoints (`/api/v1/queue`)

| Endpoint | Method | Authentication | Required Role | Description |
|----------|--------|----------------|---------------|-------------|
| `/status` | GET | ✅ Required | Any | Get queue status for all doctors |
| `/doctor/{id}` | GET | ✅ Required | Any | Get queue for specific doctor |

**Authorization Logic:**
- All authenticated users can view queue status (public information for waiting time estimation)

### Medical Records Endpoints (`/api/v1/medical-records`)

| Endpoint | Method | Authentication | Required Role | Description |
|----------|--------|----------------|---------------|-------------|
| `/patient/{id}` | GET | ✅ Required | Any | Get patient's medical records |
| `/` | POST | ✅ Required | Doctor | Create new medical record |
| `/{id}` | PUT | ✅ Required | Doctor | Update medical record |
| `/{id}/versions` | GET | ✅ Required | Any | Get record version history |

**Authorization Logic:**
- `GET /patient/{id}` - Access granted if:
  - User is the patient (patient_id matches their record)
  - User is a Doctor who has treated this patient
  - User is an Admin
- `POST /` - Only Doctors can create medical records
- `PUT /{id}` - Only the Doctor who created the record can update it
- `GET /{id}/versions` - Same access rules as viewing records

### Audit Endpoints (`/api/v1/audit`)

| Endpoint | Method | Authentication | Required Role | Description |
|----------|--------|----------------|---------------|-------------|
| `/logs` | GET | ✅ Required | Admin | Get audit logs with filtering |
| `/tampering-alerts` | GET | ✅ Required | Admin | Get tampering alerts |
| `/verify/{id}` | POST | ✅ Required | Admin | Manually verify record integrity |

**Authorization Logic:**
- All audit endpoints are Admin-only for compliance and security monitoring

## Security Implementation

### Middleware Stack

1. **JWT Validation** (`get_current_user` dependency)
   - Validates Bearer token from Authorization header
   - Decodes JWT and extracts user information
   - Fetches user from database
   - Returns 401 if token invalid/expired or user not found

2. **Role-Based Authorization** (`require_role` dependency)
   - Checks if authenticated user has required role
   - Returns 403 if user lacks required role
   - Logs unauthorized access attempts

### Convenience Dependencies

The system provides pre-configured role dependencies:

```python
# Single role requirements
require_admin()      # Admin only
require_doctor()     # Doctor only
require_nurse()      # Nurse only
require_patient()    # Patient only

# Multiple role requirements
require_staff()      # Admin, Doctor, or Nurse
require_role(UserRole.ADMIN, UserRole.DOCTOR)  # Custom combinations
```

### Usage Examples

#### Endpoint with Single Role

```python
@router.post("/medical-records")
async def create_record(
    current_user: User = Depends(require_doctor)
):
    # Only doctors can access this endpoint
    pass
```

#### Endpoint with Multiple Roles

```python
@router.post("/walk-in")
async def register_walk_in(
    current_user: User = Depends(require_staff)
):
    # Admin, Doctor, or Nurse can access
    pass
```

#### Endpoint with Custom Authorization Logic

```python
@router.get("/appointments")
async def list_appointments(
    current_user: User = Depends(get_current_user)
):
    # All authenticated users can access
    # But results are filtered based on role
    if current_user.role == UserRole.PATIENT:
        return get_patient_appointments(current_user.id)
    elif current_user.role == UserRole.DOCTOR:
        return get_doctor_appointments(current_user.id)
    else:
        return get_all_appointments()
```

## Security Best Practices

### Token Management

1. **Access Tokens**
   - Short-lived (15-30 minutes recommended)
   - Used for API authentication
   - Stored securely in mobile app (encrypted storage)

2. **Refresh Tokens**
   - Longer-lived (7-30 days recommended)
   - Used to obtain new access tokens
   - Should be rotated on each refresh

### Password Security

- Passwords hashed with bcrypt (cost factor 12)
- Minimum password requirements enforced
- No plaintext passwords stored or logged

### Audit Logging

- All protected endpoint access is logged
- Failed authentication attempts are logged
- Unauthorized access attempts are logged with user details
- Medical record access is logged in audit chain

### Error Handling

- Generic error messages for authentication failures
- No user enumeration through error messages
- Detailed errors logged server-side only

## Testing Security

### Unit Tests

Test files verify security implementation:
- `backend/tests/test_auth.py` - Authentication flows
- `backend/tests/test_rbac_middleware.py` - Role-based access control

### Security Test Scenarios

1. **Authentication Tests**
   - Valid credentials return tokens
   - Invalid credentials return 401
   - Expired tokens return 401
   - Missing tokens return 401

2. **Authorization Tests**
   - Users with correct role can access endpoints
   - Users with wrong role receive 403
   - Unauthorized access attempts are logged

3. **Data Access Tests**
   - Patients can only view their own data
   - Doctors can only modify their own records
   - Admins have full access

## Compliance Notes

### HIPAA Considerations

- All medical data access is logged in audit chain
- Audit logs are immutable and tamper-evident
- Role-based access ensures minimum necessary access
- Failed access attempts are monitored

### Data Protection

- Medical records stored off-chain (database only)
- Only hashes stored in audit chain
- HTTPS required for all communications
- Database encryption at rest recommended

## Monitoring and Alerts

### Security Metrics

Monitor these metrics for security issues:
- Failed authentication rate
- 403 Forbidden responses
- Unusual access patterns
- Tampering alerts from audit chain

### Recommended Alerts

- Multiple failed login attempts from same IP
- Access to audit endpoints by non-admins
- Tampering detected in audit chain
- Unusual volume of medical record access

## Future Enhancements

- Multi-factor authentication (MFA)
- IP-based access restrictions
- Rate limiting per user/IP
- Session management and revocation
- OAuth2 integration for third-party apps
- API key authentication for system integrations
