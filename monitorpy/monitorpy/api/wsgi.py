"""
WSGI entry point for the MonitorPy API.

This module provides a WSGI-compatible entry point for running the API
with production servers like Gunicorn.
"""

from monitorpy.api import create_app
from monitorpy.api.config import ProductionConfig

app = create_app(ProductionConfig)

if __name__ == "__main__":
    app.run()