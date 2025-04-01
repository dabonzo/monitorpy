"""
Result model for the MonitorPy FastAPI implementation.

This module defines the SQLAlchemy Result model and Pydantic schemas.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from pydantic import BaseModel
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship

from monitorpy.core.result import CheckResult
from monitorpy.fastapi_api.database import Base


class Result(Base):
    """
    SQLAlchemy model representing a monitoring check result.
    
    This stores the results of executing a monitoring check.
    """
    
    __tablename__ = 'results'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    check_id = Column(String(36), ForeignKey('checks.id'), nullable=False)
    status = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    response_time = Column(Float, nullable=False)
    raw_data = Column(Text, nullable=True)
    executed_at = Column(DateTime, default=func.now())
    
    # Relationship will be implemented once Check model is imported
    # check = relationship("Check", back_populates="results")
    
    def get_raw_data(self) -> dict:
        """
        Get the raw data as a dictionary.
        
        Returns:
            dict: Raw data or empty dict if none
        """
        if self.raw_data:
            return json.loads(self.raw_data)
        return {}
    
    @classmethod
    def from_check_result(cls, check_id: str, check_result: CheckResult):
        """
        Create a Result from a CheckResult object.
        
        Args:
            check_id: ID of the check
            check_result: CheckResult object
            
        Returns:
            Result: New Result instance
        """
        result = cls()
        result.id = str(uuid.uuid4())
        result.check_id = check_id
        result.status = check_result.status
        result.message = check_result.message
        result.response_time = check_result.response_time
        
        # Store raw_data as JSON string
        if check_result.raw_data:
            result.raw_data = json.dumps(check_result.raw_data)
        
        return result
    
    def to_check_result(self) -> CheckResult:
        """
        Convert to a CheckResult object.
        
        Returns:
            CheckResult: Equivalent CheckResult object
        """
        return CheckResult(
            status=self.status,
            message=self.message,
            response_time=self.response_time,
            raw_data=self.get_raw_data()
        )


# Pydantic models for request/response validation
class ResultBase(BaseModel):
    """Base model for result data."""
    
    check_id: str
    status: str
    message: str
    response_time: float
    raw_data: Optional[Dict[str, Any]] = None


class ResultCreate(ResultBase):
    """Model for creating a new result."""
    
    pass


class ResultInDB(ResultBase):
    """Model for result data from database."""
    
    id: str
    executed_at: datetime
    
    class Config:
        """Pydantic config."""
        
        orm_mode = True


class PaginatedResults(BaseModel):
    """Model for paginated results response."""
    
    results: List[ResultInDB]
    page: int
    per_page: int
    total: int
    pages: int