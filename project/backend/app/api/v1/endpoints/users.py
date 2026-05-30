"""
User management endpoints
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_admin
from app.db.session import get_db
from app.models.doctor import Doctor
from app.models.user import User, UserRole
from app.schemas.user import (
    DoctorProfileResponse,
    UserResponse,
    UserRoleUpdate,
    UserUpdate,
)
from app.services.blockchain_service import create_audit_entry

router = APIRouter()


# ---------------------------------------------------------------------------
# Existing routes (unchanged behaviour; inactive users filtered from lists)
# ---------------------------------------------------------------------------

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.

    Requires valid access token in Authorization header.
    """
    return current_user


@router.get("/", response_model=list[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    List all active users (Admin only).
    """
    return db.query(User).filter(User.is_active == True).all()


@router.get("/doctors", response_model=list[DoctorProfileResponse])
async def list_doctors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all doctors whose accounts are active (any authenticated user).

    Used by patients to browse available doctors when booking appointments.
    """
    doctors = (
        db.query(Doctor)
        .join(User, Doctor.user_id == User.id)
        .filter(User.is_active == True)
        .all()
    )
    result = []
    for doc in doctors:
        result.append(DoctorProfileResponse(
            id=doc.id,
            user_id=doc.user_id,
            name=doc.user.name if doc.user else "Unknown",
            specialization=doc.specialization,
            license_number=doc.license_number,
            average_consultation_duration=doc.average_consultation_duration or 15,
        ))
    return result


# ---------------------------------------------------------------------------
# New admin routes
# ---------------------------------------------------------------------------

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Update a user's name, email, and/or role (Admin only).

    - Email uniqueness is validated if the email field changes.
    - All provided fields are applied; omitted fields are left unchanged.
    - The operation is recorded in the audit chain.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a deactivated user",
        )

    updated_fields: list[str] = []

    if payload.name is not None and payload.name != user.name:
        user.name = payload.name
        updated_fields.append("name")

    if payload.email is not None and payload.email != user.email:
        conflict = (
            db.query(User)
            .filter(User.email == payload.email, User.id != user_id)
            .first()
        )
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{payload.email}' is already in use",
            )
        user.email = payload.email
        updated_fields.append("email")

    if payload.role is not None and payload.role != user.role:
        user.role = payload.role
        updated_fields.append("role")

    if not updated_fields:
        return user

    user.updated_at = datetime.utcnow()
    db.flush()

    audit_entry = create_audit_entry(
        db=db,
        record_id=user.id,
        record_type="user_updated",
        record_data={
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "updated_fields": updated_fields,
            "updated_by": current_admin.id,
        },
        user_id=current_admin.id,
    )

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Soft-delete a user by setting is_active=False (Admin only).

    The user record, appointments, and medical records are preserved.
    The deactivated account cannot authenticate and is excluded from all
    list queries. Returns 204 on success.
    """
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admins cannot deactivate their own account",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already deactivated",
        )

    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.flush()

    create_audit_entry(
        db=db,
        record_id=user.id,
        record_type="user_deactivated",
        record_data={
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "deactivated_by": current_admin.id,
        },
        user_id=current_admin.id,
    )

    db.commit()


@router.patch("/{user_id}/role", response_model=UserResponse)
async def change_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Change a user's role (Admin only).

    Accepted values: Admin, Doctor, Nurse, Patient.
    Prevents an admin from changing their own role (would risk lock-out).
    The operation is recorded in the audit chain.
    """
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admins cannot change their own role",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change role of a deactivated user",
        )

    if user.role == payload.role:
        return user

    previous_role = user.role.value
    user.role = payload.role
    user.updated_at = datetime.utcnow()
    db.flush()

    create_audit_entry(
        db=db,
        record_id=user.id,
        record_type="user_role_changed",
        record_data={
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "previous_role": previous_role,
            "new_role": payload.role.value,
            "changed_by": current_admin.id,
        },
        user_id=current_admin.id,
    )

    db.commit()
    db.refresh(user)
    return user
