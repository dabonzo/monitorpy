"""
Result module for storing and processing check results.
"""
from datetime import datetime
from typing import Dict, Any, Optional


class CheckResult:
    """
    Standard result object returned by all check plugins.

    This class provides a consistent structure for check results across all
    monitoring plugins, including status, message, response time, and additional
    data.
    """

    # Status constants
    STATUS_SUCCESS = "success"
    STATUS_WARNING = "warning"
    STATUS_ERROR = "error"

    # Valid status values
    VALID_STATUSES = [STATUS_SUCCESS, STATUS_WARNING, STATUS_ERROR]

    def __init__(
        self,
        status: str,
        message: str,
        response_time: float = 0.0,
        raw_data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new check result.

        Args:
            status: Result status (success, warning, error)
            message: Human-readable result message
            response_time: Time taken for the check in seconds
            raw_data: Additional data related to the check

        Raises:
            ValueError: If the status is not one of the valid values
        """
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of: {', '.join(self.VALID_STATUSES)}")

        self.status = status
        self.message = message
        self.response_time = response_time
        self.raw_data = raw_data or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the result to a dictionary for serialization.

        Returns:
            Dict containing the result data
        """
        return {
            "status": self.status,
            "message": self.message,
            "response_time": self.response_time,
            "raw_data": self.raw_data,
            "timestamp": self.timestamp.isoformat()
        }

    def __str__(self) -> str:
        """
        Get a string representation of the result.

        Returns:
            String representation
        """
        return f"CheckResult({self.status}): {self.message}"

    def is_success(self) -> bool:
        """
        Check if the result status is success.

        Returns:
            True if status is success, False otherwise
        """
        return self.status == self.STATUS_SUCCESS

    def is_warning(self) -> bool:
        """
        Check if the result status is warning.

        Returns:
            True if status is warning, False otherwise
        """
        return self.status == self.STATUS_WARNING

    def is_error(self) -> bool:
        """
        Check if the result status is error.

        Returns:
            True if status is error, False otherwise
        """
        return self.status == self.STATUS_ERROR
