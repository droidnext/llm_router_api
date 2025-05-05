#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping LLM Proxy Service and related processes...${NC}"

# Function to stop a process by PID file
stop_process() {
    local pid_file=$1
    local process_name=$2
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null; then
            echo -e "${BLUE}Stopping $process_name (PID: $pid)...${NC}"
            kill $pid
            rm "$pid_file"
            echo -e "${GREEN}✓ Successfully stopped $process_name${NC}"
        else
            echo -e "${YELLOW}⚠ $process_name is not running${NC}"
            rm "$pid_file"
        fi
    else
        echo -e "${YELLOW}⚠ $process_name is not running${NC}"
    fi
}

# Function to kill process by port if PID file method fails
kill_process_by_port() {
    local port=$1
    local process_name=$2
    
    if lsof -ti:$port >/dev/null; then
        pid=$(lsof -ti:$port)
        echo -e "${YELLOW}Found $process_name process on port $port (PID: $pid)${NC}"
        kill -9 $pid
        echo -e "${GREEN}✓ Successfully stopped $process_name${NC}"
    fi
}

# Stop FastAPI server
stop_process ".fastapi.pid" "FastAPI server"
kill_process_by_port 8000 "FastAPI server"

# Stop Phoenix server
stop_process ".phoenix.pid" "Phoenix server"
kill_process_by_port 6006 "Phoenix server"

# Clean up any temporary files
echo -e "${BLUE}Cleaning up temporary files...${NC}"
if [ -d ".pytest_cache" ]; then
    rm -rf .pytest_cache
    echo -e "${GREEN}✓ Removed pytest cache${NC}"
fi

if [ -d "__pycache__" ]; then
    find . -type d -name "__pycache__" -exec rm -rf {} +
    echo -e "${GREEN}✓ Removed Python cache files${NC}"
fi

echo -e "${GREEN}✓ All services stopped and cleaned up successfully${NC}" 