"""
Tests for authentication endpoints
"""
import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta

# Set environment variables before importing app
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User, UserRole
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    decode_token
)
from jose import jwt
from app.core.config import settings

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestUserRegistration:
    """Test cases for user registration endpoint"""
    
    def test_register_user_success(self):
        """Test successful user registration"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "John Doe",
                "email": "john.doe@example.com",
                "password": "SecurePass123",
                "role": "Patient"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "John Doe"
        assert data["email"] == "john.doe@example.com"
        assert data["role"] == "Patient"
        assert "id" in data
        assert "password" not in data
        assert "password_hash" not in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_register_user_password_hashed(self):
        """Test that password is properly hashed in database"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Jane Smith",
                "email": "jane.smith@example.com",
                "password": "MyPassword456",
                "role": "Doctor"
            }
        )
        
        assert response.status_code == 201
        
        # Verify password is hashed in database
        db = TestingSessionLocal()
        user = db.query(User).filter(User.email == "jane.smith@example.com").first()
        assert user is not None
        assert user.password_hash != "MyPassword456"
        assert verify_password("MyPassword456", user.password_hash)
        db.close()
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email fails"""
        # Register first user
        client.post(
            "/api/v1/auth/register",
            json={
                "name": "User One",
                "email": "duplicate@example.com",
                "password": "Password123",
                "role": "Patient"
            }
        )
        
        # Try to register with same email
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "User Two",
                "email": "duplicate@example.com",
                "password": "DifferentPass456",
                "role": "Doctor"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_invalid_email(self):
        """Test registration with invalid email format"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Test User",
                "email": "not-an-email",
                "password": "Password123",
                "role": "Patient"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_register_weak_password_too_short(self):
        """Test registration with password too short"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "password": "Pass1",
                "role": "Patient"
            }
        )
        
        assert response.status_code == 422
        assert "at least 8 characters" in str(response.json()).lower()
    
    def test_register_weak_password_no_uppercase(self):
        """Test registration with password missing uppercase letter"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "password": "password123",
                "role": "Patient"
            }
        )
        
        assert response.status_code == 422
        assert "uppercase" in str(response.json()).lower()
    
    def test_register_weak_password_no_lowercase(self):
        """Test registration with password missing lowercase letter"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "password": "PASSWORD123",
                "role": "Patient"
            }
        )
        
        assert response.status_code == 422
        assert "lowercase" in str(response.json()).lower()
    
    def test_register_weak_password_no_digit(self):
        """Test registration with password missing digit"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "password": "PasswordOnly",
                "role": "Patient"
            }
        )
        
        assert response.status_code == 422
        assert "digit" in str(response.json()).lower()
    
    def test_register_missing_name(self):
        """Test registration without name"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "Password123",
                "role": "Patient"
            }
        )
        
        assert response.status_code == 422
    
    def test_register_missing_role(self):
        """Test registration without role"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "password": "Password123"
            }
        )
        
        assert response.status_code == 422
    
    def test_register_invalid_role(self):
        """Test registration with invalid role"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "password": "Password123",
                "role": "InvalidRole"
            }
        )
        
        assert response.status_code == 422
    
    def test_register_all_valid_roles(self):
        """Test registration with all valid roles"""
        roles = ["Admin", "Doctor", "Nurse", "Patient"]
        
        for idx, role in enumerate(roles):
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "name": f"User {role}",
                    "email": f"user.{role.lower()}@example.com",
                    "password": "Password123",
                    "role": role
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["role"] == role
    
    def test_register_empty_name(self):
        """Test registration with empty name"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "",
                "email": "test@example.com",
                "password": "Password123",
                "role": "Patient"
            }
        )
        
        assert response.status_code == 422



