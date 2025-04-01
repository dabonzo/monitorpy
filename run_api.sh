#!/bin/bash

# Start the MonitorPy API server in development mode
cd $(dirname $0)
export FLASK_ENV=development
export DATABASE_URL=sqlite:///$(pwd)/data/monitorpy.db

# Create data directory if it doesn't exist
mkdir -p data

# Install dependencies if needed
if ! pip show flask > /dev/null 2>&1; then
    echo "Installing API dependencies..."
    pip install flask flask-sqlalchemy flask-migrate flask-jwt-extended flask-marshmallow marshmallow-sqlalchemy flask-cors gunicorn
fi

# Run the API server
echo "Starting MonitorPy API server..."
python -m monitorpy.cli api --debug