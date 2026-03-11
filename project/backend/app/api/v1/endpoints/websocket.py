"""
WebSocket endpoint for real-time communication
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status, Depends
from sqlalchemy.orm import Session
import logging
from typing import Optional

from app.services.websocket_manager import manager
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


def get_token_from_query(token: str = Query(..., description="JWT access token for authentication")) -> str:
    """Extract token from query parameter"""
    return token


async def authenticate_websocket(token: str, db: Session) -> Optional[User]:
    """
    Authenticate WebSocket connection using JWT token.
    
    Args:
        token: JWT token from query parameter
        db: Database session
        
    Returns:
        User object if authentication successful, None otherwise
    """
    try:
        # Decode and validate token
        payload = decode_token(token)
        
        if payload is None:
            logger.warning("Invalid or expired WebSocket token")
            return None
        
        # Verify token type
        token_type = payload.get("type")
        if token_type != "access":
            logger.warning(f"Invalid WebSocket token type: {token_type}")
            return None
        
        # Extract user info
        user_id = payload.get("user_id")
        if user_id is None:
            logger.warning("WebSocket token missing user_id")
            return None
        
        # Fetch user from database
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            logger.warning(f"User not found for WebSocket connection: {user_id}")
            return None
        
        logger.debug(f"WebSocket authenticated: {user.email} (ID: {user.id})")
        return user
        
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Depends(get_token_from_query),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time communication.
    
    Authentication:
        - Requires JWT token as query parameter: /ws?token=<jwt_token>
        - Token must be a valid access token
        - Connection rejected if authentication fails
    
    Connection Lifecycle:
        1. Client connects with JWT token
        2. Server authenticates and accepts connection
        3. Connection added to pool by user_id
        4. Server can send real-time updates
        5. Client can send messages (future enhancement)
        6. Connection closed on disconnect or error
    
    Message Format:
        All messages are JSON with the following structure:
        {
            "event": "event_type",
            "data": { ... },
            "timestamp": "2024-01-01T00:00:00Z"
        }
    
    Example:
        ws://localhost:8000/api/v1/ws?token=eyJhbGc...
    """
    try:
        # Authenticate connection
        user = await authenticate_websocket(token, db)
        
        if user is None:
            # Reject connection with close code 1008 (Policy Violation)
            try:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
            except:
                pass
            logger.warning("WebSocket connection rejected: authentication failed")
            return
        
        # Accept and register connection
        await manager.connect(websocket, user.id, user.email)
        
        # Send welcome message
        await websocket.send_json({
            "event": "connected",
            "data": {
                "message": "WebSocket connection established",
                "user_id": user.id,
                "user_email": user.email
            },
            "timestamp": None  # Will be set by client
        })
        
        # Keep connection alive and handle incoming messages
        try:
            while True:
                # Wait for messages from client
                data = await websocket.receive_text()
                
                # Echo back for now (can be extended for client-to-server messages)
                logger.debug(f"Received message from user {user.id}: {data}")
                
                # Send acknowledgment
                await websocket.send_json({
                    "event": "message_received",
                    "data": {
                        "message": "Message received",
                        "received_data": data
                    },
                    "timestamp": None
                })
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected normally: user_id={user.id}")
        except Exception as e:
            logger.error(f"WebSocket error for user {user.id}: {e}")
        finally:
            # Clean up connection
            manager.disconnect(websocket)
            
    except Exception as e:
        logger.error(f"WebSocket endpoint error: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
        except:
            pass


@router.get("/ws/status")
async def websocket_status():
    """
    Get WebSocket server status and connection statistics.
    
    Returns:
        Dictionary with connection statistics
    """
    return {
        "status": "operational",
        "active_users": len(manager.get_active_users()),
        "total_connections": manager.get_connection_count(),
        "connected_user_ids": manager.get_active_users()
    }
