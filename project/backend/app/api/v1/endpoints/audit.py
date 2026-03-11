"""
Audit and integrity verification endpoints
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime
import logging
import math
import json

from app.db.session import get_db
from app.models.user import User
from app.models.audit_chain import AuditChain
from app.schemas.audit import AuditLogResponse, AuditLogListResponse, TamperingAlertResponse
from app.core.dependencies import require_admin

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    start_date: Optional[datetime] = Query(None, description="Filter by start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date (ISO format)"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    record_type: Optional[str] = Query(None, description="Filter by record type (e.g., 'medical_record', 'appointment')"),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page (max 100)")
):
    """
    Get audit logs with optional filtering and pagination (Admin only).
    
    **Required Role:** Admin
    
    Args:
        db: Database session
        current_user: Current authenticated admin
        start_date: Filter by start date (optional)
        end_date: Filter by end date (optional)
        user_id: Filter by user ID (optional)
        record_type: Filter by record type (optional)
        page: Page number (default: 1)
        page_size: Items per page (default: 20, max: 100)
        
    Returns:
        Paginated list of audit log entries matching filters
    """
    try:
        # Build query with filters
        query = db.query(AuditChain)
        
        filters = []
        
        # Apply date range filter
        if start_date:
            filters.append(AuditChain.timestamp >= start_date)
            logger.debug(f"Filtering audit logs from: {start_date}")
        
        if end_date:
            filters.append(AuditChain.timestamp <= end_date)
            logger.debug(f"Filtering audit logs until: {end_date}")
        
        # Apply user filter
        if user_id is not None:
            filters.append(AuditChain.user_id == user_id)
            logger.debug(f"Filtering audit logs by user_id: {user_id}")
        
        # Apply record type filter
        if record_type:
            filters.append(AuditChain.record_type == record_type)
            logger.debug(f"Filtering audit logs by record_type: {record_type}")
        
        # Apply all filters
        if filters:
            query = query.filter(and_(*filters))
        
        # Get total count before pagination
        total = query.count()
        
        # Calculate pagination
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        offset = (page - 1) * page_size
        
        # Apply pagination and ordering (newest first)
        audit_entries = query.order_by(AuditChain.timestamp.desc()).offset(offset).limit(page_size).all()
        
        # Enrich with user information
        logs = []
        for entry in audit_entries:
            log_data = AuditLogResponse(
                id=entry.id,
                record_id=entry.record_id,
                record_type=entry.record_type,
                record_data=entry.record_data,
                hash=entry.hash,
                previous_hash=entry.previous_hash,
                timestamp=entry.timestamp,
                user_id=entry.user_id,
                is_tampered=entry.is_tampered,
                user_name=entry.user.name if entry.user else None,
                user_email=entry.user.email if entry.user else None
            )
            logs.append(log_data)
        
        logger.info(
            f"Admin {current_user.email} retrieved {len(logs)} audit logs "
            f"(page {page}/{total_pages}, total: {total})"
        )
        
        return AuditLogListResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            logs=logs
        )
        
    except Exception as e:
        logger.error(f"Error retrieving audit logs: {str(e)}")
        raise


@router.get("/tampering-alerts", response_model=List[TamperingAlertResponse])
async def get_tampering_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    sort_by: str = Query("timestamp", description="Sort by 'timestamp' or 'severity' (default: timestamp)")
):
    """
    Get all tampering alerts (Admin only).
    
    **Required Role:** Admin
    
    Args:
        db: Database session
        current_user: Current authenticated admin
        sort_by: Sort order - 'timestamp' (newest first) or 'severity' (default: timestamp)
        
    Returns:
        List of records flagged for tampering, sorted by timestamp (newest first) or severity
    """
    try:
        # Query all audit entries where is_tampered = True
        query = db.query(AuditChain).filter(AuditChain.is_tampered == True)
        
        # Apply sorting
        if sort_by == "severity":
            # Sort by record_type (medical_record first as most critical), then by timestamp
            query = query.order_by(
                AuditChain.record_type.desc(),  # medical_record comes before appointment
                AuditChain.timestamp.desc()
            )
        else:
            # Default: sort by timestamp (newest first)
            query = query.order_by(AuditChain.timestamp.desc())
        
        tampered_entries = query.all()
        
        # Build response with user information
        alerts = []
        for entry in tampered_entries:
            alert = {
                "id": entry.id,
                "record_id": entry.record_id,
                "record_type": entry.record_type,
                "hash": entry.hash,
                "timestamp": entry.timestamp,
                "user_id": entry.user_id,
                "user_name": entry.user.name if entry.user else None,
                "user_email": entry.user.email if entry.user else None
            }
            alerts.append(alert)
        
        logger.info(
            f"Admin {current_user.email} retrieved {len(alerts)} tampering alerts "
            f"(sorted by: {sort_by})"
        )
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error retrieving tampering alerts: {str(e)}")
        raise


@router.post("/verify/{record_id}", response_model=dict)
async def verify_record_integrity(
    record_id: int,
    record_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Manually verify integrity of a specific record (Admin only).
    
    **Required Role:** Admin
    
    Args:
        record_id: ID of the record to verify
        record_type: Type of record (e.g., 'medical_record')
        db: Database session
        current_user: Current authenticated admin
        
    Returns:
        Verification result with hash comparison details
    """
    # TODO: Implement manual integrity verification
    return {}


