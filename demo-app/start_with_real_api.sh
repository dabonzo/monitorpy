#!/bin/bash

# File: start_with_real_api.sh
# Description: Script to start the real MonitorPy API and the demo app

# Default options
MONITORPY_API_PORT=5000
DEMO_APP_PORT=8080
DATABASE_URL="sqlite:///:memory:"

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --api-port) MONITORPY_API_PORT="$2"; shift ;;
        --app-port) DEMO_APP_PORT="$2"; shift ;;
        --database) DATABASE_URL="$2"; shift ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Check if required packages are installed
if ! python -c "import flask" &>/dev/null; then
    echo "Flask is not installed. Please run ./setup.sh first."
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data

# Start the real MonitorPy API in the background
echo "Starting MonitorPy API on port $MONITORPY_API_PORT..."
cd $(dirname $0)/..

# Install monitorpy in development mode if not already installed
if ! python -c "import monitorpy" &>/dev/null; then
    echo "Installing MonitorPy in development mode..."
    
    # Try installing in current directory
    if [ -d "monitorpy" ]; then
        pip install -e .
    elif [ -d "monitorpy/monitorpy" ]; then
        cd monitorpy
        pip install -e .
        cd ..
    else
        echo "Error: Could not find MonitorPy package. Please check your directory structure."
        exit 1
    fi
fi

# Run the real API
echo "Using database: $DATABASE_URL"
./run_real_api.py --host 0.0.0.0 --port $MONITORPY_API_PORT --debug --database "$DATABASE_URL" &
API_PID=$!

# Wait for API to start
echo "Waiting for API to start..."
sleep 3

# Start the demo app HTTP server
echo "Starting demo app on port $DEMO_APP_PORT..."
cd $(dirname $0)
# Make sure we're in the demo-app directory
echo "Serving demo app from $(pwd)"
# Explicitly serve files from the current directory (demo-app)
python -m http.server $DEMO_APP_PORT --directory $(pwd) &
HTTP_PID=$!

# Setup trap to kill both servers on exit
trap "echo 'Shutting down servers...'; kill $API_PID $HTTP_PID 2>/dev/null" EXIT

# Print instructions
echo
echo "====================================================="
echo "MonitorPy Production Environment"
echo "====================================================="
echo "Real API is running at: http://localhost:$MONITORPY_API_PORT"
echo "Demo app is running at: http://localhost:$DEMO_APP_PORT"
echo "Using database: $DATABASE_URL"
echo
echo "Press Ctrl+C to shut down both servers"
echo "====================================================="

# Wait for user to press Ctrl+C
wait