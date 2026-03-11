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
    
    # CORS
    ALLOWED_ORIGINS: str = "*"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins as a list"""
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        return [self.ALLOWED_ORIGINS]
    
    class Config:
        from pathlib import Path
        # Look for .env in backend directory
        backend_dir = Path(__file__).parent.parent.parent
        env_file = str(backend_dir / ".env")
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields like HOST and PORT


settings = Settings()