@router.get("/export")
async def export_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    format: str = Query("json", description="Export format: 'json' or 'csv'"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date (ISO format)"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    record_type: Optional[str] = Query(None, description="Filter by record type (e.g., 'medical_record', 'appointment')")
):
    """
    Export audit logs in CSV or JSON format (Admin only).
    
    **Required Role:** Admin
    
    Args:
        db: Database session
        current_user: Current authenticated admin
        format: Export format - 'json' or 'csv' (default: json)
        start_date: Filter by start date (optional)
        end_date: Filter by end date (optional)
        user_id: Filter by user ID (optional)
        record_type: Filter by record type (optional)
        
    Returns:
        Audit logs in requested format with appropriate content-type headers
    """
    from fastapi.responses import StreamingResponse
    from fastapi import HTTPException
    import csv
    import io
    
    try:
        # Validate format
        if format not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail="Invalid format. Must be 'json' or 'csv'")
        
        # Build query with filters (same as get_audit_logs)
        query = db.query(AuditChain)
        
        filters = []
        
        # Apply date range filter
        if start_date:
            filters.append(AuditChain.timestamp >= start_date)
            logger.debug(f"Filtering export from: {start_date}")
        
        if end_date:
            filters.append(AuditChain.timestamp <= end_date)
            logger.debug(f"Filtering export until: {end_date}")
        
        # Apply user filter
        if user_id is not None:
            filters.append(AuditChain.user_id == user_id)
            logger.debug(f"Filtering export by user_id: {user_id}")
        
        # Apply record type filter
        if record_type:
            filters.append(AuditChain.record_type == record_type)
            logger.debug(f"Filtering export by record_type: {record_type}")
        
        # Apply all filters
        if filters:
            query = query.filter(and_(*filters))
        
        # Get all matching entries (ordered by timestamp, newest first)
        audit_entries = query.order_by(AuditChain.timestamp.desc()).all()
        
        logger.info(
            f"Admin {current_user.email} exporting {len(audit_entries)} audit logs "
            f"in {format.upper()} format"
        )
        
        if format == "json":
            # Export as JSON
            logs = []
            for entry in audit_entries:
                log_data = {
                    "id": entry.id,
                    "record_id": entry.record_id,
                    "record_type": entry.record_type,
                    "record_data": entry.record_data,
                    "hash": entry.hash,
                    "previous_hash": entry.previous_hash,
                    "timestamp": entry.timestamp.isoformat(),
                    "user_id": entry.user_id,
                    "is_tampered": entry.is_tampered,
                    "user_name": entry.user.name if entry.user else None,
                    "user_email": entry.user.email if entry.user else None
                }
                logs.append(log_data)
            
            # Convert to JSON string
            json_content = json.dumps(logs, indent=2)
            
            # Return as downloadable file
            return StreamingResponse(
                io.BytesIO(json_content.encode()),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
                }
            )
        
        else:  # format == "csv"
            # Export as CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                "id",
                "record_id",
                "record_type",
                "record_data",
                "hash",
                "previous_hash",
                "timestamp",
                "user_id",
                "user_name",
                "user_email",
                "is_tampered"
            ])
            
            # Write data rows
            for entry in audit_entries:
                writer.writerow([
                    entry.id,
                    entry.record_id,
                    entry.record_type,
                    json.dumps(entry.record_data),  # Convert dict to JSON string for CSV
                    entry.hash,
                    entry.previous_hash,
                    entry.timestamp.isoformat(),
                    entry.user_id if entry.user_id else "",
                    entry.user.name if entry.user else "",
                    entry.user.email if entry.user else "",
                    entry.is_tampered
                ])
            
            # Get CSV content
            csv_content = output.getvalue()
            
            # Return as downloadable file
            return StreamingResponse(
                io.BytesIO(csv_content.encode()),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            )
        
    except Exception as e:
        logger.error(f"Error exporting audit logs: {str(e)}")
        raise


