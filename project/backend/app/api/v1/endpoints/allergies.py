"""
Allergies endpoints — recording and retrieval of patient allergy records
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_doctor, require_patient, require_role
from app.core.utils import get_patient_by_id, check_patient_access
from app.core.crud_helpers import create_record_with_audit
from app.db.session import get_db
from app.models.allergy import Allergy
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.allergy import AllergyCreate, AllergyListResponse, AllergyResponse
from app.services.blockchain_service import create_audit_entry

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_response(allergy: Allergy) -> AllergyResponse:
    """Convert ORM Allergy to AllergyResponse, resolving recorder name."""
    return AllergyResponse(
        id=allergy.id,
        patient_id=allergy.patient_id,
        recorded_by=allergy.recorded_by,
        recorded_by_name=allergy.recorder.name if allergy.recorder else None,
        allergen=allergy.allergen,
        reaction=allergy.reaction,
        severity=allergy.severity,
        onset_date=allergy.onset_date,
        is_active=allergy.is_active,
        notes=allergy.notes,
        created_at=allergy.created_at,
        updated_at=allergy.updated_at,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/", response_model=AllergyResponse, status_code=status.HTTP_201_CREATED)
async def record_allergy(
    payload: AllergyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.DOCTOR, UserRole.NURSE)),
):
    """
    Record a new allergy for a patient (Doctor or Nurse only).

    The operation is appended to the audit chain with
    record_type='allergy_recorded'.
    """
    patient = get_patient_by_id(db, payload.patient_id)

    allergy = Allergy(
        patient_id=payload.patient_id,
        recorded_by=current_user.id,
        allergen=payload.allergen.strip(),
        reaction=payload.reaction,
        severity=payload.severity,
        onset_date=payload.onset_date,
        notes=payload.notes,
        is_active=True,
    )
    allergy = create_record_with_audit(
        db=db,
        record=allergy,
        record_type="allergy_recorded",
        record_data={
            "patient_id": payload.patient_id,
            "allergen": payload.allergen,
            "severity": payload.severity,
            "reaction": payload.reaction,
            "onset_date": payload.onset_date.isoformat() if payload.onset_date else None,
            "recorded_by": current_user.id,
        },
        user_id=current_user.id,
        logger_obj=logger,
    )
    return _build_response(allergy)


@router.get("/me", response_model=AllergyListResponse)
async def get_my_allergies(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    """
    Return the authenticated patient's own active allergies (Patient only).

    Convenience endpoint so the patient app does not need to know its own
    patient-table ID.
    """
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found for this user account",
        )

    rows = (
        db.query(Allergy)
        .filter(Allergy.patient_id == patient.id, Allergy.is_active == True)
        .order_by(Allergy.created_at.desc())
        .all()
    )
    return AllergyListResponse(allergies=[_build_response(a) for a in rows], total=len(rows))


@router.get("/patient/{patient_id}", response_model=AllergyListResponse)
async def get_patient_allergies(
    patient_id: int,
    include_inactive: bool = Query(
        False, description="When true, include deactivated allergy records"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return allergy records for a patient (Doctor, Nurse, Admin, or patient themselves).

    By default only active allergies are returned.  Pass ?include_inactive=true
    to retrieve the full history including deactivated records.
    """
    check_patient_access(db, current_user, patient_id)

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found",
        )

    query = db.query(Allergy).filter(Allergy.patient_id == patient_id)
    if not include_inactive:
        query = query.filter(Allergy.is_active == True)

    rows = query.order_by(Allergy.created_at.desc()).all()
    return AllergyListResponse(allergies=[_build_response(a) for a in rows], total=len(rows))


@router.patch("/{allergy_id}/deactivate", response_model=AllergyResponse)
async def deactivate_allergy(
    allergy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor),
):
    """
    Deactivate an allergy record (Doctor only).

    Sets is_active=False and appends an audit entry with
    record_type='allergy_deactivated'.  The record is preserved for audit
    history; it is never deleted.
    """
    allergy = db.query(Allergy).filter(Allergy.id == allergy_id).first()
    if not allergy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Allergy {allergy_id} not found",
        )
    if not allergy.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Allergy record is already inactive",
        )

    allergy.is_active = False
    db.flush()

    create_audit_entry(
        db=db,
        record_id=allergy.id,
        record_type="allergy_deactivated",
        record_data={
            "allergy_id": allergy.id,
            "patient_id": allergy.patient_id,
            "allergen": allergy.allergen,
            "severity": allergy.severity,
            "deactivated_by": current_user.id,
        },
        user_id=current_user.id,
    )

    db.commit()
    db.refresh(allergy)
    logger.info(
        "Allergy deactivated: id=%d patient_id=%d allergen='%s' by user_id=%d",
        allergy.id, allergy.patient_id, allergy.allergen, current_user.id,
    )
    return _build_response(allergy)
