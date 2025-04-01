#!/bin/bash

# Start the MonitorPy API server in development mode
cd $(dirname $0)
export DATABASE_URL=sqlite:///$(pwd)/data/monitorpy.db

# Create data directory if it doesn't exist
mkdir -p data

# Install dependencies if needed
if ! pip show fastapi > /dev/null 2>&1; then
    echo "Installing API dependencies..."
    pip install fastapi uvicorn pydantic python-jose python-multipart
fi

# Run the API server
echo "Starting MonitorPy FastAPI server..."
python run_fastapi.py