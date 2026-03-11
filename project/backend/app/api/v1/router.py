"""
Main API router for v1 endpoints
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, appointments, queue, medical_records, audit, websocket

api_router = APIRouter()

# Include authentication endpoints (public)
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Include user management endpoints (protected)
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Include appointment endpoints (protected)
api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])

# Include queue management endpoints (protected)
api_router.include_router(queue.router, prefix="/queue", tags=["queue"])

# Include medical records endpoints (protected)
api_router.include_router(medical_records.router, prefix="/medical-records", tags=["medical-records"])

# Include audit endpoints (protected - admin only)
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])

# Include WebSocket endpoint (authenticated via query parameter)
api_router.include_router(websocket.router, tags=["websocket"])

@api_router.get("/")
async def api_root():
    """API v1 root endpoint"""
    return {"message": "HealthSaathi API v1"}
