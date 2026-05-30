"""
Main API router for v1 endpoints
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, appointments, queue, medical_records, audit, websocket, anomaly, patients, vitals, allergies, procedures, organizations, providers

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

# Include anomaly detection endpoints (admin only)
api_router.include_router(anomaly.router, prefix="/anomaly", tags=["anomaly"])

# Include patient search endpoint (Doctor and Nurse only)
api_router.include_router(patients.router, prefix="/patients", tags=["patients"])

# Include vitals endpoints (Nurse/Doctor record; patients read own)
api_router.include_router(vitals.router, prefix="/vitals", tags=["vitals"])

# Include allergies endpoints (Doctor/Nurse record; patients read own)
api_router.include_router(allergies.router, prefix="/allergies", tags=["allergies"])

# Include procedures endpoints (Doctor records; patients/staff read)
api_router.include_router(procedures.router, prefix="/procedures", tags=["procedures"])

# Include organisations directory (read-only for all authenticated users)
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])

# Include providers directory (read-only for all authenticated users)
api_router.include_router(providers.router, prefix="/providers", tags=["providers"])

@api_router.get("/")
async def api_root():
    """API v1 root endpoint"""
    return {"message": "HealthSaathi API v1"}
