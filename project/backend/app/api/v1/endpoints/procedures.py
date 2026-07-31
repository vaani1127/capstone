"""
Procedures endpoints — recording and retrieval of clinical procedures
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_doctor, require_patient
from app.core.utils import get_patient_by_id, check_patient_access
from app.core.crud_helpers import create_record_with_audit
from app.db.session import get_db
from app.models.patient import Patient
from app.models.procedure import Procedure
from app.models.user import User, UserRole
from app.schemas.procedure import ProcedureCreate, ProcedureListResponse, ProcedureResponse
from app.services.blockchain_service import create_audit_entry

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_response(proc: Procedure) -> ProcedureResponse:
    return ProcedureResponse(
        id=proc.id,
        patient_id=proc.patient_id,
        encounter_id=proc.encounter_id,
        performed_by=proc.performed_by,
        performed_by_name=proc.performer.name if proc.performer else None,
        procedure_code=proc.procedure_code,
        description=proc.description,
        performed_at=proc.performed_at,
        duration_minutes=proc.duration_minutes,
        outcome=proc.outcome,
        base_cost=float(proc.base_cost) if proc.base_cost is not None else None,
        notes=proc.notes,
        created_at=proc.created_at,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/", response_model=ProcedureResponse, status_code=status.HTTP_201_CREATED)
async def record_procedure(
    payload: ProcedureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor),
):
    """
    Record a clinical procedure for a patient (Doctor only).

    Appends an audit chain entry with record_type='procedure_recorded'.
    """
    patient = get_patient_by_id(db, payload.patient_id)

    proc = Procedure(
        patient_id=payload.patient_id,
        encounter_id=payload.encounter_id,
        performed_by=current_user.id,
        procedure_code=payload.procedure_code,
        description=payload.description.strip(),
        performed_at=payload.performed_at,
        duration_minutes=payload.duration_minutes,
        outcome=payload.outcome,
        base_cost=payload.base_cost,
        notes=payload.notes,
    )
    proc = create_record_with_audit(
        db=db,
        record=proc,
        record_type="procedure_recorded",
        record_data={
            "patient_id": payload.patient_id,
            "description": payload.description,
            "procedure_code": payload.procedure_code,
            "performed_at": payload.performed_at.isoformat(),
            "base_cost": payload.base_cost,
            "recorded_by": current_user.id,
        },
        user_id=current_user.id,
        logger_obj=logger,
    )
    return _build_response(proc)


@router.get("/me", response_model=ProcedureListResponse)
async def get_my_procedures(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    """
    Return the authenticated patient's own procedure history (Patient only).

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
        db.query(Procedure)
        .filter(Procedure.patient_id == patient.id)
        .order_by(Procedure.performed_at.desc())
        .all()
    )
    return ProcedureListResponse(procedures=[_build_response(p) for p in rows], total=len(rows))


@router.get("/patient/{patient_id}", response_model=ProcedureListResponse)
async def get_patient_procedures(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return all procedures for a patient ordered by performed_at descending.

    Access: Doctor, Nurse, Admin — any patient.  Patient — own records only.
    """
    check_patient_access(db, current_user, patient_id)

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found",
        )

    rows = (
        db.query(Procedure)
        .filter(Procedure.patient_id == patient_id)
        .order_by(Procedure.performed_at.desc())
        .all()
    )
    return ProcedureListResponse(procedures=[_build_response(p) for p in rows], total=len(rows))
