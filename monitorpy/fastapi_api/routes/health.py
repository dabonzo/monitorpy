"""
Health check endpoints for the MonitorPy FastAPI implementation.

This module defines API endpoints for health checks.
"""

from fastapi import APIRouter


router = APIRouter()


@router.get("")
async def health_check():
    """
    Simple health check endpoint.
    
    Returns information about the API status.
    """
    return {
        "status": "ok",
        "message": "MonitorPy API is running"
    }