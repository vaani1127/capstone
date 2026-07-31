"""
Utility functions for common database queries, access control, and response building.
Consolidates ~100 lines of repeated code from endpoints.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.user import User, UserRole


def get_patient_by_id(db: Session, patient_id: int) -> Patient:
    """
    Retrieve a patient by ID. Raises 404 if not found.
    Consolidates 13 repeated patient lookup queries across endpoints.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found",
        )
    return patient


def check_patient_access(
    db: Session, current_user: User, patient_id: int, allow_patient_self_access: bool = True
) -> None:
    """
    Verify access control for patient records.

    Allow access if:
    - User is staff (Admin, Doctor, Nurse), OR
    - User is the patient themselves (if allow_patient_self_access=True)

    Raises 403 Forbidden if access denied.

    Consolidates 3 repeated access control functions:
    - allergies.py:_assert_read_access()
    - procedures.py:_assert_read_access()
    - vitals.py:_assert_patient_access()
    """
    # Staff always have access
    if current_user.role in (UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE):
        return

    # Patient can access own records if enabled
    if allow_patient_self_access and current_user.role == UserRole.PATIENT:
        patient = (
            db.query(Patient)
            .filter(Patient.id == patient_id, Patient.user_id == current_user.id)
            .first()
        )
        if patient:
            return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: insufficient permissions to view this record",
    )
