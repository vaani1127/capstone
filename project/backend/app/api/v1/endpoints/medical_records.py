"""
Medical records management endpoints
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.medical_record import MedicalRecord
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.core.dependencies import get_current_user, require_doctor
from app.schemas.medical_record import (
    ConsultationNoteCreate,
    ConsultationNoteResponse,
    MedicalRecordCreate,
    PrescriptionCreate,
    PrescriptionUpdate,
    MedicalRecordUpdate,
    MedicalRecordResponse
)
from app.models.user import UserRole
from app.models.audit_chain import AuditChain
from app.services.blockchain_service import (
    create_medical_record_audit_entry,
    verify_record_integrity,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


async def _trigger_anomaly_check(db, user_id: int, audit_entry_id: int):
    try:
        from app.services.anomaly_service import analyze_and_alert
        from app.services.websocket_manager import manager
        alert = analyze_and_alert(db, user_id, audit_entry_id)
        if alert and alert.severity in ("MEDIUM", "HIGH"):
            payload = {
                "type": "anomaly_alert",
                "severity": alert.severity,
                "alert_id": alert.id,
                "user_id": alert.user_id,
                "anomaly_score": float(alert.anomaly_score),
                "explanation": alert.explanation,
                "top_features": alert.top_features,
                "timestamp": alert.created_at.isoformat()
            }
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(manager.broadcast_anomaly_alert(payload))
            except Exception:
                pass
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Anomaly check failed: {e}")


def check_and_flag_tampering(db: Session, record_id: int) -> bool:
    """
    Check record integrity and flag if tampered.
    
    Args:
        db: Database session
        record_id: ID of the medical record to check
        
    Returns:
        bool: True if record is tampered, False if integrity verified
    """
    try:
        is_valid = verify_record_integrity(db, record_id)
        
        if not is_valid:
            # Tampering detected - log alert and flag in database
            logger.warning(
                f"TAMPERING DETECTED: Medical record {record_id} failed integrity verification"
            )
            
            # Update audit_chain entry to mark as tampered
            audit_entry = db.query(AuditChain).filter(
                AuditChain.record_id == record_id,
                AuditChain.record_type == "medical_record"
            ).order_by(AuditChain.id.desc()).first()
            
            if audit_entry:
                audit_entry.is_tampered = True
                db.commit()
                logger.info(f"Flagged audit entry {audit_entry.id} as tampered")
            
            return True  # Record is tampered
        
        return False  # Record integrity verified
        
    except ValueError as e:
        # Missing audit entry or record - log error but don't flag as tampered
        logger.error(f"Error verifying record {record_id}: {str(e)}")
        return False  # Treat as not tampered if verification cannot be performed
    except Exception as e:
        # Unexpected error during verification
        logger.error(f"Unexpected error verifying record {record_id}: {str(e)}")
        return False


@router.get("/patient/{patient_id}", response_model=List[MedicalRecordResponse])
async def get_patient_records(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get medical records for a patient.
    
    - Patients can view their own records
    - Doctors can view records of their patients
    - Admins can view all records
    
    **Required Role:** Any authenticated user
    **Authorization:** Ownership or authorized access verified
    
    Args:
        patient_id: ID of the patient
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of medical records for the patient (latest versions only, sorted by date)
        
    Raises:
        HTTPException 403: If user not authorized to view records
        HTTPException 404: If patient not found
    """
    logger.info(f"User {current_user.id} requesting medical records for patient {patient_id}")
    
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        logger.warning(f"Patient {patient_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Authorization check based on user role
    if current_user.role == UserRole.PATIENT:
        # Patients can only view their own records
        user_patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not user_patient or user_patient.id != patient_id:
            logger.warning(
                f"Patient user {current_user.id} attempted to access records for patient {patient_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own medical records"
            )
    
    elif current_user.role == UserRole.DOCTOR:
        # Doctors can view records of patients they have treated
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor:
            logger.error(f"Doctor record not found for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor record not found"
            )
        
        # Check if doctor has treated this patient (has any medical records for them)
        has_treated = db.query(MedicalRecord).filter(
            MedicalRecord.patient_id == patient_id,
            MedicalRecord.doctor_id == doctor.id
        ).first() is not None
        
        if not has_treated:
            logger.warning(
                f"Doctor {doctor.id} attempted to access records for patient {patient_id} "
                f"they have not treated"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view records of patients you have treated"
            )
    
    elif current_user.role == UserRole.ADMIN:
        # Admins can view all records
        pass
    
    else:
        # Nurses and other roles cannot view medical records
        logger.warning(f"User {current_user.id} with role {current_user.role} attempted to view medical records")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view medical records"
        )
    
    # Get all medical records for the patient
    # Only return the latest version of each record (highest version_number per appointment)
    # We need to find records that are not superseded by newer versions
    
    # Subquery to find the maximum version number for each appointment
    from sqlalchemy import func
    from sqlalchemy.sql import and_
    
    # Get all records for the patient
    all_records = db.query(MedicalRecord).filter(
        MedicalRecord.patient_id == patient_id
    ).all()
    
    # Group by appointment_id and find latest version
    latest_records_map = {}
    for record in all_records:
        key = record.appointment_id if record.appointment_id else f"standalone_{record.id}"
        if key not in latest_records_map or record.version_number > latest_records_map[key].version_number:
            latest_records_map[key] = record
    
    latest_records = list(latest_records_map.values())
    
    # Sort by created_at (newest first)
    latest_records.sort(key=lambda r: r.created_at, reverse=True)
    
    # Build response with patient and doctor names
    response_records = []
    for record in latest_records:
        # Check integrity and flag if tampered
        is_tampered = check_and_flag_tampering(db, record.id)
        
        # Get patient name
        patient_user = db.query(User).filter(User.id == patient.user_id).first()
        patient_name = patient_user.name if patient_user else None
        
        # Get doctor name
        doctor = db.query(Doctor).filter(Doctor.id == record.doctor_id).first()
        doctor_user = db.query(User).filter(User.id == doctor.user_id).first() if doctor else None
        doctor_name = doctor_user.name if doctor_user else None
        
        # Create response object with tampering status
        record_dict = {
            "id": record.id,
            "patient_id": record.patient_id,
            "patient_name": patient_name,
            "doctor_id": record.doctor_id,
            "doctor_name": doctor_name,
            "appointment_id": record.appointment_id,
            "consultation_notes": record.consultation_notes,
            "diagnosis": record.diagnosis,
            "prescription": record.prescription,
            "version_number": record.version_number,
            "parent_record_id": record.parent_record_id,
            "created_by": record.created_by,
            "created_at": record.created_at,
            "is_tampered": is_tampered
        }
        response_records.append(record_dict)
    
    logger.info(f"Returning {len(response_records)} medical records for patient {patient_id}")
    return response_records


