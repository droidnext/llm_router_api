#!/bin/bash

# Load environment variables
if [ -f "local.env" ]; then
    export $(cat local.env | grep -v '^#' | xargs)
fi

# Check if Phoenix server is already running
if lsof -Pi :6006 -sTCP:LISTEN -t >/dev/null ; then
    echo "Phoenix server is already running on port 6006"
    exit 1
fi

# Start Phoenix server
echo "Starting Phoenix server..."
poetry run python start_phoenix.py &

# Store the PID
echo $! > .phoenix.pid

echo "Phoenix server started with PID $(cat .phoenix.pid)"
echo "Access the dashboard at http://localhost:6006" 