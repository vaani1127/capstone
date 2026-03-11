"""
Appointment management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.appointment import AppointmentStatus
from app.core.dependencies import get_current_user, require_staff, require_patient, require_role
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentWithDetails,
    RescheduleRequest,
    WalkInCreate,
    StatusUpdateRequest
)
from app.services.appointment_service import AppointmentService

router = APIRouter()


@router.get("/", response_model=List[AppointmentWithDetails])
async def list_appointments(
    patient_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List appointments with role-based filtering.
    
    - Patients see only their own appointments
    - Doctors see only appointments assigned to them
    - Nurses and Admins can see all appointments (with optional filters)
    
    **Required Role:** Any authenticated user
    **Authorization:** Role-based filtering applied
    **Validates:** Requirements 5.2 (appointment listing with filters)
    
    Query Parameters:
        patient_id: Filter by patient ID (Admin/Nurse only)
        doctor_id: Filter by doctor ID (Admin/Nurse only)
        status: Filter by status (scheduled, checked_in, in_progress, completed, cancelled)
        start_date: Filter by start date (ISO format)
        end_date: Filter by end date (ISO format)
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of appointments with patient and doctor details
        
    Raises:
        403: If patient/doctor tries to access other users' appointments
    """
    # Convert status string to enum if provided
    status_enum = None
    if status:
        try:
            status_enum = AppointmentStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status value. Must be one of: {[s.value for s in AppointmentStatus]}"
            )
    
    # Apply role-based filtering
    if current_user.role == UserRole.PATIENT:
        # Patients can only see their own appointments
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient record not found for current user"
            )
        
        # Override any provided patient_id filter
        filter_patient_id = patient.id
        filter_doctor_id = None  # Patients can't filter by doctor
        
    elif current_user.role == UserRole.DOCTOR:
        # Doctors can only see appointments assigned to them
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor record not found for current user"
            )
        
        # Override any provided doctor_id filter
        filter_patient_id = None  # Doctors can't filter by patient
        filter_doctor_id = doctor.id
        
    else:
        # Admin and Nurse can see all appointments with optional filters
        filter_patient_id = patient_id
        filter_doctor_id = doctor_id
    
    # Get appointments using service
    appointments = AppointmentService.list_appointments(
        db=db,
        patient_id=filter_patient_id,
        doctor_id=filter_doctor_id,
        status=status_enum,
        start_date=start_date,
        end_date=end_date
    )
    
    # Build response with details
    response_list = []
    for appointment in appointments:
        # Get patient and doctor details
        patient_record = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
        doctor_record = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
        
        patient_name = None
        if patient_record and patient_record.user:
            patient_name = patient_record.user.name
        
        doctor_name = None
        doctor_specialization = None
        if doctor_record:
            if doctor_record.user:
                doctor_name = doctor_record.user.name
            doctor_specialization = doctor_record.specialization
        
        # Calculate estimated wait time
        estimated_wait_time = None
        if appointment.queue_position and appointment.status in [
            AppointmentStatus.SCHEDULED,
            AppointmentStatus.CHECKED_IN
        ]:
            estimated_wait_time = AppointmentService.calculate_estimated_wait_time(
                db=db,
                doctor_id=appointment.doctor_id,
                queue_position=appointment.queue_position
            )
        
        response_list.append(AppointmentWithDetails(
            id=appointment.id,
            patient_id=appointment.patient_id,
            doctor_id=appointment.doctor_id,
            scheduled_time=appointment.scheduled_time,
            status=appointment.status,
            appointment_type=appointment.appointment_type,
            queue_position=appointment.queue_position,
            created_at=appointment.created_at,
            updated_at=appointment.updated_at,
            patient_name=patient_name,
            doctor_name=doctor_name,
            doctor_specialization=doctor_specialization,
            estimated_wait_time=estimated_wait_time
        ))
    
    return response_list