@router.get("/me", response_model=List[MedicalRecordResponse])
async def get_my_medical_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get medical records for the current authenticated user.
    
    This is a convenience endpoint for patients to get their own records
    without needing to know their patient ID.
    
    **Required Role:** Patient
    **Authorization:** Returns only the current user's records
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of medical records for the current user (latest versions only, sorted by date)
        
    Raises:
        HTTPException 403: If user is not a patient
        HTTPException 404: If patient record not found
    """
    logger.info(f"User {current_user.id} requesting their own medical records")
    
    # Only patients can use this endpoint
    if current_user.role != UserRole.PATIENT:
        logger.warning(f"Non-patient user {current_user.id} attempted to use /me endpoint")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available for patients"
        )
    
    # Get patient record for current user
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        logger.error(f"Patient record not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient record not found"
        )
    
    # Reuse the existing logic by calling get_patient_records
    return await get_patient_records(patient.id, db, current_user)


@router.post("/consultation-notes", response_model=ConsultationNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_consultation_note(
    note_data: ConsultationNoteCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Create a new consultation note (Doctor only).
    
    Creates a medical record entry with consultation notes linked to an appointment.
    Only the doctor assigned to the appointment can create notes for it.
    
    **Required Role:** Doctor
    **Authorization:** Doctor must be assigned to the appointment
    
    Args:
        note_data: Consultation note data (appointment_id, consultation_notes, diagnosis)
        db: Database session
        current_user: Current authenticated doctor
        
    Returns:
        Created consultation note record
        
    Raises:
        HTTPException 404: If appointment not found
        HTTPException 403: If doctor not authorized for this appointment
        HTTPException 400: If appointment already has consultation notes
    """
    logger.info(f"Doctor {current_user.id} creating consultation note for appointment {note_data.appointment_id}")
    
    # Get the doctor record for the current user
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        logger.error(f"Doctor record not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor record not found"
        )
    
    # Verify appointment exists
    appointment = db.query(Appointment).filter(Appointment.id == note_data.appointment_id).first()
    if not appointment:
        logger.warning(f"Appointment {note_data.appointment_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Verify the appointment belongs to this doctor
    if appointment.doctor_id != doctor.id:
        logger.warning(
            f"Doctor {doctor.id} attempted to create note for appointment {appointment.id} "
            f"belonging to doctor {appointment.doctor_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to create notes for this appointment"
        )
    
    # Check if consultation note already exists for this appointment
    existing_record = db.query(MedicalRecord).filter(
        MedicalRecord.appointment_id == note_data.appointment_id
    ).first()
    if existing_record:
        logger.warning(f"Consultation note already exists for appointment {note_data.appointment_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consultation note already exists for this appointment. Use update endpoint to modify."
        )
    
    # Create medical record
    medical_record = MedicalRecord(
        patient_id=appointment.patient_id,
        doctor_id=doctor.id,
        appointment_id=appointment.id,
        consultation_notes=note_data.consultation_notes,
        diagnosis=note_data.diagnosis,
        version_number=1,
        created_by=current_user.id
    )
    
    try:
        db.add(medical_record)
        db.flush()  # Flush to get the ID without committing
        
        # Create audit chain entry in the same transaction
        audit_entry = create_medical_record_audit_entry(db, medical_record, current_user.id)

        db.commit()
        db.refresh(medical_record)
        background_tasks.add_task(_trigger_anomaly_check, db, current_user.id, audit_entry.id)
        logger.info(f"Created consultation note {medical_record.id} for appointment {appointment.id}")
        return medical_record
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating consultation note: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create consultation note"
        )


