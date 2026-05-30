"""
Anomaly detection endpoints — Admin only
"""
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional
from datetime import datetime, timedelta
import logging

from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.anomaly_alert import AnomalyAlert
from app.schemas.anomaly import AnomalyAlertResponse, AnomalyAlertListResponse
from app.core.dependencies import require_admin
from app.services.websocket_manager import manager
from app.api.v1.endpoints.websocket import authenticate_websocket, get_token_from_query

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/alerts", response_model=AnomalyAlertListResponse)
async def get_anomaly_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    severity: Optional[str] = Query(None, description="Filter by severity: LOW, MEDIUM, HIGH"),
    is_acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgement status"),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
):
    """
    Get paginated list of anomaly alerts with optional filters (Admin only).

    **Required Role:** Admin
    """
    try:
        query = db.query(AnomalyAlert)

        filters = []
        if severity is not None:
            filters.append(AnomalyAlert.severity == severity.upper())
        if is_acknowledged is not None:
            filters.append(AnomalyAlert.is_acknowledged == is_acknowledged)
        if filters:
            query = query.filter(and_(*filters))

        total = query.count()
        offset = (page - 1) * page_size
        alerts = (
            query.order_by(AnomalyAlert.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        logger.info(
            "Admin %s retrieved %d anomaly alerts (page %d, total %d)",
            current_user.email, len(alerts), page, total,
        )
        return AnomalyAlertListResponse(alerts=alerts, total=total, page=page, page_size=page_size)

    except Exception as e:
        logger.error("Error retrieving anomaly alerts: %s", e)
        raise


@router.get("/alerts/{alert_id}", response_model=AnomalyAlertResponse)
async def get_anomaly_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Get a single anomaly alert by ID (Admin only).

    **Required Role:** Admin
    """
    alert = db.query(AnomalyAlert).filter(AnomalyAlert.id == alert_id).first()
    if alert is None:
        raise HTTPException(status_code=404, detail=f"Anomaly alert {alert_id} not found")
    return alert


@router.post("/alerts/{alert_id}/acknowledge", response_model=AnomalyAlertResponse)
async def acknowledge_anomaly_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Acknowledge an anomaly alert (Admin only, idempotent).

    Sets is_acknowledged=True, acknowledged_by, and acknowledged_at.
    Re-acknowledging an already-acknowledged alert is a no-op.

    **Required Role:** Admin
    """
    alert = db.query(AnomalyAlert).filter(AnomalyAlert.id == alert_id).first()
    if alert is None:
        raise HTTPException(status_code=404, detail=f"Anomaly alert {alert_id} not found")

    if not alert.is_acknowledged:
        alert.is_acknowledged = True
        alert.acknowledged_by = current_user.id
        alert.acknowledged_at = datetime.utcnow()
        db.commit()
        db.refresh(alert)
        logger.info(
            "Admin %s acknowledged anomaly alert id=%d", current_user.email, alert_id
        )

    return alert


@router.get("/stats")
async def get_anomaly_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Get aggregated anomaly alert statistics (Admin only).

    Returns counts for: total, HIGH/MEDIUM/LOW severity, unacknowledged, last 24 hours.

    **Required Role:** Admin
    """
    try:
        total = db.query(func.count(AnomalyAlert.id)).scalar() or 0
        high = (
            db.query(func.count(AnomalyAlert.id))
            .filter(AnomalyAlert.severity == "HIGH")
            .scalar() or 0
        )
        medium = (
            db.query(func.count(AnomalyAlert.id))
            .filter(AnomalyAlert.severity == "MEDIUM")
            .scalar() or 0
        )
        low = (
            db.query(func.count(AnomalyAlert.id))
            .filter(AnomalyAlert.severity == "LOW")
            .scalar() or 0
        )
        unacknowledged = (
            db.query(func.count(AnomalyAlert.id))
            .filter(AnomalyAlert.is_acknowledged == False)
            .scalar() or 0
        )
        cutoff_24h = datetime.utcnow() - timedelta(hours=24)
        last_24h = (
            db.query(func.count(AnomalyAlert.id))
            .filter(AnomalyAlert.created_at >= cutoff_24h)
            .scalar() or 0
        )

        logger.info("Admin %s retrieved anomaly stats", current_user.email)
        return {
            "total_alerts": total,
            "high_severity": high,
            "medium_severity": medium,
            "low_severity": low,
            "unacknowledged": unacknowledged,
            "last_24h": last_24h,
        }

    except Exception as e:
        logger.error("Error retrieving anomaly stats: %s", e)
        raise


@router.websocket("/ws/admin")
async def anomaly_admin_websocket(
    websocket: WebSocket,
    token: str = Depends(get_token_from_query),
    db: Session = Depends(get_db),
):
    """
    WebSocket endpoint for real-time anomaly alert delivery (Admin only).

    Authentication:
        - Requires JWT access token as query parameter: /anomaly/ws/admin?token=<jwt>
        - Connection rejected with code 1008 if token invalid or user is not Admin

    Message Format:
        {
            "event": "anomaly_alert",
            "data": {
                "alert_id": int,
                "user_id": int,
                "severity": "HIGH|MEDIUM|LOW",
                "anomaly_score": float,
                "explanation": str,
                "top_features": [...],
                "created_at": "ISO8601"
            },
            "timestamp": "ISO8601"
        }
    """
    try:
        user = await authenticate_websocket(token, db)

        if user is None or (
            user.role.value if hasattr(user.role, "value") else str(user.role)
        ) != "Admin":
            try:
                await websocket.close(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason="Admin access required",
                )
            except Exception:
                pass
            logger.warning("Admin WebSocket rejected: not authenticated or not Admin")
            return

        await manager.connect_admin(websocket, user.id)

        await websocket.send_json({
            "event": "connected",
            "data": {
                "message": "Admin anomaly WebSocket established",
                "user_id": user.id,
                "user_email": user.email,
            },
            "timestamp": datetime.utcnow().isoformat(),
        })

        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            logger.info("Admin anomaly WebSocket disconnected: user_id=%d", user.id)
        except Exception as e:
            logger.error("Admin anomaly WebSocket error for user %d: %s", user.id, e)
        finally:
            manager.disconnect_admin(websocket, user.id)

    except Exception as e:
        logger.error("Admin anomaly WebSocket endpoint error: %s", e)
        try:
            await websocket.close(
                code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error"
            )
        except Exception:
            pass
