"""
Patient search endpoint (Doctor and Nurse only)
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.patient import PatientSearchResponse, PatientSearchResult

router = APIRouter()


def _compute_age(dob: Optional[date]) -> Optional[int]:
    """Return full years elapsed since date of birth, or None if dob is None."""
    if dob is None:
        return None
    today = date.today()
    return today.year - dob.year - (
        (today.month, today.day) < (dob.month, dob.day)
    )


@router.get("/search", response_model=PatientSearchResponse)
async def search_patients(
    q: str = Query(..., min_length=1, max_length=100, description="Search by patient name or phone number"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.DOCTOR, UserRole.NURSE)),
):
    """
    Search patients by name or phone number (Doctor and Nurse only).

    Performs a case-insensitive ILIKE search across:
    - ``users.name``   — patient's full name
    - ``patients.phone`` — contact phone number

    Returns paginated results ordered alphabetically by name.
    Only patients with active user accounts are included.
    """
    search_term = f"%{q.strip()}%"

    base_query = (
        db.query(Patient)
        .join(User, Patient.user_id == User.id)
        .filter(
            User.is_active == True,
            or_(
                User.name.ilike(search_term),
                Patient.phone.ilike(search_term),
            ),
        )
        .order_by(User.name.asc())
    )

    total = base_query.count()
    patients = base_query.offset((page - 1) * page_size).limit(page_size).all()

    results = [
        PatientSearchResult(
            id=p.id,
            user_id=p.user_id,
            name=p.user.name if p.user else "Unknown",
            phone=p.phone,
            blood_group=p.blood_group,
            date_of_birth=p.date_of_birth,
            gender=p.gender,
            age=_compute_age(p.date_of_birth),
        )
        for p in patients
    ]

    return PatientSearchResponse(
        results=results,
        total=total,
        page=page,
        page_size=page_size,
    )
