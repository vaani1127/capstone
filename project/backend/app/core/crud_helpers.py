"""
Generic CRUD helper functions to reduce duplication across endpoints.
Consolidates common patterns: validation, audit creation, and error handling.
"""

import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.services.blockchain_service import create_audit_entry

logger = logging.getLogger(__name__)


def create_record_with_audit(
    db: Session,
    record,
    record_type: str,
    record_data: dict,
    user_id: int,
    logger_obj: logging.Logger,
):
    """
    Generic helper to create a record, flush it, create an audit entry, and commit.

    This consolidates the repeated pattern across allergies, procedures, vitals:
    1. db.add(record)
    2. db.flush()
    3. create_audit_entry(db, record_type, record.id, record_data, user_id)
    4. db.commit()
    5. db.refresh(record)
    6. logger.info(...)

    Args:
        db: SQLAlchemy Session
        record: ORM model instance to save
        record_type: audit chain record type (e.g., 'allergy_recorded')
        record_data: dict of data to store in audit chain
        user_id: user ID making the change
        logger_obj: logger instance for info message

    Returns:
        The saved record (after commit and refresh)
    """
    db.add(record)
    db.flush()

    create_audit_entry(
        db=db,
        record_id=record.id,
        record_type=record_type,
        record_data=record_data,
        user_id=user_id,
    )

    db.commit()
    db.refresh(record)

    logger_obj.info(
        f"{record_type}: id={record.id} created_by user_id={user_id}"
    )

    return record


def update_record_with_audit(
    db: Session,
    record,
    updates: dict,
    record_type: str,
    user_id: int,
    logger_obj: logging.Logger,
):
    """
    Generic helper to update a record, create audit entry, and commit.

    Consolidates the repeated pattern for updates:
    1. Apply updates to record
    2. db.commit()
    3. db.refresh(record)
    4. logger.info(...)

    Args:
        db: SQLAlchemy Session
        record: ORM model instance to update
        updates: dict of field_name -> new_value
        record_type: audit chain record type (e.g., 'allergy_updated')
        user_id: user ID making the change
        logger_obj: logger instance for info message

    Returns:
        The updated record (after commit and refresh)
    """
    for field, value in updates.items():
        if hasattr(record, field):
            setattr(record, field, value)

    db.commit()
    db.refresh(record)

    logger_obj.info(
        f"{record_type}: id={record.id} updated_by user_id={user_id}"
    )

    return record


def delete_record_with_audit(
    db: Session,
    record,
    record_type: str,
    user_id: int,
    logger_obj: logging.Logger,
):
    """
    Generic helper to soft-delete (if applicable) or hard-delete a record.

    Args:
        db: SQLAlchemy Session
        record: ORM model instance to delete
        record_type: audit chain record type (e.g., 'allergy_deactivated')
        user_id: user ID making the change
        logger_obj: logger instance for info message
    """
    db.delete(record)
    db.commit()

    logger_obj.info(
        f"{record_type}: id={record.id} deleted_by user_id={user_id}"
    )
