#!/usr/bin/env python
"""
Script to run the MonitorPy FastAPI for production use.

This script properly configures the Python path and launches the FastAPI
implementation with proper configuration.
"""

import os
import sys
import argparse

# Add the parent directory to Python path to fix import issues
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir)

# Check for required packages
try:
    import fastapi
    import uvicorn
    import pydantic
except ImportError as e:
    print(f"Error: Missing required package - {e}")
    print("Please install the required packages:")
    print("  pip install fastapi uvicorn pydantic python-jose python-multipart")
    sys.exit(1)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the MonitorPy FastAPI server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--database", help="Database URL (default: SQLite in-memory)")
    parser.add_argument("--config", help="Path to configuration file")
    return parser.parse_args()

def main():
    """Run the API server."""
    args = parse_args()
    
    # Set environment variables for configuration
    if args.database:
        # Format SQLite URL properly if needed
        if args.database.endswith('.db') or args.database.endswith('.sqlite') or args.database.endswith('.sql'):
            # Convert path to SQLAlchemy SQLite URL format
            db_path = os.path.abspath(args.database)
            os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
            print(f"Using database: {db_path}")
        else:
            # Assume it's already a properly formatted SQLAlchemy URL
            os.environ['DATABASE_URL'] = args.database
    else:
        # Use in-memory SQLite as default for simplicity
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    
    # Load configuration if specified
    if args.config:
        # Import and load config after path setup
        try:
            from monitorpy.config import load_config
            load_config(args.config)
        except ImportError:
            print("Warning: Could not import configuration module. Using defaults.")
    
    try:
        from monitorpy.fastapi_api.run import run_api
        
        print(f"Starting MonitorPy FastAPI on {args.host}:{args.port}...")
        run_api(host=args.host, port=args.port, reload=args.reload)
    except Exception as e:
        print(f"Error starting API: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()