"""
Authentication endpoints for user registration and login
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, UserLogin, TokenResponse, TokenRefresh
from app.models.user import User
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.dependencies import get_current_user, BLACKLISTED_TOKENS
from app.core.limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def register_user(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    Args:
        user_data: User registration data (name, email, password, role)
        db: Database session
        
    Returns:
        UserResponse: Created user information (without password)
        
    Raises:
        HTTPException 400: If email already exists
        HTTPException 500: If database error occurs
    """
    try:
        # Check if user with email already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            logger.warning(f"Registration attempt with existing email: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash the password
        password_hash = get_password_hash(user_data.password)
        
        # Create new user
        new_user = User(
            name=user_data.name,
            email=user_data.email,
            password_hash=password_hash,
            role=user_data.role
        )
        
        # Add to database
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"User registered successfully: {new_user.email} (ID: {new_user.id})")
        
        return new_user
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration"
        )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login_user(
    request: Request,
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and generate JWT tokens.
    
    Args:
        login_data: User login credentials (email, password)
        db: Database session
        
    Returns:
        TokenResponse: Access token, refresh token, and user information
        
    Raises:
        HTTPException 401: If credentials are invalid
        HTTPException 500: If database error occurs
    """
    try:
        # Find user by email
        user = db.query(User).filter(User.email == login_data.email).first()
        
        # Validate credentials
        if not user or not verify_password(login_data.password, user.password_hash):
            logger.warning(f"Failed login attempt for email: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Generate JWT tokens
        token_data = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value,
            "token_version": user.token_version,
        }

        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)
        
        logger.info(f"User logged in successfully: {user.email} (ID: {user.id})")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    Args:
        token_data: Refresh token
        db: Database session
        
    Returns:
        TokenResponse: New access token, refresh token, and user information
        
    Raises:
        HTTPException 401: If refresh token is invalid or expired
        HTTPException 500: If database error occurs
    """
    try:
        # Decode and validate refresh token
        payload = decode_token(token_data.refresh_token)
        
        if payload is None:
            logger.warning("Invalid or expired refresh token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # Verify token type
        token_type = payload.get("type")
        if token_type != "refresh":
            logger.warning(f"Invalid token type for refresh: {token_type}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Extract user info
        user_id = payload.get("user_id")
        if user_id is None:
            logger.warning("Refresh token missing user_id")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Fetch user from database
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            logger.warning(f"User not found for ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        # Verify the refresh token has not been revoked.
        # token_version is bumped on password change / session revocation;
        # a stale refresh token must be rejected even if its signature is valid.
        token_version: int = payload.get("token_version", 0)
        if token_version != user.token_version:
            logger.warning(
                f"Revoked refresh token used by user {user.email} (ID: {user.id})"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )

        # Generate new tokens
        new_token_data = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value,
            "token_version": user.token_version,
        }

        access_token = create_access_token(data=new_token_data)
        refresh_token = create_refresh_token(data=new_token_data)
        
        logger.info(f"Token refreshed for user: {user.email} (ID: {user.id})")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during token refresh"
        )


_bearer = HTTPBearer()


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    _current_user: User = Depends(get_current_user),
):
    """
    Logout the current user by blacklisting the token's JTI.

    get_current_user already validates the token, so by the time we reach
    this handler the token is guaranteed to be valid and not already revoked.
    """
    payload = decode_token(credentials.credentials)
    jti: str | None = payload.get("jti") if payload else None
    if jti:
        BLACKLISTED_TOKENS.add(jti)
        logger.info(f"Token JTI blacklisted for user ID {_current_user.id}: {jti}")
    return {"message": "Logged out successfully"}
