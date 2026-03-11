"""Create a test admin user for HealthSaathi"""
from passlib.context import CryptContext
from sqlalchemy import create_engine, text
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend/.env
env_path = Path(__file__).parent / 'backend' / '.env'
load_dotenv(env_path)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

try:
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment")
    
    engine = create_engine(database_url)
    
    # Create admin user
    admin_email = "admin@healthsaathi.com"
    admin_password = "admin123"  # Change this in production!
    hashed_password = hash_password(admin_password)
    
    with engine.connect() as conn:
        # Check if user exists
        result = conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": admin_email}
        )
        
        if result.fetchone():
            print(f"✓ User {admin_email} already exists")
        else:
            # Insert admin user
            conn.execute(
                text("""
                    INSERT INTO users (email, hashed_password, full_name, role, is_active)
                    VALUES (:email, :password, :name, :role, true)
                """),
                {
                    "email": admin_email,
                    "password": hashed_password,
                    "name": "Admin User",
                    "role": "admin"
                }
            )
            conn.commit()
            print(f"\n✓ Test admin user created successfully!")
            print(f"  Email: {admin_email}")
            print(f"  Password: {admin_password}")
            print(f"\nYou can now login with these credentials in the mobile app!")
            
except Exception as e:
    print(f"\n✗ Failed to create user!")
    print(f"Error: {e}")
