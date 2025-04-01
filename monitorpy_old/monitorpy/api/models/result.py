"""
Result model for the MonitorPy API.

This module defines the Result model for storing check results.
"""

import json
import uuid
from datetime import datetime

from monitorpy.api.extensions import db
from monitorpy.core.result import CheckResult


class Result(db.Model):
    """
    Model representing a monitoring check result.
    
    This stores the results of executing a monitoring check.
    """
    
    __tablename__ = 'results'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    check_id = db.Column(db.String(36), db.ForeignKey('checks.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response_time = db.Column(db.Float, nullable=False)
    raw_data = db.Column(db.Text, nullable=True)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, check_id, status, message, response_time, raw_data=None):
        """
        Initialize a new Result.
        
        Args:
            check_id: ID of the check that produced this result
            status: Status of the check (success, warning, error)
            message: Human-readable message
            response_time: Time taken for the check in seconds
            raw_data: Additional data related to the check
        """
        self.id = str(uuid.uuid4())
        self.check_id = check_id
        self.status = status
        self.message = message
        self.response_time = response_time
        
        # Store raw_data as JSON string
        if raw_data:
            if isinstance(raw_data, dict):
                self.raw_data = json.dumps(raw_data)
            else:
                self.raw_data = raw_data
    
    def get_raw_data(self):
        """
        Get the raw data as a dictionary.
        
        Returns:
            dict: Raw data or empty dict if none
        """
        if self.raw_data:
            return json.loads(self.raw_data)
        return {}
    
    def to_dict(self):
        """
        Convert the result to a dictionary.
        
        Returns:
            dict: Result data
        """
        return {
            'id': self.id,
            'check_id': self.check_id,
            'status': self.status,
            'message': self.message,
            'response_time': self.response_time,
            'raw_data': self.get_raw_data(),
            'executed_at': self.executed_at.isoformat()
        }
    
    @classmethod
    def from_check_result(cls, check_id, check_result):
        """
        Create a Result from a CheckResult object.
        
        Args:
            check_id: ID of the check
            check_result: CheckResult object
            
        Returns:
            Result: New Result instance
        """
        return cls(
            check_id=check_id,
            status=check_result.status,
            message=check_result.message,
            response_time=check_result.response_time,
            raw_data=check_result.raw_data
        )
    
    def to_check_result(self):
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
    
    def __repr__(self):
        """Get string representation."""
        return f"<Result {self.id} ({self.status})>"