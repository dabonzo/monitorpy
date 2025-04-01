#!/usr/bin/env python
"""
Script to run the real MonitorPy API for production use.

This script properly configures the Python path and imports the actual
MonitorPy API implementation.
"""

import os
import sys
import argparse

# Add the parent directory to Python path to fix import issues
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir)

# Check for required packages
try:
    import flask
    from flask_cors import CORS
    from flask_sqlalchemy import SQLAlchemy
except ImportError as e:
    print(f"Error: Missing required package - {e}")
    print("Please install the required packages:")
    print("  pip install flask flask-sqlalchemy flask-migrate flask-jwt-extended flask-marshmallow marshmallow-sqlalchemy flask-cors")
    sys.exit(1)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the MonitorPy API server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--database", help="Database URL (default: SQLite in-memory)")
    parser.add_argument("--config", help="Path to configuration file")
    return parser.parse_args()

def main():
    """Run the API server."""
    args = parse_args()
    
    # Set environment variables for configuration
    if args.database:
        os.environ['DATABASE_URL'] = args.database
    else:
        # Use in-memory SQLite as default for simplicity
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    
    os.environ['FLASK_ENV'] = 'development' if args.debug else 'production'
    
    # Load configuration if specified
    if args.config:
        # Import and load config after path setup
        try:
            from monitorpy.config import load_config
            load_config(args.config)
        except ImportError:
            print("Warning: Could not import configuration module. Using defaults.")
    
    # Try different import approaches
    try:
        # Try the nested module structure
        from monitorpy.monitorpy.api import create_app
        from monitorpy.monitorpy.api.config import DevelopmentConfig, ProductionConfig
        config_class = DevelopmentConfig if args.debug else ProductionConfig
    except ImportError:
        try:
            # Try direct import
            from monitorpy.api import create_app
            from monitorpy.api.config import DevelopmentConfig, ProductionConfig
            config_class = DevelopmentConfig if args.debug else ProductionConfig
        except ImportError:
            print("Error: Could not import MonitorPy API modules.")
            print("Please make sure MonitorPy is installed correctly:")
            print("  cd /path/to/monitorpy && pip install -e .")
            sys.exit(1)
    
    try:
        # Create the Flask app
        app = create_app(config_class)
        
        # Enable CORS for all origins in development
        if args.debug:
            CORS(app)
        
        print(f"Starting MonitorPy API on {args.host}:{args.port}...")
        app.run(host=args.host, port=args.port, debug=args.debug)
    except Exception as e:
        print(f"Error starting API: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()