@router.post("/prescriptions", response_model=ConsultationNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_prescription(
    prescription_data: PrescriptionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Create a new prescription (Doctor only).
    
    Creates a medical record entry with prescription details linked to an appointment.
    Only the doctor assigned to the appointment can create prescriptions for it.
    
    **Required Role:** Doctor
    **Authorization:** Doctor must be assigned to the appointment
    
    Args:
        prescription_data: Prescription data (appointment_id, medication, dosage, frequency, duration)
        db: Database session
        current_user: Current authenticated doctor
        
    Returns:
        Created medical record with prescription
        
    Raises:
        HTTPException 404: If appointment not found
        HTTPException 403: If doctor not authorized for this appointment
        HTTPException 400: If appointment already has a medical record
    """
    logger.info(f"Doctor {current_user.id} creating prescription for appointment {prescription_data.appointment_id}")
    
    # Get the doctor record for the current user
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        logger.error(f"Doctor record not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor record not found"
        )
    
    # Verify appointment exists
    appointment = db.query(Appointment).filter(Appointment.id == prescription_data.appointment_id).first()
    if not appointment:
        logger.warning(f"Appointment {prescription_data.appointment_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Verify the appointment belongs to this doctor
    if appointment.doctor_id != doctor.id:
        logger.warning(
            f"Doctor {doctor.id} attempted to create prescription for appointment {appointment.id} "
            f"belonging to doctor {appointment.doctor_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to create prescriptions for this appointment"
        )
    
    # Check if medical record already exists for this appointment
    existing_record = db.query(MedicalRecord).filter(
        MedicalRecord.appointment_id == prescription_data.appointment_id
    ).first()
    if existing_record:
        logger.warning(f"Medical record already exists for appointment {prescription_data.appointment_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Medical record already exists for this appointment. Use update endpoint to modify."
        )
    
    # Format prescription as structured text
    prescription_text = (
        f"Medication: {prescription_data.medication}\n"
        f"Dosage: {prescription_data.dosage}\n"
        f"Frequency: {prescription_data.frequency}\n"
        f"Duration: {prescription_data.duration}"
    )
    
    # Create medical record with prescription
    medical_record = MedicalRecord(
        patient_id=appointment.patient_id,
        doctor_id=doctor.id,
        appointment_id=appointment.id,
        prescription=prescription_text,
        version_number=1,
        created_by=current_user.id
    )
    
    try:
        db.add(medical_record)
        db.flush()  # Flush to get the ID without committing
        
        # Create audit chain entry in the same transaction
        audit_entry = create_medical_record_audit_entry(db, medical_record, current_user.id)

        db.commit()
        db.refresh(medical_record)
        background_tasks.add_task(_trigger_anomaly_check, db, current_user.id, audit_entry.id)
        logger.info(f"Created prescription {medical_record.id} for appointment {appointment.id}")
        return medical_record
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating prescription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create prescription"
        )


@router.post("/", response_model=ConsultationNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_medical_record(
    record_data: MedicalRecordCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Create a complete medical record with notes, diagnosis, and prescription (Doctor only).

    Combines consultation notes and prescription into a single record linked to an
    appointment. An audit-chain entry with a SHA-256 hash is created atomically in
    the same transaction.

    Use this endpoint when you want to record all clinical details in one call.
    For updating an existing record use PUT /consultation-notes/{record_id}.

    **Required Role:** Doctor
    **Authorization:** Doctor must be assigned to the appointment
    **Validates:** Requirements 8.1, 8.2 (medical record creation with blockchain hash)
    """
    logger.info(
        f"Doctor {current_user.id} creating medical record for appointment {record_data.appointment_id}"
    )

    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        logger.error(f"Doctor record not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor record not found"
        )

    appointment = db.query(Appointment).filter(Appointment.id == record_data.appointment_id).first()
    if not appointment:
        logger.warning(f"Appointment {record_data.appointment_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    if appointment.doctor_id != doctor.id:
        logger.warning(
            f"Doctor {doctor.id} attempted to create record for appointment {appointment.id} "
            f"belonging to doctor {appointment.doctor_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to create records for this appointment"
        )

    existing = db.query(MedicalRecord).filter(
        MedicalRecord.appointment_id == record_data.appointment_id
    ).first()
    if existing:
        logger.warning(f"Medical record already exists for appointment {record_data.appointment_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A medical record already exists for this appointment. "
                   "Use PUT /consultation-notes/{record_id} to update it."
        )

    medical_record = MedicalRecord(
        patient_id=appointment.patient_id,
        doctor_id=doctor.id,
        appointment_id=appointment.id,
        consultation_notes=record_data.consultation_notes,
        diagnosis=record_data.diagnosis,
        prescription=record_data.prescription,
        version_number=1,
        created_by=current_user.id,
    )

    try:
        db.add(medical_record)
        db.flush()

        audit_entry = create_medical_record_audit_entry(db, medical_record, current_user.id)

        db.commit()
        db.refresh(medical_record)
        background_tasks.add_task(_trigger_anomaly_check, db, current_user.id, audit_entry.id)
        logger.info(
            f"Created medical record {medical_record.id} for appointment {appointment.id}"
        )
        return medical_record
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating medical record: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create medical record"
        )


@router.put("/consultation-notes/{record_id}", response_model=ConsultationNoteResponse)
async def update_consultation_note(
    record_id: int,
    update_data: MedicalRecordUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Update a consultation note (Doctor only).
    
    Creates a new version of the medical record with incremented version_number.
    The original record is preserved and linked via parent_record_id.
    
    **Required Role:** Doctor
    **Authorization:** Only the doctor who created the original record can update it
    
    Args:
        record_id: ID of the medical record to update
        update_data: Updated consultation notes and/or diagnosis
        db: Database session
        current_user: Current authenticated doctor
        
    Returns:
        New version of the medical record
        
    Raises:
        HTTPException 404: If record not found
        HTTPException 403: If doctor didn't create the original record
        HTTPException 400: If no fields provided for update
    """
    logger.info(f"Doctor {current_user.id} updating consultation note {record_id}")
    
    # Get the doctor record for the current user
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        logger.error(f"Doctor record not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor record not found"
        )
    
    # Fetch the original record
    original_record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if not original_record:
        logger.warning(f"Medical record {record_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical record not found"
        )
    
    # Verify the doctor owns this record
    if original_record.doctor_id != doctor.id:
        logger.warning(
            f"Doctor {doctor.id} attempted to update record {record_id} "
            f"belonging to doctor {original_record.doctor_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this record"
        )
    
    # Validate that at least one field is being updated
    if not any([
        update_data.consultation_notes is not None,
        update_data.diagnosis is not None,
        update_data.prescription is not None
    ]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided for update"
        )
    
    # Create new version of the record
    new_version = MedicalRecord(
        patient_id=original_record.patient_id,
        doctor_id=original_record.doctor_id,
        appointment_id=original_record.appointment_id,
        consultation_notes=update_data.consultation_notes if update_data.consultation_notes is not None else original_record.consultation_notes,
        diagnosis=update_data.diagnosis if update_data.diagnosis is not None else original_record.diagnosis,
        prescription=update_data.prescription if update_data.prescription is not None else original_record.prescription,
        version_number=original_record.version_number + 1,
        parent_record_id=record_id,
        created_by=current_user.id
    )
    
    try:
        db.add(new_version)
        db.flush()  # Flush to get the ID without committing
        
        # Create audit chain entry in the same transaction
        audit_entry = create_medical_record_audit_entry(db, new_version, current_user.id)

        db.commit()
        db.refresh(new_version)
        background_tasks.add_task(_trigger_anomaly_check, db, current_user.id, audit_entry.id)
        logger.info(
            f"Created new version {new_version.id} (v{new_version.version_number}) "
            f"for record {record_id}"
        )
        return new_version
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating consultation note: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update consultation note"
        )


@router.put("/prescriptions/{record_id}", response_model=ConsultationNoteResponse)
async def update_prescription(
    record_id: int,
    update_data: PrescriptionUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Update a prescription (Doctor only).
    
    Creates a new version of the medical record with updated prescription.
    The original record is preserved and linked via parent_record_id.
    
    **Required Role:** Doctor
    **Authorization:** Only the doctor who created the original record can update it
    
    Args:
        record_id: ID of the medical record to update
        update_data: Updated prescription fields (medication, dosage, frequency, duration)
        db: Database session
        current_user: Current authenticated doctor
        
    Returns:
        New version of the medical record with updated prescription
        
    Raises:
        HTTPException 404: If record not found
        HTTPException 403: If doctor didn't create the original record
    """
    logger.info(f"Doctor {current_user.id} updating prescription {record_id}")
    
    # Get the doctor record for the current user
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        logger.error(f"Doctor record not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor record not found"
        )
    
    # Fetch the original record
    original_record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if not original_record:
        logger.warning(f"Medical record {record_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical record not found"
        )
    
    # Verify the doctor owns this record
    if original_record.doctor_id != doctor.id:
        logger.warning(
            f"Doctor {doctor.id} attempted to update record {record_id} "
            f"belonging to doctor {original_record.doctor_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this record"
        )
    
    # Format updated prescription as structured text
    prescription_text = (
        f"Medication: {update_data.medication}\n"
        f"Dosage: {update_data.dosage}\n"
        f"Frequency: {update_data.frequency}\n"
        f"Duration: {update_data.duration}"
    )
    
    # Create new version of the record
    new_version = MedicalRecord(
        patient_id=original_record.patient_id,
        doctor_id=original_record.doctor_id,
        appointment_id=original_record.appointment_id,
        consultation_notes=original_record.consultation_notes,
        diagnosis=original_record.diagnosis,
        prescription=prescription_text,
        version_number=original_record.version_number + 1,
        parent_record_id=record_id,
        created_by=current_user.id
    )
    
    try:
        db.add(new_version)
        db.flush()  # Flush to get the ID without committing
        
        # Create audit chain entry in the same transaction
        audit_entry = create_medical_record_audit_entry(db, new_version, current_user.id)

        db.commit()
        db.refresh(new_version)
        background_tasks.add_task(_trigger_anomaly_check, db, current_user.id, audit_entry.id)
        logger.info(
            f"Created new version {new_version.id} (v{new_version.version_number}) "
            f"for prescription {record_id}"
        )
        return new_version
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating prescription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update prescription"
        )


@router.get("/{record_id}/versions", response_model=List[dict])
async def get_record_versions(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get version history of a medical record.
    
    Returns all versions of a record (all records with same appointment_id or linked via parent_record_id).
    Sorted by version_number (ascending - oldest first).
    
    **Required Role:** Any authenticated user
    **Authorization:** Same access rules as viewing records
    - Patients can view versions of their own records
    - Doctors can view versions of records for patients they've treated
    - Admins can view all versions
    
    Args:
        record_id: ID of any version of the medical record
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of all versions of the medical record with version_number, created_at, created_by (user name)
        
    Raises:
        HTTPException 404: If record not found
        HTTPException 403: If user not authorized to view record
    """
    logger.info(f"User {current_user.id} requesting version history for record {record_id}")
    
    # Fetch the specified record
    record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if not record:
        logger.warning(f"Medical record {record_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical record not found"
        )
    
    # Authorization check based on user role
    patient_id = record.patient_id
    
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        logger.warning(f"Patient {patient_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    if current_user.role == UserRole.PATIENT:
        # Patients can only view their own records
        user_patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not user_patient or user_patient.id != patient_id:
            logger.warning(
                f"Patient user {current_user.id} attempted to access record versions for patient {patient_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own medical records"
            )
    
    elif current_user.role == UserRole.DOCTOR:
        # Doctors can view records of patients they have treated
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor:
            logger.error(f"Doctor record not found for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor record not found"
            )
        
        # Check if doctor has treated this patient
        has_treated = db.query(MedicalRecord).filter(
            MedicalRecord.patient_id == patient_id,
            MedicalRecord.doctor_id == doctor.id
        ).first() is not None
        
        if not has_treated:
            logger.warning(
                f"Doctor {doctor.id} attempted to access record versions for patient {patient_id} "
                f"they have not treated"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view records of patients you have treated"
            )
    
    elif current_user.role == UserRole.ADMIN:
        # Admins can view all records
        pass
    
    else:
        # Nurses and other roles cannot view medical records
        logger.warning(f"User {current_user.id} with role {current_user.role} attempted to view record versions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view medical records"
        )
    
    # Get all versions of this record
    # Strategy: Find all records with the same appointment_id or linked via parent_record_id chain
    all_versions = []
    
    if record.appointment_id:
        # Get all records with the same appointment_id
        all_versions = db.query(MedicalRecord).filter(
            MedicalRecord.appointment_id == record.appointment_id
        ).order_by(MedicalRecord.version_number).all()
    else:
        # For records without appointment_id, traverse the version chain
        # Find the root record (version 1)
        root_record = record
        while root_record.parent_record_id:
            root_record = db.query(MedicalRecord).filter(
                MedicalRecord.id == root_record.parent_record_id
            ).first()
            if not root_record:
                break
        
        # Collect all versions starting from root
        if root_record:
            all_versions = [root_record]
            current_id = root_record.id
            
            # Traverse forward through child records
            while True:
                child = db.query(MedicalRecord).filter(
                    MedicalRecord.parent_record_id == current_id
                ).first()
                if not child:
                    break
                all_versions.append(child)
                current_id = child.id
    
    # Build response with version details
    response_versions = []
    for version in all_versions:
        # Check integrity and flag if tampered
        is_tampered = check_and_flag_tampering(db, version.id)
        
        # Get creator name
        creator = db.query(User).filter(User.id == version.created_by).first()
        creator_name = creator.name if creator else None
        
        # Get patient name
        patient_user = db.query(User).filter(User.id == patient.user_id).first()
        patient_name = patient_user.name if patient_user else None
        
        # Get doctor name
        doctor = db.query(Doctor).filter(Doctor.id == version.doctor_id).first()
        doctor_user = db.query(User).filter(User.id == doctor.user_id).first() if doctor else None
        doctor_name = doctor_user.name if doctor_user else None
        
        version_dict = {
            "id": version.id,
            "patient_id": version.patient_id,
            "patient_name": patient_name,
            "doctor_id": version.doctor_id,
            "doctor_name": doctor_name,
            "appointment_id": version.appointment_id,
            "consultation_notes": version.consultation_notes,
            "diagnosis": version.diagnosis,
            "prescription": version.prescription,
            "version_number": version.version_number,
            "parent_record_id": version.parent_record_id,
            "created_by": version.created_by,
            "created_by_name": creator_name,
            "created_at": version.created_at,
            "is_tampered": is_tampered
        }
        response_versions.append(version_dict)
    
    logger.info(f"Returning {len(response_versions)} versions for record {record_id}")
    return response_versions