class TestUserLogin:
    """Test cases for user login endpoint"""
    
    def test_login_success(self):
        """Test successful user login"""
        # Register a user first
        client.post(
            "/api/v1/auth/register",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "password": "Password123",
                "role": "Patient"
            }
        )
        
        # Login with correct credentials
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "Password123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["role"] == "Patient"
        assert "password" not in data["user"]
        assert "password_hash" not in data["user"]
    
    def test_login_invalid_email(self):
        """Test login with non-existent email"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "Password123"
            }
        )
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_login_invalid_password(self):
        """Test login with incorrect password"""
        # Register a user first
        client.post(
            "/api/v1/auth/register",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "password": "CorrectPassword123",
                "role": "Doctor"
            }
        )
        
        # Try to login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword456"
            }
        )
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_login_missing_email(self):
        """Test login without email"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "password": "Password123"
            }
        )
        
        assert response.status_code == 422
    
    def test_login_missing_password(self):
        """Test login without password"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com"
            }
        )
        
        assert response.status_code == 422
    
    def test_login_invalid_email_format(self):
        """Test login with invalid email format"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "not-an-email",
                "password": "Password123"
            }
        )
        
        assert response.status_code == 422
    
    def test_login_jwt_token_contains_user_info(self):
        """Test that JWT token contains correct user information"""
        from jose import jwt
        from app.core.config import settings
        
        # Register a user
        client.post(
            "/api/v1/auth/register",
            json={
                "name": "Token Test User",
                "email": "tokentest@example.com",
                "password": "Password123",
                "role": "Admin"
            }
        )
        
        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "tokentest@example.com",
                "password": "Password123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Decode access token
        access_token = data["access_token"]
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert payload["email"] == "tokentest@example.com"
        assert payload["role"] == "Admin"
        assert "user_id" in payload
        assert "exp" in payload
        assert payload["type"] == "access"
    
    def test_login_refresh_token_contains_user_info(self):
        """Test that refresh token contains correct user information"""
        from jose import jwt
        from app.core.config import settings
        
        # Register a user
        client.post(
            "/api/v1/auth/register",
            json={
                "name": "Refresh Test User",
                "email": "refreshtest@example.com",
                "password": "Password123",
                "role": "Nurse"
            }
        )
        
        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "refreshtest@example.com",
                "password": "Password123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Decode refresh token
        refresh_token = data["refresh_token"]
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert payload["email"] == "refreshtest@example.com"
        assert payload["role"] == "Nurse"
        assert "user_id" in payload
        assert "exp" in payload
        assert payload["type"] == "refresh"
    
    def test_login_multiple_users_different_roles(self):
        """Test login for users with different roles"""
        users = [
            {"name": "Admin User", "email": "admin@example.com", "password": "AdminPass123", "role": "Admin"},
            {"name": "Doctor User", "email": "doctor@example.com", "password": "DoctorPass123", "role": "Doctor"},
            {"name": "Nurse User", "email": "nurse@example.com", "password": "NursePass123", "role": "Nurse"},
            {"name": "Patient User", "email": "patient@example.com", "password": "PatientPass123", "role": "Patient"}
        ]
        
        # Register all users
        for user in users:
            client.post("/api/v1/auth/register", json=user)
        
        # Login each user and verify
        for user in users:
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": user["email"],
                    "password": user["password"]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["user"]["email"] == user["email"]
            assert data["user"]["role"] == user["role"]
            assert "access_token" in data
            assert "refresh_token" in data
    
    def test_login_case_sensitive_password(self):
        """Test that password is case-sensitive"""
        # Register a user
        client.post(
            "/api/v1/auth/register",
            json={
                "name": "Case Test User",
                "email": "casetest@example.com",
                "password": "Password123",
                "role": "Patient"
            }
        )
        
        # Try to login with different case password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "casetest@example.com",
                "password": "password123"  # lowercase 'p'
            }
        )
        
        assert response.status_code == 401
    
    def test_login_empty_password(self):
        """Test login with empty password"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": ""
            }
        )
        
        # Empty password is accepted by validation but fails authentication
        assert response.status_code == 401



class TestTokenRefresh:
    """Test cases for token refresh endpoint"""
    
    def test_refresh_token_success(self):
        """Test successful token refresh"""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "name": "Refresh User",
                "email": "refresh@example.com",
                "password": "Password123",
                "role": "Patient"
            }
        )
        
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "refresh@example.com",
                "password": "Password123"
            }
        )
        
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh the token
        response = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": refresh_token
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == "refresh@example.com"
    
    def test_refresh_token_invalid(self):
        """Test refresh with invalid token"""
        response = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": "invalid.token.here"
            }
        )
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_refresh_token_with_access_token(self):
        """Test that access token cannot be used for refresh"""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "password": "Password123",
                "role": "Patient"
            }
        )
        
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "Password123"
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Try to refresh with access token
        response = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": access_token
            }
        )
        
        assert response.status_code == 401
        assert "invalid token type" in response.json()["detail"].lower()
    
    def test_refresh_token_expired(self):
        """Test refresh with expired token"""
        from jose import jwt
        from app.core.config import settings
        from datetime import datetime, timedelta
        
        # Create an expired refresh token
        expired_payload = {
            "user_id": 999,
            "email": "expired@example.com",
            "role": "Patient",
            "type": "refresh",
            "exp": datetime.utcnow() - timedelta(days=1)  # Expired yesterday
        }
        
        expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        response = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": expired_token
            }
        )
        
        assert response.status_code == 401
    
    def test_refresh_token_nonexistent_user(self):
        """Test refresh with token for non-existent user"""
        from jose import jwt
        from app.core.config import settings
        from datetime import datetime, timedelta
        
        # Create a token for non-existent user
        payload = {
            "user_id": 99999,
            "email": "nonexistent@example.com",
            "role": "Patient",
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=7)
        }
        
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        response = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": token
            }
        )
        
        assert response.status_code == 401
        assert "user not found" in response.json()["detail"].lower()


class TestJWTValidation:
    """Test cases for JWT token validation on protected endpoints"""
    
    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == 401  # No credentials provided
    
    def test_protected_endpoint_with_valid_token(self):
        """Test accessing protected endpoint with valid token"""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "name": "Protected User",
                "email": "protected@example.com",
                "password": "Password123",
                "role": "Patient"
            }
        )
        
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "protected@example.com",
                "password": "Password123"
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Access protected endpoint
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "protected@example.com"
        assert data["role"] == "Patient"
    
    def test_protected_endpoint_with_invalid_token(self):
        """Test accessing protected endpoint with invalid token"""
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_protected_endpoint_with_expired_token(self):
        """Test accessing protected endpoint with expired token"""
        from jose import jwt
        from app.core.config import settings
        from datetime import datetime, timedelta
        
        # Create an expired access token
        expired_payload = {
            "user_id": 999,
            "email": "expired@example.com",
            "role": "Patient",
            "type": "access",
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        }
        
        expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401
    
    def test_protected_endpoint_with_refresh_token(self):
        """Test that refresh token cannot be used for protected endpoints"""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "password": "Password123",
                "role": "Patient"
            }
        )
        
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "Password123"
            }
        )
        
        refresh_token = login_response.json()["refresh_token"]
        
        # Try to access protected endpoint with refresh token
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {refresh_token}"}
        )
        
        assert response.status_code == 401
        assert "invalid token type" in response.json()["detail"].lower()
    
    def test_protected_endpoint_with_malformed_header(self):
        """Test accessing protected endpoint with malformed Authorization header"""
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": "InvalidFormat token"}
        )
        
        assert response.status_code == 401
    
    def test_protected_endpoint_nonexistent_user(self):
        """Test accessing protected endpoint with token for deleted user"""
        from jose import jwt
        from app.core.config import settings
        from datetime import datetime, timedelta
        
        # Create a token for non-existent user
        payload = {
            "user_id": 99999,
            "email": "deleted@example.com",
            "role": "Patient",
            "type": "access",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 401
        assert "user not found" in response.json()["detail"].lower()


class TestRoleBasedAccessControl:
    """Test cases for role-based access control"""
    
    def test_admin_only_endpoint_with_admin(self):
        """Test admin-only endpoint with admin user"""
        # Register admin user
        client.post(
            "/api/v1/auth/register",
            json={
                "name": "Admin User",
                "email": "admin@example.com",
                "password": "AdminPass123",
                "role": "Admin"
            }
        )
        
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@example.com",
                "password": "AdminPass123"
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Access admin-only endpoint
        response = client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_admin_only_endpoint_with_patient(self):
        """Test admin-only endpoint with patient user (should fail)"""
        # Register patient user
        client.post(
            "/api/v1/auth/register",
            json={
                "name": "Patient User",
                "email": "patient@example.com",
                "password": "PatientPass123",
                "role": "Patient"
            }
        )
        
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "patient@example.com",
                "password": "PatientPass123"
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Try to access admin-only endpoint
        response = client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()
    
    def test_admin_only_endpoint_with_doctor(self):
        """Test admin-only endpoint with doctor user (should fail)"""
        # Register doctor user
        client.post(
            "/api/v1/auth/register",
            json={
                "name": "Doctor User",
                "email": "doctor@example.com",
                "password": "DoctorPass123",
                "role": "Doctor"
            }
        )
        
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "doctor@example.com",
                "password": "DoctorPass123"
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Try to access admin-only endpoint
        response = client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 403
    
    def test_admin_only_endpoint_with_nurse(self):
        """Test admin-only endpoint with nurse user (should fail)"""
        # Register nurse user
        client.post(
            "/api/v1/auth/register",
            json={
                "name": "Nurse User",
                "email": "nurse@example.com",
                "password": "NursePass123",
                "role": "Nurse"
            }
        )
        
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nurse@example.com",
                "password": "NursePass123"
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Try to access admin-only endpoint
        response = client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 403
    
    def test_all_roles_can_access_own_info(self):
        """Test that all roles can access their own user info"""
        roles = ["Admin", "Doctor", "Nurse", "Patient"]
        
        for role in roles:
            # Register user
            email = f"{role.lower()}@example.com"
            client.post(
                "/api/v1/auth/register",
                json={
                    "name": f"{role} User",
                    "email": email,
                    "password": f"{role}Pass123",
                    "role": role
                }
            )
            
            # Login
            login_response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": email,
                    "password": f"{role}Pass123"
                }
            )
            
            access_token = login_response.json()["access_token"]
            
            # Access own info
            response = client.get(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == email
            assert data["role"] == role



class TestPasswordHashing:
    """Test cases for password hashing functions"""
    
    def test_password_hash_generation(self):
        """Test that password hashing generates a hash"""
        password = "TestPassword123"
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
        assert isinstance(hashed, str)
    
    def test_password_hash_different_for_same_password(self):
        """Test that same password generates different hashes (due to salt)"""
        password = "SamePassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different due to random salt
        assert hash1 != hash2
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "CorrectPassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "CorrectPassword123"
        wrong_password = "WrongPassword456"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive"""
        password = "CaseSensitive123"
        hashed = get_password_hash(password)
        
        assert verify_password("casesensitive123", hashed) is False
        assert verify_password("CASESENSITIVE123", hashed) is False
    
    def test_password_hash_handles_special_characters(self):
        """Test password hashing with special characters"""
        password = "P@ssw0rd!#$%^&*()"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_password_hash_handles_unicode(self):
        """Test password hashing with unicode characters"""
        password = "Pässwörd123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_password_hash_handles_long_passwords(self):
        """Test password hashing with very long passwords"""
        password = "A" * 100 + "1"
        hashed = get_password_hash(password)
        
        # Bcrypt truncates at 72 bytes, both hashing and verification handle this
        assert verify_password(password, hashed) is True
    
    def test_password_hash_empty_string(self):
        """Test password hashing with empty string"""
        password = ""
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True


