#!/bin/bash

# File: start.sh
# Description: Script to start both the MonitorPy API and a simple HTTP server for the demo app

# Default options
MONITORPY_API_PORT=5000
DEMO_APP_PORT=8080

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --api-port) MONITORPY_API_PORT="$2"; shift ;;
        --app-port) DEMO_APP_PORT="$2"; shift ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Create data directory if it doesn't exist
mkdir -p data

# Start the MonitorPy API in the background
echo "Starting MonitorPy API on port $MONITORPY_API_PORT..."
cd $(dirname $0)/..
python -m monitorpy.monitorpy.cli api --host 0.0.0.0 --port $MONITORPY_API_PORT --debug &
API_PID=$!

# Wait for API to start
echo "Waiting for API to start..."
sleep 2

# Start the demo app HTTP server
echo "Starting demo app on port $DEMO_APP_PORT..."
cd $(dirname $0)
python -m http.server $DEMO_APP_PORT &
HTTP_PID=$!

# Setup trap to kill both servers on exit
trap "echo 'Shutting down servers...'; kill $API_PID $HTTP_PID 2>/dev/null" EXIT

# Print instructions
echo
echo "====================================================="
echo "MonitorPy Demo Environment"
echo "====================================================="
echo "API is running at: http://localhost:$MONITORPY_API_PORT"
echo "Demo app is running at: http://localhost:$DEMO_APP_PORT"
echo
echo "Press Ctrl+C to shut down both servers"
echo "====================================================="

# Wait for user to press Ctrl+C
wait