"""
FastAPI application for MonitorPy.

This module provides a FastAPI application that exposes MonitorPy functionality
through a REST API with OpenAPI documentation.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from monitorpy.fastapi_api import __version__
from monitorpy.fastapi_api.config import settings
from monitorpy.fastapi_api.database import engine, Base
from monitorpy.fastapi_api.routes import checks, health, plugins, results, batch, auth
from monitorpy.utils.logging import get_logger

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    # Create FastAPI app
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=__version__,
        description="MonitorPy FastAPI implementation with OpenAPI documentation",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Update with your frontend URLs in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Create database tables
    if settings.DATABASE_URL.startswith('sqlite:'):
        # SQLite database - create directory if needed
        db_path = settings.DATABASE_URL.replace('sqlite:///', '')
        if db_path and not db_path.startswith(':memory:'):  # Skip for in-memory database
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    Base.metadata.create_all(bind=engine)
    
    # Register routes
    app.include_router(
        health.router,
        prefix=f"{settings.API_V1_PREFIX}/health",
        tags=["health"],
    )
    
    app.include_router(
        auth.router,
        prefix=f"{settings.API_V1_PREFIX}/auth",
        tags=["auth"],
    )
    
    app.include_router(
        checks.router,
        prefix=f"{settings.API_V1_PREFIX}/checks",
        tags=["checks"],
    )
    
    app.include_router(
        results.router,
        prefix=f"{settings.API_V1_PREFIX}/results",
        tags=["results"],
    )
    
    app.include_router(
        plugins.router,
        prefix=f"{settings.API_V1_PREFIX}/plugins",
        tags=["plugins"],
    )
    
    app.include_router(
        batch.router,
        prefix=f"{settings.API_V1_PREFIX}/batch",
        tags=["batch"],
    )
    
    @app.get("/")
    async def root():
        """Root endpoint returning API information."""
        return {
            "name": settings.PROJECT_NAME,
            "version": __version__,
            "docs": f"{settings.API_V1_PREFIX}/docs",
            "redoc": f"{settings.API_V1_PREFIX}/redoc",
            "endpoints": [
                f"{settings.API_V1_PREFIX}/health",
                f"{settings.API_V1_PREFIX}/auth",
                f"{settings.API_V1_PREFIX}/plugins",
                f"{settings.API_V1_PREFIX}/checks",
                f"{settings.API_V1_PREFIX}/results",
                f"{settings.API_V1_PREFIX}/batch"
            ]
        }
    
    return app


app = create_app()