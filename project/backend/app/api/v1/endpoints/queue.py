"""
Queue management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services.appointment_service import AppointmentService
from app.schemas.appointment import DoctorQueueResponse, QueueStatusSummary

router = APIRouter()


@router.get("/status", response_model=List[QueueStatusSummary])
async def get_queue_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get real-time queue status for all doctors.
    
    **Required Role:** Any authenticated user
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of queue status for each doctor with waiting times
    """
    queue_summaries = AppointmentService.get_all_queues_status(db=db)
    return queue_summaries


@router.get("/doctor/{doctor_id}", response_model=DoctorQueueResponse)
async def get_doctor_queue(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get queue details for a specific doctor.
    
    **Required Role:** Any authenticated user
    
    Args:
        doctor_id: ID of the doctor
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Queue details including patients, positions, and estimated wait times
    """
    queue_details = AppointmentService.get_doctor_queue(db=db, doctor_id=doctor_id)
    return queue_details
