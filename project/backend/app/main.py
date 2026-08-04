"""
Main FastAPI application entry point
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import uuid
import time
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.limiter import limiter
from app.api.v1.router import api_router
from app.db import check_db_connection, close_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting HealthSaathi API...")
    
    # Check database connection
    if check_db_connection():
        logger.info("Database connection established successfully")
    else:
        logger.error("Failed to establish database connection")
        raise Exception("Database connection failed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down HealthSaathi API...")
    close_db_connection()
    logger.info("Database connections closed")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="HealthSaathi - Mobile-Based Secure Healthcare System",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Rate limiting
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Too many requests, slow down"},
    )

# Configure CORS.
# cors_origins raises RuntimeError at import time in production if
# ALLOWED_ORIGINS is missing or contains a wildcard — intentional: the
# app must not start with an open CORS policy.
_cors_origins = settings.cors_origins

# Warn loudly when ENVIRONMENT=production but DEBUG=True. is_development()
# returns True whenever DEBUG=True regardless of ENVIRONMENT, silently
# bypassing the production CORS lockdown and other production safeguards.
if settings.ENVIRONMENT.lower() == "production" and settings.DEBUG:
    logger.warning(
        "MISCONFIGURATION: ENVIRONMENT=production but DEBUG=True. "
        "This bypasses the production CORS lockdown and other production "
        "safeguards. Set DEBUG=False immediately."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# ---------------------------------------------------------------------------
# Request size guard — reject bodies larger than 10 MB at the app layer.
# Nginx also enforces client_max_body_size 10M; this is a defence-in-depth layer.
# ---------------------------------------------------------------------------
_MAX_BODY_BYTES = 10 * 1024 * 1024  # 10 MB

@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("Content-Length")
    if content_length and int(content_length) > _MAX_BODY_BYTES:
        return JSONResponse(
            status_code=413,
            content={"detail": "Request body too large. Maximum allowed size is 10 MB."},
        )
    return await call_next(request)


# ---------------------------------------------------------------------------
# Request tracing — attaches a UUID to every request and response.
# Logs path only (never query strings, which may contain tokens).
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# ---------------------------------------------------------------------------
# Global exception handler — logs unhandled errors with request ID.
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        extra={"request_id": request_id, "path": str(request.url)},
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": request_id},
    )


# Health check endpoint for deployment
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    """Liveness probe — returns 200 while the process is running."""
    db_healthy = check_db_connection()
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "version": settings.VERSION,
        "database": "connected" if db_healthy else "disconnected",
    }


@app.get("/ready")
async def readiness_check():
    """
    Readiness probe — returns 200 only when the service can handle traffic.

    Checks that:
    - The database connection is alive
    Returns 503 if any dependency is unavailable so that load balancers
    and k8s readiness probes can stop routing traffic to this instance.
    """
    db_ok = check_db_connection()
    if not db_ok:
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "reason": "database unavailable"},
        )
    return {"status": "ready", "version": settings.VERSION}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HealthSaathi API",
        "version": settings.VERSION,
        "docs": "/api/docs",
    }
