"""
Check model for the MonitorPy FastAPI implementation.

This module defines the SQLAlchemy Check model and Pydantic schemas.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Boolean, DateTime, Text, func
from sqlalchemy.orm import relationship

from monitorpy.fastapi_api.database import Base


class Check(Base):
    """
    SQLAlchemy model representing a configured monitoring check.
    
    This stores the configuration for a monitoring check that can be
    executed on demand or on a schedule.
    """
    
    __tablename__ = 'checks'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    plugin_type = Column(String(50), nullable=False)
    config = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True)
    schedule = Column(String(50), nullable=True)
    last_run = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationship will be implemented once Result model is created
    # results = relationship("Result", back_populates="check", cascade="all, delete-orphan")
    
    def get_config(self) -> dict:
        """
        Get the configuration as a dictionary.
        
        Returns:
            dict: Check configuration
        """
        return json.loads(self.config)
    
    def set_config(self, config: dict) -> None:
        """
        Set the configuration from a dictionary.
        
        Args:
            config: Configuration dictionary
        """
        self.config = json.dumps(config)


# Pydantic models for request/response validation
class CheckBase(BaseModel):
    """Base model for check data."""
    
    name: str
    plugin_type: str
    config: Dict[str, Any]
    enabled: bool = True
    schedule: Optional[str] = None


class CheckCreate(CheckBase):
    """Model for creating a new check."""
    
    pass


class CheckUpdate(BaseModel):
    """Model for updating an existing check."""
    
    name: Optional[str] = None
    plugin_type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None
    schedule: Optional[str] = None


class CheckInDB(CheckBase):
    """Model for check data from database."""
    
    id: str
    last_run: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        
        orm_mode = True


class PaginatedChecks(BaseModel):
    """Model for paginated checks response."""
    
    checks: List[CheckInDB]
    page: int
    per_page: int
    total: int
    pages: int