#!/bin/bash

# Install required packages for the MonitorPy API and demo app
echo "Installing required packages..."

# Try to detect if we're in a virtual environment
if [[ -n "$VIRTUAL_ENV" || -n "$CONDA_PREFIX" ]]; then
    echo "Using Python from virtual environment: $(which python)"
    
    # Install with pip
    pip install flask flask-sqlalchemy flask-migrate flask-jwt-extended flask-marshmallow marshmallow-sqlalchemy flask-cors gunicorn pyyaml
else
    echo "WARNING: No virtual environment detected. Installing packages globally is not recommended."
    echo "Consider creating and activating a virtual environment first."
    echo
    echo "To create a virtual environment:"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate  # On Linux/Mac"
    echo "  venv\\Scripts\\activate    # On Windows"
    echo
    
    read -p "Continue with global installation? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip install flask flask-sqlalchemy flask-migrate flask-jwt-extended flask-marshmallow marshmallow-sqlalchemy flask-cors gunicorn pyyaml
    else
        exit 1
    fi
fi

echo
echo "Installation complete! You can now run the demo app with ./start.sh"