@router.post("/", response_model=AppointmentWithDetails, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient)
):
    """
    Book a new appointment (Patient only).
    
    Validates:
    - Doctor availability at requested time
    - Prevents double-booking
    - Assigns queue position
    - Returns confirmation with estimated wait time
    
    **Required Role:** Patient
    **Validates:** Requirements 3.3, 3.4, 3.5
    
    Args:
        appointment_data: Appointment creation data (doctor_id, scheduled_time)
        db: Database session
        current_user: Current authenticated patient
        
    Returns:
        Created appointment details with queue position and estimated wait time
        
    Raises:
        404: Doctor or patient not found
        409: Doctor not available at requested time (double-booking prevented)
    """
    # Get patient record for current user
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient record not found for current user"
        )
    
    # Create appointment using service
    appointment = AppointmentService.create_appointment(
        db=db,
        patient_id=patient.id,
        appointment_data=appointment_data
    )
    
    # Get doctor details
    doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
    
    # Calculate estimated wait time
    estimated_wait_time = AppointmentService.calculate_estimated_wait_time(
        db=db,
        doctor_id=appointment.doctor_id,
        queue_position=appointment.queue_position
    )
    
    # Build response with details
    response = AppointmentWithDetails(
        id=appointment.id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        scheduled_time=appointment.scheduled_time,
        status=appointment.status,
        appointment_type=appointment.appointment_type,
        queue_position=appointment.queue_position,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at,
        patient_name=current_user.name,
        doctor_name=doctor.user.name if doctor and doctor.user else None,
        doctor_specialization=doctor.specialization if doctor else None,
        estimated_wait_time=estimated_wait_time
    )
    
    return response


