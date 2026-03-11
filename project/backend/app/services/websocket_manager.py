"""
WebSocket connection manager for real-time communication
"""
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.
    
    Maintains a connection pool organized by user_id, supporting
    multiple connections per user (e.g., multiple browser tabs).
    """
    
    def __init__(self):
        # Dictionary mapping user_id to list of active WebSocket connections
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Track connection metadata
        self.connection_metadata: Dict[WebSocket, dict] = {}
        logger.info("WebSocket ConnectionManager initialized")
    
    async def connect(self, websocket: WebSocket, user_id: int, user_email: str = None):
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection instance
            user_id: ID of the authenticated user
            user_email: Email of the authenticated user (optional, for logging)
        """
        await websocket.accept()
        
        # Add connection to user's connection list
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        
        # Store metadata
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "user_email": user_email,
            "connected_at": datetime.utcnow().isoformat()
        }
        
        logger.info(
            f"WebSocket connected: user_id={user_id}, "
            f"email={user_email}, "
            f"total_connections={len(self.active_connections[user_id])}"
        )
    
    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection from the pool.
        
        Args:
            websocket: WebSocket connection to remove
        """
        # Get metadata before removing
        metadata = self.connection_metadata.get(websocket, {})
        user_id = metadata.get("user_id")
        user_email = metadata.get("user_email")
        
        # Remove from active connections
        if user_id and user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            # Clean up empty user entries
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        # Remove metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
        
        logger.info(
            f"WebSocket disconnected: user_id={user_id}, "
            f"email={user_email}"
        )
    
    async def send_personal_message(self, message: dict, user_id: int):
        """
        Send a message to all connections of a specific user.
        
        Args:
            message: Message dictionary to send (will be JSON serialized)
            user_id: Target user ID
        """
        if user_id not in self.active_connections:
            logger.debug(f"No active connections for user_id={user_id}")
            return
        
        # Send to all user's connections
        disconnected = []
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to user_id={user_id}: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast(self, message: dict, exclude_user_ids: Set[int] = None):
        """
        Broadcast a message to all connected users.
        
        Args:
            message: Message dictionary to send (will be JSON serialized)
            exclude_user_ids: Set of user IDs to exclude from broadcast
        """
        exclude_user_ids = exclude_user_ids or set()
        
        for user_id, connections in list(self.active_connections.items()):
            if user_id in exclude_user_ids:
                continue
            
            await self.send_personal_message(message, user_id)
    
    async def send_to_users(self, message: dict, user_ids: List[int]):
        """
        Send a message to specific users.
        
        Args:
            message: Message dictionary to send (will be JSON serialized)
            user_ids: List of target user IDs
        """
        for user_id in user_ids:
            await self.send_personal_message(message, user_id)
    
    def get_active_users(self) -> List[int]:
        """
        Get list of all users with active connections.
        
        Returns:
            List of user IDs with active connections
        """
        return list(self.active_connections.keys())
    
    def get_connection_count(self, user_id: int = None) -> int:
        """
        Get connection count for a specific user or total.
        
        Args:
            user_id: User ID to check (None for total count)
            
        Returns:
            Number of active connections
        """
        if user_id is not None:
            return len(self.active_connections.get(user_id, []))
        
        return sum(len(connections) for connections in self.active_connections.values())
    
    def is_user_connected(self, user_id: int) -> bool:
        """
        Check if a user has any active connections.
        
        Args:
            user_id: User ID to check
            
        Returns:
            True if user has at least one active connection
        """
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0
    
    async def broadcast_queue_update(self, doctor_id: int, queue_data: dict):
        """
        Broadcast queue update to all connected clients.
        
        This sends queue updates to all users who might be interested in
        the doctor's queue status (patients, doctors, nurses, admins).
        
        Args:
            doctor_id: ID of the doctor whose queue was updated
            queue_data: Queue information including length, patients, wait times
        """
        message = {
            "event": "queue_update",
            "data": {
                "doctor_id": doctor_id,
                "queue_length": queue_data.get("total_queue_length", 0),
                "patients": queue_data.get("patients", []),
                "average_consultation_duration": queue_data.get("average_consultation_duration", 15),
                "doctor_name": queue_data.get("doctor_name"),
                "doctor_specialization": queue_data.get("doctor_specialization")
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Broadcast to all connected users
        await self.broadcast(message)
        
        logger.info(
            f"Queue update broadcast: doctor_id={doctor_id}, "
            f"queue_length={queue_data.get('total_queue_length', 0)}, "
            f"recipients={len(self.active_connections)}"
        )
    
    async def send_appointment_notification(
        self,
        notification_type: str,
        appointment_data: dict,
        patient_user_id: int,
        doctor_user_id: int,
        message: str
    ):
        """
        Send appointment notification to specific patient and doctor.
        
        Sends targeted notifications when appointment status changes,
        including full appointment details.
        
        Args:
            notification_type: Type of notification (appointment_created, status_changed, cancelled, rescheduled)
            appointment_data: Full appointment details including patient and doctor names
            patient_user_id: User ID of the patient
            doctor_user_id: User ID of the doctor
            message: Human-readable notification message
        """
        notification = {
            "event": "appointment_notification",
            "data": {
                "notification_type": notification_type,
                "appointment": appointment_data,
                "message": message
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to both patient and doctor
        user_ids = [patient_user_id, doctor_user_id]
        await self.send_to_users(notification, user_ids)
        
        logger.info(
            f"Appointment notification sent: type={notification_type}, "
            f"appointment_id={appointment_data.get('id')}, "
            f"patient_user_id={patient_user_id}, "
            f"doctor_user_id={doctor_user_id}"
        )


# Global connection manager instance
manager = ConnectionManager()
