"""
Configuration for MonitorPy FastAPI implementation.

This module provides configuration settings using Pydantic's BaseSettings.
"""

import os
from typing import Optional

from pydantic import BaseSettings, PostgresDsn, SqliteGsn, validator


class Settings(BaseSettings):
    """Application settings."""
    
    # API settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "MonitorPy API"
    DEBUG: bool = False
    
    # Database settings
    DATABASE_URL: Optional[str] = None
    
    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v, values):
        """
        Validate and set default database URL.
        
        If not provided, defaults to SQLite in the current directory.
        """
        if v:
            return v
        return "sqlite:///./monitorpy.db"
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Pagination settings
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    class Config:
        """Pydantic config."""
        
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()