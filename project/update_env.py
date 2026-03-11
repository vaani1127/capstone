"""Helper script to update .env file with actual credentials"""
import secrets
from pathlib import Path

print("=== HealthSaathi Backend Configuration ===\n")

# Get database password
print("Enter the password you set for PostgreSQL user 'healthsaathi_user':")
db_password = input("Password: ").strip()

# Generate a secure SECRET_KEY
secret_key = secrets.token_urlsafe(32)

# Read current .env
env_file = Path('backend/.env')
env_content = env_file.read_text()

# Update DATABASE_URL
env_content = env_content.replace(
    'DATABASE_URL=postgresql://healthsaathi_user:your_password@localhost:5432/healthsaathi_db',
    f'DATABASE_URL=postgresql://healthsaathi_user:{db_password}@localhost:5432/healthsaathi_db'
)

# Update SECRET_KEY
env_content = env_content.replace(
    'SECRET_KEY=your-secret-key-here-change-in-production-min-32-chars',
    f'SECRET_KEY={secret_key}'
)

# Write back
env_file.write_text(env_content)

print("\n✓ Configuration updated successfully!")
print(f"✓ DATABASE_URL configured for user 'healthsaathi_user'")
print(f"✓ SECRET_KEY generated: {secret_key[:20]}...")
print("\nYou can now run: python test_db_connection.py")
