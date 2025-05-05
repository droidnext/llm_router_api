#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting LLM Proxy Service...${NC}"

# Function to read user input
read_input() {
    local prompt=$1
    local default=$2
    local input
    
    read -p "$prompt" input
    input=${input:-$default}
    echo "$input"
}

# Ask user for configuration method
echo -e "${YELLOW}Select configuration method:${NC}"
echo -e "${BLUE}1) Remote Vault (HCP)${NC}"
echo -e "${BLUE}2) Local Environment File${NC}"
echo -e "${BLUE}3) Exit${NC}"

while true; do
    choice=$(read_input "Enter your choice (1-3): " "1")
    case $choice in
        1)
            echo -e "${GREEN}✓ Using Remote Vault (HCP) configuration${NC}"
            break
            ;;
        2)
            echo -e "${GREEN}✓ Using Local Environment File configuration${NC}"
            break
            ;;
        3)
            echo -e "${YELLOW}Exiting...${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}✗ Invalid choice. Please enter 1, 2, or 3${NC}"
            ;;
    esac
done

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo -e "${YELLOW}Poetry is not installed. Installing Poetry...${NC}"
    curl -sSL https://install.python-poetry.org | python3 -
fi

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
poetry install

if [ "$choice" = "1" ]; then
    # Remote Vault (HCP) Configuration
    echo -e "${YELLOW}Checking HCP credentials...${NC}"
    if [ -z "$HCP_CLIENT_ID" ] || [ -z "$HCP_CLIENT_SECRET" ]; then
        echo -e "${RED}✗ Error: HCP_CLIENT_ID and HCP_CLIENT_SECRET must be set${NC}"
        echo -e "${YELLOW}Please set the following environment variables:${NC}"
        echo -e "${BLUE}export HCP_CLIENT_ID=your_client_id${NC}"
        echo -e "${BLUE}export HCP_CLIENT_SECRET=your_client_secret${NC}"
        exit 1
    fi

    # Get HCP API token
    echo -e "${YELLOW}Getting HCP API token...${NC}"
    HCP_API_TOKEN=$(curl -s --location "https://auth.idp.hashicorp.com/oauth2/token" \
        --header "Content-Type: application/x-www-form-urlencoded" \
        --data-urlencode "client_id=$HCP_CLIENT_ID" \
        --data-urlencode "client_secret=$HCP_CLIENT_SECRET" \
        --data-urlencode "grant_type=client_credentials" \
        --data-urlencode "audience=https://api.hashicorp.cloud" | jq -r .access_token)

    if [ -z "$HCP_API_TOKEN" ] || [ "$HCP_API_TOKEN" = "null" ]; then
        echo -e "${RED}Error: Failed to get HCP API token${NC}"
        exit 1
    fi

    # Set default HCP configuration if not set
    export HCP_ORG_ID=${HCP_ORG_ID:-"2abf3ad3-2b28-4909-bf15-f0380e35bccf"}
    export HCP_PROJECT_ID=${HCP_PROJECT_ID:-"03640df7-f56b-4385-be8c-76ec82925e07"}
    export HCP_APP_NAME=${HCP_APP_NAME:-"my-llm-router"}

    # Function to read secrets from HCP
    read_hcp_secrets() {
        echo -e "${YELLOW}Reading secrets from HCP...${NC}"
        
        # Get secrets from HCP
        local response=$(curl -s --location \
            "https://api.cloud.hashicorp.com/secrets/2023-11-28/organizations/$HCP_ORG_ID/projects/$HCP_PROJECT_ID/apps/$HCP_APP_NAME/secrets:open" \
            --header "Authorization: Bearer $HCP_API_TOKEN")
        
        if [ $? -ne 0 ] || [ "$response" = "null" ]; then
            echo -e "${RED}Error: Failed to get secrets from HCP${NC}"
            exit 1
        fi
        
        # Process each secret
        echo -e "${YELLOW}Processing secrets...${NC}"
        while IFS='=' read -r key value; do
            if [ -n "$key" ] && [ -n "$value" ]; then
                local env_var=$(echo "$key" | tr "[:lower:]" "[:upper:]" | tr "-" "_")
                export "$env_var"="$value"
                echo -e "${GREEN}Set environment variable: $env_var=$value${NC}"
            fi
        done < <(echo "$response" | jq -r '.secrets[] | select(.static_version != null) | "\(.name)=\(.static_version.value)"')
    }

    # Read secrets from HCP
    read_hcp_secrets
else
    # Local Environment File Configuration
    echo -e "${YELLOW}Using Local Environment File configuration...${NC}"
    if [ -f "local.env" ]; then
        echo -e "${GREEN}✓ Found local.env file${NC}"
        echo -e "${BLUE}Loading environment variables from local.env...${NC}"
        export $(cat local.env | grep -v '^#' | xargs)
        echo -e "${GREEN}✓ Environment variables loaded from local.env${NC}"
    else
        echo -e "${RED}✗ Error: local.env file not found${NC}"
        exit 1
    fi
fi

# Check for required environment variables
echo -e "${YELLOW}Checking required environment variables...${NC}"

# List of required environment variables
required_vars=(
    "AZURE_API_KEY"
    "AZURE_API_BASE"
    "AUTH0_DOMAIN"
    "AUTH0_AUDIENCE"
)

# Check each required variable
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}✗ Error: $var is not set${NC}"
        exit 1
    else
        echo -e "${GREEN}✓ $var is set${NC}"
    fi
done

# Load environment variables
source local.env

# Check if FastAPI server is already running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${RED}FastAPI server is already running on port 8000${NC}"
    exit 1
fi

# Start FastAPI server
echo -e "${BLUE}Starting FastAPI server...${NC}"
poetry run uvicorn app.main:app --reload --port 8000 &

# Store the PID
echo $! > .fastapi.pid

echo -e "${GREEN}FastAPI server started with PID $(cat .fastapi.pid)${NC}"
echo -e "${BLUE}API available at http://localhost:8000${NC}"
echo -e "${YELLOW}Note: Make sure Phoenix server is running for observability${NC}" 