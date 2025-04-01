#!/usr/bin/env python
"""
Standalone script to run the MonitorPy API for the demo application.

This script provides a more direct way to start the API without relying
on module imports that might be affected by the project structure.
"""

import sys
import os
import argparse
from flask import Flask, jsonify
from flask_cors import CORS

# Ensure monitorpy is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from monitorpy.monitorpy.api import create_app
from monitorpy.monitorpy.api.config import DevelopmentConfig

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the MonitorPy API server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    return parser.parse_args()

def main():
    """Run the API server."""
    args = parse_args()
    
    # Use development config for demo
    app = create_app(DevelopmentConfig)
    
    # Enable CORS for the demo app
    CORS(app)
    
    # Add a special route for the demo
    @app.route('/demo-info')
    def demo_info():
        return jsonify({
            "name": "MonitorPy Demo API",
            "version": "1.0.0",
            "status": "running"
        })
    
    print(f"Starting MonitorPy API on {args.host}:{args.port}...")
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()