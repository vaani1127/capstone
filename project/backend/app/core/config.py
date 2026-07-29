"""
Application configuration management
"""
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, field_validator, AnyUrl


class Settings(BaseSettings):
    """Application settings"""

    # Project Info
    PROJECT_NAME: str = "HealthSaathi API"
    VERSION: str = "1.0.0"

    # Database - Allow any URL for testing
    DATABASE_URL: Union[PostgresDsn, AnyUrl]

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters. "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        return v
    
    # CORS — never set to "*" in production (see cors_origins property below)
    ALLOWED_ORIGINS: str = ""

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    _DEV_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
    ]

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development" or self.DEBUG

    @property
    def cors_origins(self) -> List[str]:
        """
        Return the list of allowed CORS origins.

        Development  → fixed localhost origins, no config required.
        Production   → read from ALLOWED_ORIGINS env var (comma-separated).
                       Raises RuntimeError at startup if the var is absent or
                       empty so the app never starts with an open CORS policy.
        Wildcards are rejected in all environments.
        """
        if self.is_development:
            return self._DEV_ORIGINS

        # Production path
        raw = self.ALLOWED_ORIGINS.strip()
        if not raw:
            raise RuntimeError(
                "ALLOWED_ORIGINS must be set to a non-empty comma-separated list "
                "of origins in production. The app will not start without it."
            )

        origins = [o.strip() for o in raw.split(",") if o.strip()]
        if "*" in origins:
            raise RuntimeError(
                "Wildcard '*' is not permitted in ALLOWED_ORIGINS. "
                "Provide explicit origin URLs."
            )
        return origins
    
    class Config:
        from pathlib import Path
        # Look for .env in backend directory
        backend_dir = Path(__file__).parent.parent.parent
        env_file = str(backend_dir / ".env")
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields like HOST and PORT


settings = Settings()
