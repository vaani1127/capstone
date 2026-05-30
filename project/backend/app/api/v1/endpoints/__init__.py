"""API v1 endpoints"""
from app.api.v1.endpoints import auth, users, appointments, queue, medical_records, audit, websocket

__all__ = ["auth", "users", "appointments", "queue", "medical_records", "audit", "websocket"]