@router.put("/{appointment_id}/reschedule", response_model=AppointmentWithDetails)
async def reschedule_appointment(
    appointment_id: int,
    reschedule_data: RescheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reschedule an appointment to a new time.
    
    Validates:
    - Appointment exists
    - User has permission (patient owns it or staff can reschedule any)
    - New time slot is available (no double-booking)
    - Updates scheduled_time and recalculates queue_position
    
    **Required Role:** Any authenticated user
    **Authorization:** Ownership or staff role verified
    **Validates:** Requirements 6.2 (reschedule to available time slots)
    
    Args:
        appointment_id: ID of appointment to reschedule
        reschedule_data: New scheduled time
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated appointment details with new queue position and estimated wait time
        
    Raises:
        404: Appointment not found
        403: User not authorized to reschedule this appointment
        400: Appointment already cancelled or completed
        409: Doctor not available at requested time (double-booking prevented)
    """
    # Reschedule appointment using service
    appointment = AppointmentService.reschedule_appointment(
        db=db,
        appointment_id=appointment_id,
        new_scheduled_time=reschedule_data.new_scheduled_time,
        user_id=current_user.id,
        user_role=current_user.role.value
    )
    
    # Get patient and doctor details
    patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
    doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
    
    patient_name = None
    if patient and patient.user:
        patient_name = patient.user.name
    
    doctor_name = None
    doctor_specialization = None
    if doctor:
        if doctor.user:
            doctor_name = doctor.user.name
        doctor_specialization = doctor.specialization
    
    # Calculate estimated wait time
    estimated_wait_time = AppointmentService.calculate_estimated_wait_time(
        db=db,
        doctor_id=appointment.doctor_id,
        queue_position=appointment.queue_position
    )
    
    # Build response with details
    response = AppointmentWithDetails(
        id=appointment.id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        scheduled_time=appointment.scheduled_time,
        status=appointment.status,
        appointment_type=appointment.appointment_type,
        queue_position=appointment.queue_position,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at,
        patient_name=patient_name,
        doctor_name=doctor_name,
        doctor_specialization=doctor_specialization,
        estimated_wait_time=estimated_wait_time
    )
    
    return response


@router.put("/{appointment_id}", response_model=dict)
async def update_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update appointment (reschedule or change status).
    
    - Patients can reschedule their own appointments
    - Staff can update appointment status
    
    **Required Role:** Any authenticated user
    **Authorization:** Ownership or staff role verified
    
    Args:
        appointment_id: ID of appointment to update
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated appointment details
    """
    # TODO: Implement appointment update logic with ownership check
    return {}


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel an appointment.
    
    Validates:
    - Appointment exists
    - User has permission (patient owns it or staff can cancel any)
    - 2-hour cancellation rule (appointments can only be cancelled if scheduled time is at least 2 hours away)
    - Updates queue positions for remaining appointments
    
    **Required Role:** Any authenticated user
    **Authorization:** Ownership or staff role verified
    **Validates:** Requirements 6.1, 6.3 (cancellation with 2-hour rule and queue updates)
    
    Args:
        appointment_id: ID of appointment to cancel
        db: Database session
        current_user: Current authenticated user
        
    Raises:
        404: Appointment not found
        403: User not authorized to cancel this appointment
        400: Appointment already cancelled or within 2-hour window
    """
    # Cancel appointment using service
    AppointmentService.cancel_appointment(
        db=db,
        appointment_id=appointment_id,
        user_id=current_user.id,
        user_role=current_user.role.value
    )
    
    # Return 204 No Content on success
    return None


@router.patch("/{appointment_id}/status", response_model=AppointmentWithDetails)
async def update_appointment_status(
    appointment_id: int,
    status_data: StatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update appointment status (Doctor/Nurse/Admin only).
    
    Handles status transitions:
    - SCHEDULED → CHECKED_IN (patient arrives)
    - CHECKED_IN → IN_PROGRESS (consultation starts)
    - IN_PROGRESS → COMPLETED (consultation ends)
    
    When status changes to COMPLETED:
    - Clears queue_position
    - Recalculates positions for remaining appointments in queue
    
    **Required Role:** Doctor, Nurse, or Admin
    **Validates:** Requirements 7.2 (queue updates on status changes)
    
    Args:
        appointment_id: ID of appointment to update
        status_data: New status to set
        db: Database session
        current_user: Current authenticated user (must be Doctor/Nurse/Admin)
        
    Returns:
        Updated appointment details with new queue information
        
    Raises:
        404: Appointment not found
        403: User not authorized (not Doctor/Nurse/Admin)
        400: Invalid status transition
    """
    # Update appointment status using service
    appointment = AppointmentService.update_appointment_status(
        db=db,
        appointment_id=appointment_id,
        new_status=status_data.status,
        user_id=current_user.id,
        user_role=current_user.role.value
    )
    
    # Get patient and doctor details
    patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
    doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
    
    patient_name = None
    if patient and patient.user:
        patient_name = patient.user.name
    
    doctor_name = None
    doctor_specialization = None
    if doctor:
        if doctor.user:
            doctor_name = doctor.user.name
        doctor_specialization = doctor.specialization
    
    # Calculate estimated wait time (if still in queue)
    estimated_wait_time = None
    if appointment.queue_position and appointment.status in [
        AppointmentStatus.SCHEDULED,
        AppointmentStatus.CHECKED_IN,
        AppointmentStatus.IN_PROGRESS
    ]:
        estimated_wait_time = AppointmentService.calculate_estimated_wait_time(
            db=db,
            doctor_id=appointment.doctor_id,
            queue_position=appointment.queue_position
        )
    
    # Build response with details
    response = AppointmentWithDetails(
        id=appointment.id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        scheduled_time=appointment.scheduled_time,
        status=appointment.status,
        appointment_type=appointment.appointment_type,
        queue_position=appointment.queue_position,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at,
        patient_name=patient_name,
        doctor_name=doctor_name,
        doctor_specialization=doctor_specialization,
        estimated_wait_time=estimated_wait_time
    )
    
    return response


@router.post("/walk-in", response_model=AppointmentWithDetails, status_code=status.HTTP_201_CREATED)
async def register_walk_in(
    walk_in_data: WalkInCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.NURSE))
):
    """
    Register a walk-in patient and create immediate appointment (Admin/Nurse only).
    
    This endpoint:
    - Checks if patient exists by email or phone
    - Creates User and Patient records if new patient
    - Creates appointment with type WALK_IN and immediate scheduled_time (now)
    - Assigns queue position and returns estimated wait time
    - Only accessible by Admin and Nurse roles
    
    **Required Role:** Admin or Nurse
    **Validates:** Requirements 4.1, 4.2, 4.3, 4.4 (walk-in registration)
    
    Args:
        walk_in_data: Walk-in patient data (doctor_id, patient details)
        db: Database session
        current_user: Current authenticated staff member
        
    Returns:
        Created appointment details with queue position and estimated wait time
        
    Raises:
        404: Doctor not found
        403: User not authorized (not Admin or Nurse)
    """
    # Call service to register walk-in
    appointment, patient, is_new_patient = AppointmentService.register_walk_in(
        db=db,
        doctor_id=walk_in_data.doctor_id,
        patient_name=walk_in_data.patient_name,
        patient_email=walk_in_data.patient_email,
        patient_phone=walk_in_data.patient_phone,
        gender=walk_in_data.gender,
        date_of_birth=walk_in_data.date_of_birth,
        address=walk_in_data.address,
        blood_group=walk_in_data.blood_group
    )
    
    # Get doctor details
    doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
    
    # Calculate estimated wait time
    estimated_wait_time = AppointmentService.calculate_estimated_wait_time(
        db=db,
        doctor_id=appointment.doctor_id,
        queue_position=appointment.queue_position
    )
    
    # Build response with details
    response = AppointmentWithDetails(
        id=appointment.id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        scheduled_time=appointment.scheduled_time,
        status=appointment.status,
        appointment_type=appointment.appointment_type,
        queue_position=appointment.queue_position,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at,
        patient_name=patient.user.name if patient.user else walk_in_data.patient_name,
        doctor_name=doctor.user.name if doctor and doctor.user else None,
        doctor_specialization=doctor.specialization if doctor else None,
        estimated_wait_time=estimated_wait_time
    )
    
    return response

