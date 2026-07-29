"""
Appointment service for business logic
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, text
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import HTTPException, status
import asyncio

from app.models.appointment import Appointment, AppointmentStatus, AppointmentType
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.schemas.appointment import AppointmentCreate
from app.services.blockchain_service import create_audit_entry


class AppointmentService:
    """Service for appointment management operations"""
    
    @staticmethod
    def _broadcast_queue_update(db: Session, doctor_id: int):
        """
        Helper method to broadcast queue updates via WebSocket.
        
        This method fetches the current queue status and broadcasts it
        to all connected clients asynchronously.
        
        Args:
            db: Database session
            doctor_id: ID of the doctor whose queue was updated
        """
        try:
            from app.services.websocket_manager import manager
            
            # Get current queue data
            queue_data = AppointmentService.get_doctor_queue(db, doctor_id)
            
            # Create a new event loop if needed and broadcast
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run the broadcast in the event loop
            if loop.is_running():
                # If loop is already running, create a task
                asyncio.create_task(manager.broadcast_queue_update(doctor_id, queue_data))
            else:
                # If loop is not running, run until complete
                loop.run_until_complete(manager.broadcast_queue_update(doctor_id, queue_data))
        except Exception as e:
            # Log error but don't fail the operation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to broadcast queue update for doctor_id={doctor_id}: {e}")
    
    @staticmethod
    def _send_appointment_notification(
        db: Session,
        appointment: Appointment,
        notification_type: str,
        message: str
    ):
        """
        Helper method to send appointment notifications via WebSocket.
        
        Sends targeted notifications to the patient and doctor involved
        in the appointment with full appointment details.
        
        Args:
            db: Database session
            appointment: Appointment object
            notification_type: Type of notification (appointment_created, status_changed, cancelled, rescheduled)
            message: Human-readable notification message
        """
        try:
            from app.services.websocket_manager import manager
            from app.models.user import User
            
            # Get patient and doctor user IDs
            patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
            doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
            
            if not patient or not doctor:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Cannot send notification: patient or doctor not found for appointment_id={appointment.id}")
                return
            
            # Get user info for names
            patient_user = db.query(User).filter(User.id == patient.user_id).first()
            doctor_user = db.query(User).filter(User.id == doctor.user_id).first()
            
            if not patient_user or not doctor_user:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Cannot send notification: user info not found for appointment_id={appointment.id}")
                return
            
            # Calculate estimated wait time
            estimated_wait_time = 0
            if appointment.queue_position:
                estimated_wait_time = AppointmentService.calculate_estimated_wait_time(
                    db=db,
                    doctor_id=appointment.doctor_id,
                    queue_position=appointment.queue_position
                )
            
            # Build appointment data
            appointment_data = {
                "id": appointment.id,
                "patient_id": appointment.patient_id,
                "doctor_id": appointment.doctor_id,
                "scheduled_time": appointment.scheduled_time.isoformat(),
                "status": appointment.status.value,
                "patient_name": patient_user.name,
                "doctor_name": doctor_user.name,
                "queue_position": appointment.queue_position,
                "estimated_wait_time": estimated_wait_time
            }
            
            # Create a new event loop if needed and send notification
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run the notification in the event loop
            if loop.is_running():
                # If loop is already running, create a task
                asyncio.create_task(manager.send_appointment_notification(
                    notification_type=notification_type,
                    appointment_data=appointment_data,
                    patient_user_id=patient.user_id,
                    doctor_user_id=doctor.user_id,
                    message=message
                ))
            else:
                # If loop is not running, run until complete
                loop.run_until_complete(manager.send_appointment_notification(
                    notification_type=notification_type,
                    appointment_data=appointment_data,
                    patient_user_id=patient.user_id,
                    doctor_user_id=doctor.user_id,
                    message=message
                ))
        except Exception as e:
            # Log error but don't fail the operation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send appointment notification for appointment_id={appointment.id}: {e}")
    
    @staticmethod
    def check_doctor_availability(
        db: Session,
        doctor_id: int,
        scheduled_time: datetime,
        exclude_appointment_id: Optional[int] = None
    ) -> bool:
        """
        Check if a doctor is available at the specified time.
        
        Args:
            db: Database session
            doctor_id: ID of the doctor
            scheduled_time: Requested appointment time
            exclude_appointment_id: Appointment ID to exclude (for rescheduling)
            
        Returns:
            True if doctor is available, False otherwise
        """
        # Check if doctor exists
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor with ID {doctor_id} not found"
            )
        
        # Get average consultation duration
        avg_duration = doctor.average_consultation_duration
        
        # Define time window (scheduled_time ± avg_duration)
        time_window_start = scheduled_time - timedelta(minutes=avg_duration)
        time_window_end = scheduled_time + timedelta(minutes=avg_duration)
        
        # Check for overlapping appointments
        query = db.query(Appointment).filter(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.status.in_([
                    AppointmentStatus.SCHEDULED,
                    AppointmentStatus.CHECKED_IN,
                    AppointmentStatus.IN_PROGRESS
                ]),
                Appointment.scheduled_time >= time_window_start,
                Appointment.scheduled_time <= time_window_end
            )
        )
        
        # Exclude specific appointment if provided (for rescheduling)
        if exclude_appointment_id:
            query = query.filter(Appointment.id != exclude_appointment_id)
        
        conflicting_appointment = query.first()
        
        return conflicting_appointment is None
    
    @staticmethod
    def get_next_queue_position(db: Session, doctor_id: int) -> int:
        """
        Get the next available queue position for a doctor.
        
        Args:
            db: Database session
            doctor_id: ID of the doctor
            
        Returns:
            Next queue position number
        """
        max_position = db.query(func.max(Appointment.queue_position)).filter(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.status.in_([
                    AppointmentStatus.SCHEDULED,
                    AppointmentStatus.CHECKED_IN,
                    AppointmentStatus.IN_PROGRESS
                ])
            )
        ).scalar()
        
        return (max_position or 0) + 1
    
    @staticmethod
    def create_appointment(
        db: Session,
        patient_id: int,
        appointment_data: AppointmentCreate,
        appointment_type: AppointmentType = AppointmentType.SCHEDULED
    ) -> Appointment:
        """
        Create a new appointment with validation.
        
        Args:
            db: Database session
            patient_id: ID of the patient
            appointment_data: Appointment creation data
            appointment_type: Type of appointment (scheduled or walk-in)
            
        Returns:
            Created appointment
            
        Raises:
            HTTPException: If validation fails
        """
        # Validate patient exists
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID {patient_id} not found"
            )

        # Validate appointment is in the future
        if appointment_data.scheduled_time <= datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Appointment must be scheduled in the future"
            )

        # Check doctor availability
        is_available = AppointmentService.check_doctor_availability(
            db=db,
            doctor_id=appointment_data.doctor_id,
            scheduled_time=appointment_data.scheduled_time
        )
        
        if not is_available:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Doctor is not available at the requested time. Please choose another time slot."
            )
        
        # Get next queue position
        queue_position = AppointmentService.get_next_queue_position(
            db=db,
            doctor_id=appointment_data.doctor_id
        )
        
        # Create appointment
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=appointment_data.doctor_id,
            scheduled_time=appointment_data.scheduled_time,
            status=AppointmentStatus.SCHEDULED,
            appointment_type=appointment_type,
            queue_position=queue_position
        )
        
        db.add(appointment)
        db.commit()
        db.refresh(appointment)

        # Audit chain entry for appointment creation
        create_audit_entry(
            db, appointment.id, "appointment_created",
            {
                "patient_id": appointment.patient_id,
                "doctor_id": appointment.doctor_id,
                "scheduled_time": appointment.scheduled_time.isoformat(),
                "queue_position": appointment.queue_position,
                "appointment_type": appointment.appointment_type.value,
                "status": appointment.status.value,
            },
            patient.user_id
        )
        db.commit()

        # Broadcast queue update
        AppointmentService._broadcast_queue_update(db, appointment_data.doctor_id)

        # Send appointment notification to patient and doctor
        AppointmentService._send_appointment_notification(
            db=db,
            appointment=appointment,
            notification_type="appointment_created",
            message="Your appointment has been created"
        )

        return appointment

    @staticmethod
    def calculate_estimated_wait_time(
        db: Session,
        doctor_id: int,
        queue_position: int
    ) -> int:
        """
        Calculate estimated waiting time for a patient in queue.
        
        Args:
            db: Database session
            doctor_id: ID of the doctor
            queue_position: Patient's position in queue
            
        Returns:
            Estimated wait time in minutes
        """
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            return 0
        
        # Estimated wait time = (queue_position - 1) * average_consultation_duration
        # Subtract 1 because position 1 means patient is next (no wait)
        wait_time = max(0, (queue_position - 1) * doctor.average_consultation_duration)
        
        return wait_time
    
    @staticmethod
    def list_appointments(
        db: Session,
        patient_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
        status: Optional[AppointmentStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Appointment]:
        """
        List appointments with optional filtering.
        
        Args:
            db: Database session
            patient_id: Filter by patient ID
            doctor_id: Filter by doctor ID
            status: Filter by appointment status
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)
            
        Returns:
            List of appointments sorted by scheduled_time
        """
        query = db.query(Appointment)
        
        # Apply filters
        if patient_id is not None:
            query = query.filter(Appointment.patient_id == patient_id)
        
        if doctor_id is not None:
            query = query.filter(Appointment.doctor_id == doctor_id)
        
        if status is not None:
            query = query.filter(Appointment.status == status)
        
        if start_date is not None:
            query = query.filter(Appointment.scheduled_time >= start_date)
        
        if end_date is not None:
            query = query.filter(Appointment.scheduled_time <= end_date)
        
        # Sort by scheduled time (ascending)
        query = query.order_by(Appointment.scheduled_time.asc())
        
        return query.all()
    
    @staticmethod
    def cancel_appointment(
        db: Session,
        appointment_id: int,
        user_id: int,
        user_role: str
    ) -> Appointment:
        """
        Cancel an appointment with validation.
        
        Validates:
        - Appointment exists
        - User has permission (patient owns it or staff)
        - 2-hour cancellation rule (appointments can only be cancelled if scheduled time is at least 2 hours away)
        - Updates queue positions for remaining appointments
        
        Args:
            db: Database session
            appointment_id: ID of appointment to cancel
            user_id: ID of user requesting cancellation
            user_role: Role of user (Patient, Doctor, Nurse, Admin)
            
        Returns:
            Cancelled appointment
            
        Raises:
            HTTPException: If validation fails
        """
        from app.models.user import UserRole
        
        # Get appointment
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment with ID {appointment_id} not found"
            )
        
        # Check if already cancelled
        if appointment.status == AppointmentStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Appointment is already cancelled"
            )
        
        # Check authorization
        if user_role == UserRole.PATIENT.value:
            # Patients can only cancel their own appointments
            patient = db.query(Patient).filter(Patient.user_id == user_id).first()
            if not patient or appointment.patient_id != patient.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only cancel your own appointments"
                )
        # Staff (Admin, Doctor, Nurse) can cancel any appointment - no additional check needed
        
        # Check 2-hour cancellation rule
        time_until_appointment = appointment.scheduled_time - datetime.utcnow()
        if time_until_appointment < timedelta(hours=2):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Appointments can only be cancelled at least 2 hours before the scheduled time"
            )

        # Store doctor_id and queue_position before cancellation
        doctor_id = appointment.doctor_id
        cancelled_queue_position = appointment.queue_position
        was_in_progress = appointment.status == AppointmentStatus.IN_PROGRESS

        # Update appointment status
        appointment.status = AppointmentStatus.CANCELLED
        appointment.queue_position = None
        appointment.updated_at = datetime.utcnow()

        # Capture elapsed time in EMA when cancelling a consultation already in
        # progress. Use alpha=0.05 so an interrupted session nudges the average
        # less than a cleanly completed one.
        if was_in_progress and appointment.consultation_start_time:
            elapsed_seconds = (datetime.utcnow() - appointment.consultation_start_time).total_seconds()
            elapsed_minutes = int(elapsed_seconds / 60)
            AppointmentService.update_average_consultation_duration(
                db=db,
                doctor_id=doctor_id,
                actual_duration=elapsed_minutes,
                alpha=0.05,
            )

        db.commit()

        # Audit chain entry for cancellation
        create_audit_entry(
            db, appointment.id, "appointment_cancelled",
            {
                "patient_id": appointment.patient_id,
                "doctor_id": appointment.doctor_id,
                "scheduled_time": appointment.scheduled_time.isoformat(),
                "cancelled_by_user_id": user_id,
            },
            user_id
        )
        db.commit()
        
        # Update queue positions for remaining appointments
        if cancelled_queue_position:
            AppointmentService.update_queue_positions_after_cancellation(
                db=db,
                doctor_id=doctor_id,
                cancelled_position=cancelled_queue_position
            )
        
        # Broadcast queue update
        AppointmentService._broadcast_queue_update(db, doctor_id)
        
        db.refresh(appointment)
        
        # Send cancellation notification to patient and doctor
        AppointmentService._send_appointment_notification(
            db=db,
            appointment=appointment,
            notification_type="cancelled",
            message="Your appointment has been cancelled"
        )
        
        return appointment
    
    @staticmethod
    def update_queue_positions_after_cancellation(
        db: Session,
        doctor_id: int,
        cancelled_position: int
    ):
        """
        Update queue positions after an appointment is cancelled.

        All appointments with queue_position > cancelled_position are decremented by 1.

        A PostgreSQL advisory transaction lock keyed on doctor_id is acquired
        before the read-modify-write so that concurrent cancellations for the
        same doctor are serialised. The lock is held until the surrounding
        transaction commits, preventing the lost-update race condition where
        two concurrent requests both read the same queue positions and both
        write decremented values, resulting in duplicate position numbers.
        """
        # Serialise all queue renumbering for this doctor within the transaction.
        # pg_advisory_xact_lock is released automatically at transaction end.
        db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": doctor_id})

        # Get all appointments with higher queue positions
        appointments_to_update = db.query(Appointment).filter(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.queue_position > cancelled_position,
                Appointment.status.in_([
                    AppointmentStatus.SCHEDULED,
                    AppointmentStatus.CHECKED_IN,
                    AppointmentStatus.IN_PROGRESS
                ])
            )
        ).all()

        # Decrement queue positions
        for appointment in appointments_to_update:
            appointment.queue_position -= 1
            appointment.updated_at = datetime.utcnow()

        db.commit()
    
    @staticmethod
    def reschedule_appointment(
        db: Session,
        appointment_id: int,
        new_scheduled_time: datetime,
        user_id: int,
        user_role: str
    ) -> Appointment:
        """
        Reschedule an appointment to a new time.
        
        Validates:
        - Appointment exists
        - User has permission (patient owns it or staff)
        - New time slot is available (no double-booking)
        - Updates scheduled_time and recalculates queue_position
        
        Args:
            db: Database session
            appointment_id: ID of appointment to reschedule
            new_scheduled_time: New scheduled time for the appointment
            user_id: ID of user requesting reschedule
            user_role: Role of user (Patient, Doctor, Nurse, Admin)
            
        Returns:
            Rescheduled appointment
            
        Raises:
            HTTPException: If validation fails
        """
        from app.models.user import UserRole
        
        # Get appointment
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment with ID {appointment_id} not found"
            )
        
        # Check if already cancelled or completed
        if appointment.status in [AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reschedule appointment with status: {appointment.status.value}"
            )
        
        # Check authorization
        if user_role == UserRole.PATIENT.value:
            # Patients can only reschedule their own appointments
            patient = db.query(Patient).filter(Patient.user_id == user_id).first()
            if not patient or appointment.patient_id != patient.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only reschedule your own appointments"
                )
        # Staff (Admin, Doctor, Nurse) can reschedule any appointment - no additional check needed

        # Validate new time is in the future
        if new_scheduled_time <= datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="New appointment time must be in the future"
            )

        # Check new time slot availability (exclude current appointment)
        is_available = AppointmentService.check_doctor_availability(
            db=db,
            doctor_id=appointment.doctor_id,
            scheduled_time=new_scheduled_time,
            exclude_appointment_id=appointment_id
        )
        
        if not is_available:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Doctor is not available at the requested time. Please choose another time slot."
            )
        
        # Store old queue position and old scheduled_time before update
        old_queue_position = appointment.queue_position
        old_scheduled_time = appointment.scheduled_time

        # Update appointment scheduled time
        appointment.scheduled_time = new_scheduled_time
        appointment.updated_at = datetime.utcnow()

        # Recalculate queue position based on new scheduled time
        # Get new queue position (add to end of queue)
        new_queue_position = AppointmentService.get_next_queue_position(
            db=db,
            doctor_id=appointment.doctor_id
        )
        appointment.queue_position = new_queue_position

        db.commit()

        # Audit chain entry for reschedule
        create_audit_entry(
            db, appointment.id, "appointment_rescheduled",
            {
                "patient_id": appointment.patient_id,
                "doctor_id": appointment.doctor_id,
                "old_scheduled_time": old_scheduled_time.isoformat(),
                "new_scheduled_time": new_scheduled_time.isoformat(),
                "rescheduled_by_user_id": user_id,
            },
            user_id
        )
        db.commit()

        # Update queue positions for appointments after the old position
        if old_queue_position:
            AppointmentService.update_queue_positions_after_cancellation(
                db=db,
                doctor_id=appointment.doctor_id,
                cancelled_position=old_queue_position
            )

        # Broadcast queue update
        AppointmentService._broadcast_queue_update(db, appointment.doctor_id)

        db.refresh(appointment)

        # Send reschedule notification to patient and doctor
        AppointmentService._send_appointment_notification(
            db=db,
            appointment=appointment,
            notification_type="rescheduled",
            message="Your appointment has been rescheduled"
        )
        
        return appointment
    
    @staticmethod
    def register_walk_in(
        db: Session,
        doctor_id: int,
        patient_name: str,
        patient_email: Optional[str] = None,
        patient_phone: Optional[str] = None,
        gender: Optional[str] = None,
        date_of_birth: Optional[datetime] = None,
        address: Optional[str] = None,
        blood_group: Optional[str] = None
    ) -> tuple[Appointment, Patient, bool]:
        """
        Register a walk-in patient and create an immediate appointment.
        
        This method:
        1. Checks if patient exists by email or phone
        2. Creates User and Patient records if new patient
        3. Creates appointment with type WALK_IN and immediate scheduled_time
        4. Assigns queue position and returns estimated wait time
        
        Args:
            db: Database session
            doctor_id: ID of the doctor to assign
            patient_name: Patient's full name
            patient_email: Patient's email (optional)
            patient_phone: Patient's phone number (optional)
            gender: Patient's gender (optional)
            date_of_birth: Patient's date of birth (optional)
            address: Patient's address (optional)
            blood_group: Patient's blood group (optional)
            
        Returns:
            Tuple of (Appointment, Patient, is_new_patient)
            
        Raises:
            HTTPException: If doctor not found or validation fails
        """
        from app.models.user import User, UserRole
        from app.core.security import get_password_hash
        import secrets
        import uuid
        
        # Validate doctor exists
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor with ID {doctor_id} not found"
            )
        
        # Check if patient already exists by email or phone
        existing_patient = None
        is_new_patient = True
        
        if patient_email:
            # Check by email
            existing_user = db.query(User).filter(
                User.email == patient_email,
                User.role == UserRole.PATIENT
            ).first()
            if existing_user:
                existing_patient = db.query(Patient).filter(
                    Patient.user_id == existing_user.id
                ).first()
                is_new_patient = False
        
        if not existing_patient and patient_phone:
            # Check by phone
            existing_patient = db.query(Patient).filter(
                Patient.phone == patient_phone
            ).first()
            if existing_patient:
                is_new_patient = False
        
        # Create new patient if doesn't exist
        if is_new_patient:
            # Generate a unique email if not provided
            if not patient_email:
                patient_email = f"walkin_{uuid.uuid4().hex[:12]}@healthsaathi.internal"
            
            # Generate a random password for walk-in patients
            random_password = secrets.token_urlsafe(16)
            password_hash = get_password_hash(random_password)
            
            # Create User record
            new_user = User(
                name=patient_name,
                email=patient_email,
                password_hash=password_hash,
                role=UserRole.PATIENT,
                is_walk_in=True,
            )
            db.add(new_user)
            db.flush()  # Get user.id without committing
            
            # Create Patient record
            existing_patient = Patient(
                user_id=new_user.id,
                date_of_birth=date_of_birth,
                gender=gender,
                phone=patient_phone,
                address=address,
                blood_group=blood_group
            )
            db.add(existing_patient)
            db.flush()  # Get patient.id without committing
        
        # Create walk-in appointment with current UTC time as scheduled time
        scheduled_time = datetime.utcnow()

        # Get next queue position
        queue_position = AppointmentService.get_next_queue_position(
            db=db,
            doctor_id=doctor_id
        )
        
        # Create appointment
        appointment = Appointment(
            patient_id=existing_patient.id,
            doctor_id=doctor_id,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.SCHEDULED,
            appointment_type=AppointmentType.WALK_IN,
            queue_position=queue_position
        )
        
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        db.refresh(existing_patient)

        # Audit chain entry for walk-in registration
        create_audit_entry(
            db, appointment.id, "walk_in_registered",
            {
                "patient_id": existing_patient.id,
                "doctor_id": doctor_id,
                "is_new_patient": is_new_patient,
                "queue_position": appointment.queue_position,
                "scheduled_time": appointment.scheduled_time.isoformat(),
            },
            existing_patient.user_id
        )
        db.commit()

        # Broadcast queue update
        AppointmentService._broadcast_queue_update(db, doctor_id)

        # Send appointment notification to patient and doctor
        AppointmentService._send_appointment_notification(
            db=db,
            appointment=appointment,
            notification_type="appointment_created",
            message="Walk-in appointment has been created"
        )

        return appointment, existing_patient, is_new_patient
    
    @staticmethod
    def get_doctor_queue(db: Session, doctor_id: int) -> dict:
        """
        Get current queue for a specific doctor.
        
        Returns queue information including:
        - List of patients in queue with names and positions
        - Estimated wait time for each patient
        - Total queue length
        - Doctor's average consultation duration
        
        Args:
            db: Database session
            doctor_id: ID of the doctor
            
        Returns:
            Dictionary with queue details
            
        Raises:
            HTTPException: If doctor not found
        """
        from app.models.user import User
        
        # Validate doctor exists
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor with ID {doctor_id} not found"
            )
        
        # Get doctor's user info
        doctor_user = db.query(User).filter(User.id == doctor.user_id).first()
        
        # Get all appointments in queue (SCHEDULED, CHECKED_IN, IN_PROGRESS)
        queue_appointments = db.query(Appointment).filter(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.status.in_([
                    AppointmentStatus.SCHEDULED,
                    AppointmentStatus.CHECKED_IN,
                    AppointmentStatus.IN_PROGRESS
                ])
            )
        ).order_by(Appointment.queue_position.asc()).all()
        
        # Build patient list with details
        patients = []
        for appointment in queue_appointments:
            # Get patient info
            patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
            patient_user = db.query(User).filter(User.id == patient.user_id).first()
            
            # Calculate estimated wait time
            estimated_wait_time = AppointmentService.calculate_estimated_wait_time(
                db=db,
                doctor_id=doctor_id,
                queue_position=appointment.queue_position
            )
            
            patients.append({
                "appointment_id": appointment.id,
                "patient_id": patient.id,
                "patient_name": patient_user.name,
                "queue_position": appointment.queue_position,
                "estimated_wait_time": estimated_wait_time,
                "status": appointment.status,
                "scheduled_time": appointment.scheduled_time
            })
        
        return {
            "doctor_id": doctor.id,
            "doctor_name": doctor_user.name,
            "doctor_specialization": doctor.specialization,
            "average_consultation_duration": doctor.average_consultation_duration,
            "total_queue_length": len(patients),
            "patients": patients
        }
    
    @staticmethod
    def get_all_queues_status(db: Session) -> List[dict]:
        """
        Get queue status summary for all doctors.
        
        Returns a summary of queue length and average wait time for each doctor.
        
        Args:
            db: Database session
            
        Returns:
            List of queue status summaries for all doctors
        """
        from app.models.user import User
        
        # Get all doctors
        doctors = db.query(Doctor).all()
        
        queue_summaries = []
        for doctor in doctors:
            # Get doctor's user info
            doctor_user = db.query(User).filter(User.id == doctor.user_id).first()
            
            # Count appointments in queue
            queue_count = db.query(func.count(Appointment.id)).filter(
                and_(
                    Appointment.doctor_id == doctor.id,
                    Appointment.status.in_([
                        AppointmentStatus.SCHEDULED,
                        AppointmentStatus.CHECKED_IN,
                        AppointmentStatus.IN_PROGRESS
                    ])
                )
            ).scalar()
            
            # Calculate average wait time (middle of queue)
            avg_wait_time = 0
            if queue_count > 0:
                # Average position is roughly queue_count / 2
                avg_position = (queue_count + 1) / 2
                avg_wait_time = int(avg_position * doctor.average_consultation_duration)
            
            queue_summaries.append({
                "doctor_id": doctor.id,
                "doctor_name": doctor_user.name,
                "doctor_specialization": doctor.specialization,
                "queue_length": queue_count,
                "average_wait_time": avg_wait_time
            })
        
        return queue_summaries
    
    @staticmethod
    def update_appointment_status(
        db: Session,
        appointment_id: int,
        new_status: AppointmentStatus,
        user_id: int,
        user_role: str
    ) -> Appointment:
        """
        Update appointment status with queue management.
        
        Handles status transitions:
        - SCHEDULED → CHECKED_IN (patient arrives)
        - CHECKED_IN → IN_PROGRESS (consultation starts)
        - IN_PROGRESS → COMPLETED (consultation ends)
        
        When status changes to COMPLETED:
        - Clears queue_position
        - Recalculates positions for remaining appointments
        
        Args:
            db: Database session
            appointment_id: ID of appointment to update
            new_status: New status to set
            user_id: ID of user making the change
            user_role: Role of user (Doctor, Nurse, Admin)
            
        Returns:
            Updated appointment
            
        Raises:
            HTTPException: If validation fails
        """
        from app.models.user import UserRole
        
        # Get appointment
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment with ID {appointment_id} not found"
            )
        
        # Only doctors and staff can update appointment status
        if user_role not in [UserRole.DOCTOR.value, UserRole.NURSE.value, UserRole.ADMIN.value]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only doctors and staff can update appointment status"
            )
        
        # Validate status transition
        current_status = appointment.status
        
        # Define valid transitions
        valid_transitions = {
            AppointmentStatus.SCHEDULED: [AppointmentStatus.CHECKED_IN, AppointmentStatus.NO_SHOW],
            AppointmentStatus.CHECKED_IN: [AppointmentStatus.IN_PROGRESS],
            AppointmentStatus.IN_PROGRESS: [AppointmentStatus.COMPLETED],
        }
        
        # Check if transition is valid
        if current_status not in valid_transitions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transition from status: {current_status.value}"
            )
        
        if new_status not in valid_transitions[current_status]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from {current_status.value} to {new_status.value}"
            )
        
        # Store doctor_id, queue_position, and old_status before update
        doctor_id = appointment.doctor_id
        old_queue_position = appointment.queue_position
        old_status = appointment.status

        # Update appointment status
        appointment.status = new_status
        appointment.updated_at = datetime.utcnow()

        # Track consultation start time when status changes to IN_PROGRESS
        if new_status == AppointmentStatus.IN_PROGRESS:
            appointment.consultation_start_time = datetime.utcnow()

        # If status is COMPLETED, clear queue position and update remaining queue
        if new_status == AppointmentStatus.COMPLETED:
            appointment.queue_position = None

            # Calculate actual consultation duration and update doctor's average
            if appointment.consultation_start_time:
                actual_duration_seconds = (datetime.utcnow() - appointment.consultation_start_time).total_seconds()
                actual_duration_minutes = int(actual_duration_seconds / 60)

                # Update doctor's average consultation duration using EMA
                AppointmentService.update_average_consultation_duration(
                    db=db,
                    doctor_id=doctor_id,
                    actual_duration=actual_duration_minutes
                )

            # Update queue positions for remaining appointments
            if old_queue_position:
                AppointmentService.update_queue_positions_after_cancellation(
                    db=db,
                    doctor_id=doctor_id,
                    cancelled_position=old_queue_position
                )

        # If status is NO_SHOW, record timestamp and clear queue position.
        # Queue is NOT renumbered — the slot simply closes naturally.
        if new_status == AppointmentStatus.NO_SHOW:
            appointment.no_show_at = datetime.utcnow()
            appointment.queue_position = None
        
        db.commit()
        db.refresh(appointment)

        # Audit chain entry for status change
        create_audit_entry(
            db, appointment.id, "appointment_status_updated",
            {
                "old_status": old_status.value,
                "new_status": new_status.value,
                "doctor_id": appointment.doctor_id,
                "patient_id": appointment.patient_id,
                "consultation_start_time": (
                    appointment.consultation_start_time.isoformat()
                    if appointment.consultation_start_time else None
                ),
            },
            user_id
        )
        db.commit()

        # Broadcast queue update
        AppointmentService._broadcast_queue_update(db, doctor_id)

        # Send status change notification to patient and doctor
        AppointmentService._send_appointment_notification(
            db=db,
            appointment=appointment,
            notification_type="status_changed",
            message=f"Your appointment status has been updated to {new_status.value}"
        )

        return appointment

    @staticmethod
    def update_average_consultation_duration(
        db: Session,
        doctor_id: int,
        actual_duration: int,
        alpha: float = 0.2,
    ):
        """
        Update doctor's average consultation duration using exponential moving average (EMA).

        Formula: new_average = (alpha * actual_duration) + ((1 - alpha) * old_average)

        Args:
            db: Database session
            doctor_id: ID of the doctor
            actual_duration: Actual consultation duration in minutes
            alpha: EMA weight for the new sample. Default 0.2 for completed
                   consultations; pass 0.05 for non-completed exits (no_show,
                   cancellation mid-consult) so they nudge the average less.
        """
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            return

        old_average = doctor.average_consultation_duration
        new_average = (alpha * actual_duration) + ((1 - alpha) * old_average)

        doctor.average_consultation_duration = int(round(new_average))

        db.commit()