@router.get("/export")
async def export_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    format: str = Query("json", description="Export format: 'json' or 'csv'"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date (ISO format)"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    record_type: Optional[str] = Query(None, description="Filter by record type (e.g., 'medical_record', 'appointment')")
):
    """
    Export audit logs in CSV or JSON format (Admin only).

    **Required Role:** Admin

    Args:
        db: Database session
        current_user: Current authenticated admin
        format: Export format - 'json' or 'csv' (default: json)
        start_date: Filter by start date (optional)
        end_date: Filter by end date (optional)
        user_id: Filter by user ID (optional)
        record_type: Filter by record type (optional)

    Returns:
        Audit logs in requested format with appropriate content-type headers
    """
    from fastapi.responses import StreamingResponse
    import csv
    import io

    try:
        # Validate format
        if format not in ["json", "csv"]:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Invalid format. Must be 'json' or 'csv'")

        # Build query with filters (same as get_audit_logs)
        query = db.query(AuditChain)

        filters = []

        # Apply date range filter
        if start_date:
            filters.append(AuditChain.timestamp >= start_date)
            logger.debug(f"Filtering export from: {start_date}")

        if end_date:
            filters.append(AuditChain.timestamp <= end_date)
            logger.debug(f"Filtering export until: {end_date}")

        # Apply user filter
        if user_id is not None:
            filters.append(AuditChain.user_id == user_id)
            logger.debug(f"Filtering export by user_id: {user_id}")

        # Apply record type filter
        if record_type:
            filters.append(AuditChain.record_type == record_type)
            logger.debug(f"Filtering export by record_type: {record_type}")

        # Apply all filters
        if filters:
            query = query.filter(and_(*filters))

        # Get all matching entries (ordered by timestamp, newest first)
        audit_entries = query.order_by(AuditChain.timestamp.desc()).all()

        logger.info(
            f"Admin {current_user.email} exporting {len(audit_entries)} audit logs "
            f"in {format.upper()} format"
        )

        if format == "json":
            # Export as JSON
            logs = []
            for entry in audit_entries:
                log_data = {
                    "id": entry.id,
                    "record_id": entry.record_id,
                    "record_type": entry.record_type,
                    "record_data": entry.record_data,
                    "hash": entry.hash,
                    "previous_hash": entry.previous_hash,
                    "timestamp": entry.timestamp.isoformat(),
                    "user_id": entry.user_id,
                    "is_tampered": entry.is_tampered,
                    "user_name": entry.user.name if entry.user else None,
                    "user_email": entry.user.email if entry.user else None
                }
                logs.append(log_data)

            # Convert to JSON string
            json_content = json.dumps(logs, indent=2)

            # Return as downloadable file
            return StreamingResponse(
                io.BytesIO(json_content.encode()),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
                }
            )

        else:  # format == "csv"
            # Export as CSV
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow([
                "id",
                "record_id",
                "record_type",
                "record_data",
                "hash",
                "previous_hash",
                "timestamp",
                "user_id",
                "user_name",
                "user_email",
                "is_tampered"
            ])

            # Write data rows
            for entry in audit_entries:
                writer.writerow([
                    entry.id,
                    entry.record_id,
                    entry.record_type,
                    json.dumps(entry.record_data),  # Convert dict to JSON string for CSV
                    entry.hash,
                    entry.previous_hash,
                    entry.timestamp.isoformat(),
                    entry.user_id if entry.user_id else "",
                    entry.user.name if entry.user else "",
                    entry.user.email if entry.user else "",
                    entry.is_tampered
                ])

            # Get CSV content
            csv_content = output.getvalue()

            # Return as downloadable file
            return StreamingResponse(
                io.BytesIO(csv_content.encode()),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            )

    except Exception as e:
        logger.error(f"Error exporting audit logs: {str(e)}")
        raise

