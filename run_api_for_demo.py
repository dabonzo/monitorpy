#!/usr/bin/env python
"""
Standalone script to run the MonitorPy API for the demo application.

This script provides a simple FastAPI implementation for demo purposes.
"""

import sys
import os
import argparse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the MonitorPy API server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    return parser.parse_args()

def main():
    """Run the API server."""
    args = parse_args()
    
    # Create a simple FastAPI app for the demo
    app = FastAPI(
        title="MonitorPy API",
        description="Demo API for MonitorPy",
        version="1.0.0",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Sample data for the demo
    plugins = [
        {
            "name": "website_status",
            "description": "Check website availability and content",
            "required_config": ["url"],
            "optional_config": ["timeout", "expected_status", "content", "method", "headers"]
        },
        {
            "name": "ssl_certificate",
            "description": "Check SSL certificate validity and expiration",
            "required_config": ["hostname"],
            "optional_config": ["port", "timeout", "warning_days", "critical_days"]
        },
        {
            "name": "dns_record",
            "description": "Check DNS records and propagation",
            "required_config": ["domain", "record_type"],
            "optional_config": ["expected_value", "nameserver", "check_propagation"]
        }
    ]
    
    checks = []
    results = []
    
    # API routes
    @app.get("/api/v1/health")
    async def health():
        return {
            "status": "healthy",
            "database": "connected",
            "version": "1.0.0"
        }
    
    @app.get("/api/v1/plugins")
    async def get_plugins():
        return {
            "plugins": plugins,
            "count": len(plugins)
        }
    
    @app.get("/api/v1/checks")
    async def get_checks():
        return {
            "checks": checks,
            "pagination": {
                "page": 1,
                "per_page": 20,
                "total": len(checks),
                "pages": 1
            }
        }
    
    @app.post("/api/v1/checks", status_code=201)
    async def create_check(check: dict):
        # Mock creating a check
        new_check = {
            "id": f"check_{len(checks) + 1}",
            "name": check.get('name', 'New Check'),
            "plugin_type": check.get('plugin_type', 'unknown'),
            "config": check.get('config', {}),
            "enabled": True,
            "schedule": None,
            "last_run": None,
            "created_at": "2025-04-01T00:00:00Z",
            "updated_at": "2025-04-01T00:00:00Z"
        }
        checks.append(new_check)
        return new_check
    
    @app.delete("/api/v1/checks/{check_id}", status_code=204)
    async def delete_check(check_id: str):
        nonlocal checks
        original_length = len(checks)
        checks = [c for c in checks if c["id"] != check_id]
        if len(checks) == original_length:
            raise HTTPException(status_code=404, detail="Check not found")
        return None
    
    @app.post("/api/v1/checks/{check_id}/run")
    async def run_check(check_id: str):
        # Find the check
        check = next((c for c in checks if c["id"] == check_id), None)
        if not check:
            raise HTTPException(status_code=404, detail="Check not found")
        
        # Create a mock result
        result = {
            "id": f"result_{len(results) + 1}",
            "check_id": check_id,
            "status": "success",
            "message": f"Check completed successfully for {check['name']}",
            "response_time": 0.123,
            "raw_data": {"details": "Sample result data"},
            "executed_at": "2025-04-01T00:00:00Z"
        }
        results.append(result)
        return result
    
    @app.get("/api/v1/results")
    async def get_results():
        return {
            "results": results,
            "pagination": {
                "page": 1,
                "per_page": 20,
                "total": len(results),
                "pages": 1
            }
        }
    
    # Root endpoint showing API info and available endpoints
    @app.get("/")
    async def root():
        return {
            "name": "MonitorPy API",
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc",
            "endpoints": [
                "/api/v1/health",
                "/api/v1/plugins",
                "/api/v1/checks",
                "/api/v1/results"
            ]
        }
    
    print(f"Starting Mock MonitorPy API on {args.host}:{args.port}...")
    print(f"API documentation available at http://{args.host}:{args.port}/docs")
    
    # Run the FastAPI app with Uvicorn
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)

if __name__ == "__main__":
    main()