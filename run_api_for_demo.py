#!/usr/bin/env python
"""
Standalone script to run the MonitorPy API for the demo application.

This script provides a more direct way to start the API without relying
on module imports that might be affected by the project structure.
"""

import sys
import os
import argparse
from flask import Flask, jsonify, request
from flask_cors import CORS

# Make a simpler mock API since we're having module path issues
# This will provide the basic API endpoints for the demo

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
    
    # Create a simple Flask app for the demo
    app = Flask("monitorpy-demo-api")
    CORS(app)
    
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
    @app.route('/api/v1/health')
    def health():
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "version": "1.0.0"
        })
    
    @app.route('/api/v1/plugins')
    def get_plugins():
        return jsonify({
            "plugins": plugins,
            "count": len(plugins)
        })
    
    @app.route('/api/v1/checks')
    def get_checks():
        return jsonify({
            "checks": checks,
            "pagination": {
                "page": 1,
                "per_page": 20,
                "total": len(checks),
                "pages": 1
            }
        })
    
    @app.route('/api/v1/checks', methods=['POST'])
    def create_check():
        # Mock creating a check
        new_check = {
            "id": f"check_{len(checks) + 1}",
            "name": request.json.get('name', 'New Check'),
            "plugin_type": request.json.get('plugin_type', 'unknown'),
            "config": request.json.get('config', {}),
            "enabled": True,
            "schedule": None,
            "last_run": None,
            "created_at": "2025-04-01T00:00:00Z",
            "updated_at": "2025-04-01T00:00:00Z"
        }
        checks.append(new_check)
        return jsonify(new_check), 201
    
    @app.route('/api/v1/checks/<check_id>', methods=['DELETE'])
    def delete_check(check_id):
        global checks
        checks = [c for c in checks if c["id"] != check_id]
        return "", 204
    
    @app.route('/api/v1/checks/<check_id>/run', methods=['POST'])
    def run_check(check_id):
        # Find the check
        check = next((c for c in checks if c["id"] == check_id), None)
        if not check:
            return jsonify({"error": "Check not found"}), 404
        
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
        return jsonify(result)
    
    @app.route('/api/v1/results')
    def get_results():
        return jsonify({
            "results": results,
            "pagination": {
                "page": 1,
                "per_page": 20,
                "total": len(results),
                "pages": 1
            }
        })
    
    print(f"Starting Mock MonitorPy API on {args.host}:{args.port}...")
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()