class TestJWTTokenGeneration:
    """Test cases for JWT token generation functions"""
    
    def test_create_access_token_basic(self):
        """Test basic access token creation"""
        data = {
            "user_id": 1,
            "email": "test@example.com",
            "role": "Patient"
        }
        
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_contains_data(self):
        """Test that access token contains the provided data"""
        data = {
            "user_id": 123,
            "email": "user@example.com",
            "role": "Doctor"
        }
        
        token = create_access_token(data)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert payload["user_id"] == 123
        assert payload["email"] == "user@example.com"
        assert payload["role"] == "Doctor"
    
    def test_create_access_token_has_expiration(self):
        """Test that access token has expiration time"""
        data = {"user_id": 1, "email": "test@example.com", "role": "Patient"}
        
        token = create_access_token(data)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert "exp" in payload
        assert isinstance(payload["exp"], (int, float))
    
    def test_create_access_token_has_type(self):
        """Test that access token has type field"""
        data = {"user_id": 1, "email": "test@example.com", "role": "Patient"}
        
        token = create_access_token(data)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert payload["type"] == "access"
    
    def test_create_access_token_custom_expiration(self):
        """Test access token creation with custom expiration"""
        data = {"user_id": 1, "email": "test@example.com", "role": "Patient"}
        custom_delta = timedelta(hours=2)
        
        token = create_access_token(data, expires_delta=custom_delta)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Check that expiration is approximately 2 hours from now
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        expected_time = datetime.utcnow() + custom_delta
        time_diff = abs((exp_time - expected_time).total_seconds())
        
        assert time_diff < 5  # Within 5 seconds tolerance
    
    def test_create_refresh_token_basic(self):
        """Test basic refresh token creation"""
        data = {
            "user_id": 1,
            "email": "test@example.com",
            "role": "Patient"
        }
        
        token = create_refresh_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token_contains_data(self):
        """Test that refresh token contains the provided data"""
        data = {
            "user_id": 456,
            "email": "refresh@example.com",
            "role": "Nurse"
        }
        
        token = create_refresh_token(data)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert payload["user_id"] == 456
        assert payload["email"] == "refresh@example.com"
        assert payload["role"] == "Nurse"
    
    def test_create_refresh_token_has_type(self):
        """Test that refresh token has type field"""
        data = {"user_id": 1, "email": "test@example.com", "role": "Patient"}
        
        token = create_refresh_token(data)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert payload["type"] == "refresh"
    
    def test_create_refresh_token_longer_expiration(self):
        """Test that refresh token has longer expiration than access token"""
        data = {"user_id": 1, "email": "test@example.com", "role": "Patient"}
        
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)
        
        access_payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        refresh_payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Refresh token should expire later than access token
        assert refresh_payload["exp"] > access_payload["exp"]
    
    def test_tokens_with_different_data_are_unique(self):
        """Test that tokens with different data are unique"""
        data1 = {"user_id": 1, "email": "test1@example.com", "role": "Patient"}
        data2 = {"user_id": 2, "email": "test2@example.com", "role": "Doctor"}
        
        token1 = create_access_token(data1)
        token2 = create_access_token(data2)
        
        # Tokens should be different due to different data
        assert token1 != token2
        
        # Verify each token contains correct data
        payload1 = jwt.decode(token1, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        payload2 = jwt.decode(token2, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert payload1["user_id"] == 1
        assert payload2["user_id"] == 2


class TestJWTTokenDecoding:
    """Test cases for JWT token decoding function"""
    
    def test_decode_valid_token(self):
        """Test decoding a valid token"""
        data = {"user_id": 1, "email": "test@example.com", "role": "Patient"}
        token = create_access_token(data)
        
        payload = decode_token(token)
        
        assert payload is not None
        assert payload["user_id"] == 1
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "Patient"
    
    def test_decode_invalid_token(self):
        """Test decoding an invalid token"""
        invalid_token = "invalid.token.string"
        
        payload = decode_token(invalid_token)
        
        assert payload is None
    
    def test_decode_expired_token(self):
        """Test decoding an expired token"""
        data = {"user_id": 1, "email": "test@example.com", "role": "Patient"}
        expired_delta = timedelta(seconds=-1)  # Already expired
        token = create_access_token(data, expires_delta=expired_delta)
        
        payload = decode_token(token)
        
        assert payload is None
    
    def test_decode_token_with_wrong_secret(self):
        """Test that token signed with different secret fails"""
        data = {"user_id": 1, "email": "test@example.com", "role": "Patient"}
        
        # Create token with different secret
        wrong_token = jwt.encode(
            {**data, "exp": datetime.utcnow() + timedelta(hours=1)},
            "wrong-secret-key",
            algorithm=settings.ALGORITHM
        )
        
        payload = decode_token(wrong_token)
        
        assert payload is None
    
    def test_decode_token_preserves_all_fields(self):
        """Test that decoding preserves all token fields"""
        data = {
            "user_id": 123,
            "email": "test@example.com",
            "role": "Admin",
            "custom_field": "custom_value"
        }
        token = create_access_token(data)
        
        payload = decode_token(token)
        
        assert payload["user_id"] == 123
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "Admin"
        assert payload["custom_field"] == "custom_value"
        assert payload["type"] == "access"
        assert "exp" in payload
    
    def test_decode_refresh_token(self):
        """Test decoding a refresh token"""
        data = {"user_id": 1, "email": "test@example.com", "role": "Patient"}
        token = create_refresh_token(data)
        
        payload = decode_token(token)
        
        assert payload is not None
        assert payload["type"] == "refresh"
    
    def test_decode_malformed_token(self):
        """Test decoding a malformed token"""
        malformed_tokens = [
            "",
            "not.a.token",
            "only-one-part",
            "two.parts",
            None
        ]
        
        for token in malformed_tokens:
            if token is not None:
                payload = decode_token(token)
                assert payload is None
