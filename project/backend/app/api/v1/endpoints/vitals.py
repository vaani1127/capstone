"""
Vitals endpoints — recording and retrieval of patient vital signs
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role, require_patient
from app.core.utils import get_patient_by_id, check_patient_access
from app.core.crud_helpers import create_record_with_audit
from app.db.session import get_db
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.models.vitals import Vitals
from app.schemas.vitals import VitalsCreate, VitalsListResponse, VitalsResponse
from app.services.blockchain_service import create_audit_entry

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_bmi(weight_kg: float | None, height_cm: float | None) -> float | None:
    """Return BMI rounded to 1 decimal place, or None if inputs are missing."""
    if weight_kg and height_cm and height_cm > 0:
        height_m = height_cm / 100.0
        return round(weight_kg / (height_m ** 2), 1)
    return None


def _build_response(vitals: Vitals) -> VitalsResponse:
    """Convert ORM Vitals object to VitalsResponse, resolving recorder name."""
    recorder_name: str | None = None
    if vitals.recorder:
        recorder_name = vitals.recorder.name
    return VitalsResponse(
        id=vitals.id,
        patient_id=vitals.patient_id,
        appointment_id=vitals.appointment_id,
        recorded_by=vitals.recorded_by,
        recorded_by_name=recorder_name,
        recorded_at=vitals.recorded_at,
        systolic_bp=vitals.systolic_bp,
        diastolic_bp=vitals.diastolic_bp,
        heart_rate=vitals.heart_rate,
        temperature=vitals.temperature,
        respiratory_rate=vitals.respiratory_rate,
        oxygen_saturation=vitals.oxygen_saturation,
        weight_kg=vitals.weight_kg,
        height_cm=vitals.height_cm,
        bmi=vitals.bmi,
        notes=vitals.notes,
        created_at=vitals.created_at,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/", response_model=VitalsResponse, status_code=status.HTTP_201_CREATED)
async def record_vitals(
    payload: VitalsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.NURSE, UserRole.DOCTOR)),
):
    """
    Record a new set of vital signs for a patient (Nurse or Doctor only).

    BMI is computed automatically when both weight_kg and height_cm are
    provided.  The operation is appended to the audit chain with
    record_type='vitals_recorded'.
    """
    patient = get_patient_by_id(db, payload.patient_id)

    bmi = _compute_bmi(payload.weight_kg, payload.height_cm)

    vitals = Vitals(
        patient_id=payload.patient_id,
        appointment_id=payload.appointment_id,
        recorded_by=current_user.id,
        recorded_at=datetime.utcnow(),
        systolic_bp=payload.systolic_bp,
        diastolic_bp=payload.diastolic_bp,
        heart_rate=payload.heart_rate,
        temperature=payload.temperature,
        respiratory_rate=payload.respiratory_rate,
        oxygen_saturation=payload.oxygen_saturation,
        weight_kg=payload.weight_kg,
        height_cm=payload.height_cm,
        bmi=bmi,
        notes=payload.notes,
    )
    vitals = create_record_with_audit(
        db=db,
        record=vitals,
        record_type="vitals_recorded",
        record_data={
            "patient_id": payload.patient_id,
            "appointment_id": payload.appointment_id,
            "systolic_bp": payload.systolic_bp,
            "diastolic_bp": payload.diastolic_bp,
            "heart_rate": payload.heart_rate,
            "temperature": payload.temperature,
            "respiratory_rate": payload.respiratory_rate,
            "oxygen_saturation": payload.oxygen_saturation,
            "weight_kg": payload.weight_kg,
            "height_cm": payload.height_cm,
            "bmi": bmi,
            "recorded_by": current_user.id,
        },
        user_id=current_user.id,
        logger_obj=logger,
    )
    return _build_response(vitals)


@router.get("/me", response_model=VitalsListResponse)
async def get_my_vitals(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    """
    Return all vitals for the currently authenticated patient (Patient only).

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
        db.query(Vitals)
        .filter(Vitals.patient_id == patient.id)
        .order_by(Vitals.recorded_at.desc())
        .all()
    )
    return VitalsListResponse(vitals=[_build_response(v) for v in rows], total=len(rows))


@router.get("/patient/{patient_id}", response_model=VitalsListResponse)
async def get_patient_vitals(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return all vitals for a specific patient ordered by recorded_at descending.

    Access rules:
    - Doctor, Nurse, Admin: any patient
    - Patient: own records only
    """
    check_patient_access(db, current_user, patient_id)

    patient = get_patient_by_id(db, patient_id)

    rows = (
        db.query(Vitals)
        .filter(Vitals.patient_id == patient_id)
        .order_by(Vitals.recorded_at.desc())
        .all()
    )
    return VitalsListResponse(vitals=[_build_response(v) for v in rows], total=len(rows))


@router.get("/patient/{patient_id}/latest", response_model=VitalsResponse)
async def get_latest_patient_vitals(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return the single most recent vitals row for a patient.

    Access rules are the same as GET /vitals/patient/{patient_id}.
    Returns 404 if no vitals have been recorded yet.
    """
    check_patient_access(db, current_user, patient_id)

    patient = get_patient_by_id(db, patient_id)

    row = (
        db.query(Vitals)
        .filter(Vitals.patient_id == patient_id)
        .order_by(Vitals.recorded_at.desc())
        .first()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No vitals recorded yet for this patient",
        )
    return _build_response(row)
