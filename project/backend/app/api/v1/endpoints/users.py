"""
User management endpoints (protected routes example)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.core.dependencies import get_current_user, require_admin

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    
    This endpoint demonstrates JWT token validation.
    Requires valid access token in Authorization header.
    
    Args:
        current_user: Current authenticated user (injected by dependency)
        
    Returns:
        UserResponse: Current user information
    """
    return current_user


@router.get("/", response_model=list[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    List all users (Admin only).
    
    This endpoint demonstrates role-based access control.
    Requires valid access token with Admin role.
    
    Args:
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        List[UserResponse]: List of all users
    """
    users = db.query(User).all()
    return users
