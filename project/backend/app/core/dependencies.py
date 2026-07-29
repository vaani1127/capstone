"""
Authentication and authorization dependencies for FastAPI
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User, UserRole
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()

# In-memory JTI blacklist for revoked tokens.
# TODO: replace with Redis (or another shared store) in production so that
#       revocations are visible across all worker processes.
BLACKLISTED_TOKENS: set[str] = set()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Validate JWT token and return current user.
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException 401: If token is invalid, expired, or user not found
    """
    token = credentials.credentials
    
    # Decode and validate token
    payload = decode_token(token)
    
    if payload is None:
        logger.warning("Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Reject blacklisted tokens (logged-out JTIs)
    jti: str | None = payload.get("jti")
    if jti and jti in BLACKLISTED_TOKENS:
        logger.warning(f"Blacklisted token JTI used: {jti}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token type
    token_type = payload.get("type")
    if token_type != "access":
        logger.warning(f"Invalid token type: {token_type}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user info
    user_id: Optional[int] = payload.get("user_id")
    if user_id is None:
        logger.warning("Token missing user_id")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        logger.warning(f"User not found for ID: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning(f"Inactive user attempted login: {user.email} (ID: {user.id})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token has not been revoked (e.g. after deactivation/reactivation)
    token_version: int = payload.get("token_version", 0)
    if token_version != user.token_version:
        logger.warning(f"Revoked token used by user {user.email} (ID: {user.id})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug(f"Authenticated user: {user.email} (ID: {user.id})")
    return user


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory to enforce role-based access control.
    
    Args:
        *allowed_roles: Variable number of UserRole values that are allowed
        
    Returns:
        Dependency function that validates user role
        
    Example:
        @router.get("/doctors-only", dependencies=[Depends(require_role(UserRole.DOCTOR))])
        async def doctors_only_endpoint():
            pass
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        """
        Check if current user has required role.
        
        Args:
            current_user: Current authenticated user
            
        Returns:
            User: Current user if authorized
            
        Raises:
            HTTPException 403: If user doesn't have required role
        """
        if current_user.role not in allowed_roles:
            logger.warning(
                f"Unauthorized access attempt by user {current_user.email} "
                f"(role: {current_user.role.value}) to endpoint requiring roles: "
                f"{[role.value for role in allowed_roles]}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {[role.value for role in allowed_roles]}"
            )
        
        return current_user
    
    return role_checker


# Convenience dependencies for specific roles
async def require_admin(current_user: User = Depends(require_role(UserRole.ADMIN))) -> User:
    """Require Admin role"""
    return current_user


async def require_doctor(current_user: User = Depends(require_role(UserRole.DOCTOR))) -> User:
    """Require Doctor role"""
    return current_user


async def require_nurse(current_user: User = Depends(require_role(UserRole.NURSE))) -> User:
    """Require Nurse role"""
    return current_user


async def require_patient(current_user: User = Depends(require_role(UserRole.PATIENT))) -> User:
    """Require Patient role"""
    return current_user


async def require_staff(
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE))
) -> User:
    """Require any staff role (Admin, Doctor, or Nurse)"""
    return current_user
