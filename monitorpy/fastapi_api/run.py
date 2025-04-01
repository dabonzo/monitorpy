"""
Script to run the FastAPI application using Uvicorn.

This module provides a function to run the FastAPI app using Uvicorn.
"""

import uvicorn

from monitorpy.fastapi_api.config import settings
from monitorpy.utils.logging import get_logger

logger = get_logger(__name__)


def run_api(host="0.0.0.0", port=8000, reload=False):
    """
    Run the FastAPI application using Uvicorn.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Whether to reload on file changes (for development)
    """
    logger.info(f"Starting MonitorPy FastAPI on {host}:{port}")
    logger.info(f"API documentation available at http://{host}:{port}{settings.API_V1_PREFIX}/docs")
    
    uvicorn.run(
        "monitorpy.fastapi_api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    run_api(reload=True)