"""
Pytest configuration file for MonitorPy tests.

This file contains fixtures and setup for all tests.
"""

import pytest
from typing import Dict, Generator
import os
import tempfile
from unittest.mock import patch


@pytest.fixture
def mock_redis():
    """Mock Redis for testing."""
    with patch("monitorpy.fastapi_api.redis.Redis") as mock:
        # Configure mock
        mock.return_value.ping.return_value = True
        mock.return_value.get.return_value = None
        mock.return_value.set.return_value = True
        yield mock


@pytest.fixture
def mock_access_token() -> str:
    """Generate a dummy access token for testing."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJleHAiOjk5OTk5OTk5OTl9.tWGgbp4N7xQgSXRHdVjUYToCMJ9n1nRLAXjX3K40QXM"


@pytest.fixture
def mock_auth_headers(mock_access_token: str) -> Dict[str, str]:
    """Create mock auth headers with Bearer token."""
    return {"Authorization": f"Bearer {mock_access_token}"}


@pytest.fixture
def temp_db_path() -> Generator[str, None, None]:
    """Create a temporary database file for testing."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a path for the database file
        db_path = os.path.join(temp_dir, "test.db")
        db_url = f"sqlite:///{db_path}"
        
        # Set environment variable
        old_db_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = db_url
        
        yield db_url
        
        # Restore original environment variable
        if old_db_url:
            os.environ["DATABASE_URL"] = old_db_url
        else:
            os.environ.pop("DATABASE_URL", None)