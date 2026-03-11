# JWT Authentication & Authorization

This module provides JWT-based authentication and role-based access control (RBAC) for the HealthSaathi API.

## Overview

The authentication system consists of:
- **JWT Token Generation**: Access tokens (1 hour) and refresh tokens (7 days)
- **Token Validation**: Middleware to validate JWT tokens on protected endpoints
- **Role-Based Access Control**: Enforce role requirements on endpoints
- **Token Refresh**: Mechanism to refresh expired access tokens

## Components

### 1. Security Module (`security.py`)

Provides core security functions:
- `get_password_hash(password)`: Hash passwords using bcrypt
- `verify_password(plain_password, hashed_password)`: Verify password against hash
- `create_access_token(data)`: Generate JWT access token (1 hour expiry)
- `create_refresh_token(data)`: Generate JWT refresh token (7 days expiry)
- `decode_token(token)`: Decode and verify JWT token

### 2. Dependencies Module (`dependencies.py`)

Provides FastAPI dependencies for authentication and authorization:

#### `get_current_user(credentials, db)`
Validates JWT token and returns the current authenticated user.

**Usage:**
```python
from app.core.dependencies import get_current_user

@router.get("/protected")
async def protected_endpoint(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.name}"}
```

#### `require_role(*allowed_roles)`
Factory function to create role-based access control dependencies.

**Usage:**
```python
from app.core.dependencies import require_role
from app.models.user import UserRole

@router.post("/doctors-only")
async def doctors_only(current_user: User = Depends(require_role(UserRole.DOCTOR))):
    return {"message": "Doctor access granted"}

@router.post("/staff-only")
async def staff_only(
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE))
):
    return {"message": "Staff access granted"}
```

#### Convenience Dependencies
Pre-configured role dependencies:
- `require_admin`: Requires Admin role
- `require_doctor`: Requires Doctor role
- `require_nurse`: Requires Nurse role
- `require_patient`: Requires Patient role
- `require_staff`: Requires Admin, Doctor, or Nurse role

**Usage:**
```python
from app.core.dependencies import require_admin, require_doctor

@router.get("/admin-dashboard")
async def admin_dashboard(current_user: User = Depends(require_admin)):
    return {"message": "Admin dashboard"}

@router.post("/consultation")
async def create_consultation(current_user: User = Depends(require_doctor)):
    return {"message": "Consultation created"}
```

## Authentication Flow

### 1. User Registration
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "role": "Patient"
}
```

**Response:**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "role": "Patient",
  "created_at": "2024-02-27T10:00:00Z",
  "updated_at": "2024-02-27T10:00:00Z"
}
```

### 2. User Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "SecurePass123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "role": "Patient",
    "created_at": "2024-02-27T10:00:00Z",
    "updated_at": "2024-02-27T10:00:00Z"
  }
}
```

### 3. Accessing Protected Endpoints
Include the access token in the Authorization header:

```http
GET /api/v1/users/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 4. Token Refresh
When the access token expires, use the refresh token to get a new one:

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": { ... }
}
```

## JWT Token Structure

### Access Token Payload
```json
{
  "user_id": 1,
  "email": "john@example.com",
  "role": "Patient",
  "type": "access",
  "exp": 1709035200
}
```

### Refresh Token Payload
```json
{
  "user_id": 1,
  "email": "john@example.com",
  "role": "Patient",
  "type": "refresh",
  "exp": 1709640000
}
```

## Error Responses

### 401 Unauthorized
Returned when:
- No token provided
- Invalid token
- Expired token
- Token type mismatch (e.g., using refresh token for protected endpoint)
- User not found

```json
{
  "detail": "Invalid or expired token"
}
```

### 403 Forbidden
Returned when user doesn't have required role:

```json
{
  "detail": "Access denied. Required role(s): ['Admin']"
}
```

## Security Best Practices

1. **Token Storage**: Store tokens securely on the client side (e.g., secure HTTP-only cookies or encrypted local storage)
2. **HTTPS Only**: Always use HTTPS in production to prevent token interception
3. **Token Expiry**: Access tokens expire after 1 hour, refresh tokens after 7 days
4. **Password Requirements**: Passwords must be at least 8 characters with uppercase, lowercase, and digit
5. **Bcrypt Hashing**: Passwords are hashed using bcrypt with automatic salt generation

## Configuration

Token expiry times are configured in `config.py`:

```python
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS: int = 7     # 7 days
SECRET_KEY: str                         # Set via environment variable
ALGORITHM: str = "HS256"                # JWT signing algorithm
```

## Testing

Comprehensive tests are available in `backend/tests/test_auth.py`:
- User registration tests
- User login tests
- Token refresh tests
- JWT validation tests
- Role-based access control tests

Run tests:
```bash
pytest backend/tests/test_auth.py -v
```

## Example: Creating a Protected Endpoint

```python
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user, require_doctor
from app.models.user import User

router = APIRouter()

# Any authenticated user can access
@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role
    }

# Only doctors can access
@router.post("/consultation")
async def create_consultation(
    consultation_data: dict,
    current_user: User = Depends(require_doctor)
):
    # Only doctors can reach this code
    return {"message": "Consultation created by Dr. " + current_user.name}
```

## Logging

All authentication events are logged:
- Successful registrations
- Failed registration attempts (duplicate email)
- Successful logins
- Failed login attempts
- Token refresh events
- Unauthorized access attempts

Logs include user email and ID for audit purposes.
