# Endpoint Protection Quick Reference

## How to Protect API Endpoints

This guide shows how to apply authentication and authorization to FastAPI endpoints in HealthSaathi.

## Import Required Dependencies

```python
from fastapi import APIRouter, Depends
from app.models.user import User
from app.core.dependencies import (
    get_current_user,      # Base authentication
    require_admin,         # Admin only
    require_doctor,        # Doctor only
    require_nurse,         # Nurse only
    require_patient,       # Patient only
    require_staff,         # Admin, Doctor, or Nurse
    require_role           # Custom role combinations
)
```

## Protection Patterns

### 1. Any Authenticated User

Use when any logged-in user can access the endpoint:

```python
@router.get("/resource")
async def get_resource(
    current_user: User = Depends(get_current_user)
):
    # Any authenticated user can access
    # Use current_user.role to apply custom logic
    pass
```

### 2. Single Role Requirement

Use pre-built dependencies for single role requirements:

```python
# Admin only
@router.get("/admin-resource")
async def admin_only(
    current_user: User = Depends(require_admin)
):
    pass

# Doctor only
@router.post("/medical-record")
async def create_record(
    current_user: User = Depends(require_doctor)
):
    pass

# Patient only
@router.post("/appointment")
async def book_appointment(
    current_user: User = Depends(require_patient)
):
    pass
```

### 3. Multiple Role Requirement

Use `require_staff` for Admin/Doctor/Nurse or create custom combinations:

```python
# Staff only (Admin, Doctor, or Nurse)
@router.post("/walk-in")
async def register_walk_in(
    current_user: User = Depends(require_staff)
):
    pass

# Custom combination
from app.models.user import UserRole

@router.get("/special-resource")
async def special_access(
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.DOCTOR))
):
    pass
```

### 4. Role-Based Filtering

Use when all users can access but results differ by role:

```python
@router.get("/appointments")
async def list_appointments(
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.PATIENT:
        # Return only patient's appointments
        return get_patient_appointments(current_user.id)
    elif current_user.role == UserRole.DOCTOR:
        # Return doctor's appointments
        return get_doctor_appointments(current_user.id)
    else:
        # Admin/Nurse see all
        return get_all_appointments()
```

### 5. Ownership Verification

Use when users can only access their own resources:

```python
@router.get("/medical-records/{patient_id}")
async def get_records(
    patient_id: int,
    current_user: User = Depends(get_current_user)
):
    # Verify ownership or authorized access
    if current_user.role == UserRole.PATIENT:
        # Verify patient_id matches current user
        if patient_id != current_user.patient.id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == UserRole.DOCTOR:
        # Verify doctor has treated this patient
        if not has_treated_patient(current_user.id, patient_id):
            raise HTTPException(status_code=403, detail="Access denied")
    # Admin has full access
    
    return get_patient_records(patient_id)
```

## Common Patterns by Endpoint Type

### Public Endpoints (No Protection)

```python
@router.post("/auth/login")
async def login():
    # No authentication required
    pass
```

### User Profile Endpoints

```python
@router.get("/users/me")
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user
```

### Admin-Only Endpoints

```python
@router.get("/users")
async def list_users(
    current_user: User = Depends(require_admin)
):
    return get_all_users()
```

### Resource Creation (Role-Specific)

```python
@router.post("/medical-records")
async def create_record(
    current_user: User = Depends(require_doctor)
):
    # Only doctors can create medical records
    pass
```

### Resource Access (Ownership-Based)

```python
@router.get("/appointments/{id}")
async def get_appointment(
    id: int,
    current_user: User = Depends(get_current_user)
):
    appointment = get_appointment_by_id(id)
    
    # Verify ownership or staff access
    if current_user.role == UserRole.PATIENT:
        if appointment.patient_id != current_user.patient.id:
            raise HTTPException(status_code=403)
    # Staff can access all appointments
    
    return appointment
```

## Error Responses

### 401 Unauthorized

Returned when:
- No token provided
- Invalid token
- Expired token
- User not found

```json
{
  "detail": "Invalid or expired token"
}
```

### 403 Forbidden

Returned when:
- User lacks required role
- User doesn't own the resource
- User not authorized to access resource

```json
{
  "detail": "Access denied. Required role(s): ['Admin']"
}
```

## Testing Protected Endpoints

### Unit Test Example

```python
def test_protected_endpoint_requires_auth(client):
    # Without token
    response = client.get("/api/v1/protected")
    assert response.status_code == 401

def test_protected_endpoint_requires_role(client, patient_token):
    # Patient trying to access admin endpoint
    response = client.get(
        "/api/v1/admin-only",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert response.status_code == 403

def test_protected_endpoint_success(client, admin_token):
    # Admin accessing admin endpoint
    response = client.get(
        "/api/v1/admin-only",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
```

## Checklist for New Endpoints

When creating a new endpoint, ensure:

- [ ] Authentication requirement is clear (public vs protected)
- [ ] Required role(s) are documented in docstring
- [ ] Appropriate dependency is used (`get_current_user`, `require_*`)
- [ ] Ownership verification is implemented if needed
- [ ] Error cases return appropriate status codes (401, 403)
- [ ] Endpoint is documented in API_SECURITY_DOCUMENTATION.md
- [ ] Unit tests cover authentication and authorization scenarios

## Quick Reference Table

| Access Pattern | Dependency to Use | Example Use Case |
|----------------|-------------------|------------------|
| Any authenticated user | `get_current_user` | View queue status |
| Admin only | `require_admin` | View audit logs |
| Doctor only | `require_doctor` | Create medical record |
| Nurse only | `require_nurse` | Check-in patient |
| Patient only | `require_patient` | Book appointment |
| Staff (Admin/Doctor/Nurse) | `require_staff` | Register walk-in |
| Custom roles | `require_role(Role1, Role2)` | Special access |
| Ownership-based | `get_current_user` + logic | View own records |

## Additional Resources

- Full security documentation: `API_SECURITY_DOCUMENTATION.md`
- RBAC middleware implementation: `app/core/dependencies.py`
- Authentication tests: `tests/test_auth.py`
- RBAC tests: `tests/test_rbac_middleware.py`
