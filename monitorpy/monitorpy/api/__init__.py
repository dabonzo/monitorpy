"""
API module for MonitorPy.

This module provides a REST API for accessing MonitorPy functionality.
"""

from monitorpy.api.app import create_app

__all__ = ["create_app"]