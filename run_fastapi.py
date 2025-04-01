#!/usr/bin/env python3
"""
Script to run the MonitorPy FastAPI application.

This script is a convenience wrapper to start the FastAPI version of the API.
"""

from monitorpy.fastapi_api.run import run_api

if __name__ == "__main__":
    run_api(reload=True)