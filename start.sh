#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting LLM Proxy Service...${NC}"

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

# Check for required HCP credentials
echo -e "${YELLOW}Checking HCP credentials...${NC}"
if [ -z "$HCP_CLIENT_ID" ] || [ -z "$HCP_CLIENT_SECRET" ]; then
    echo -e "${RED}Error: HCP_CLIENT_ID and HCP_CLIENT_SECRET must be set${NC}"
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
    
    # Debug: Print raw response
    # echo -e "${YELLOW}Raw HCP response:${NC}"
    # echo "$response" | jq .
    
    # Process each secret
    echo -e "${YELLOW}Processing secrets...${NC}"
    while IFS='=' read -r key value; do
        if [ -n "$key" ] && [ -n "$value" ]; then
            local env_var=$(echo "$key" | tr "[:lower:]" "[:upper:]" | tr "-" "_")
            export "$env_var"="$value"
            echo -e "${GREEN}Set environment variable: $env_var=$value${NC}"
        fi
    done < <(echo "$response" | jq -r '.secrets[] | select(.static_version != null) | "\(.name)=\(.static_version.value)"')
    
    # Debug: Print all environment variables
    echo -e "${YELLOW}Current environment variables:${NC}"
    env | grep -i "azure\|api\|key"
}

# Read secrets from HCP
read_hcp_secrets

# Check for required environment variables
echo -e "${YELLOW}Checking required environment variables...${NC}"

# List of required environment variables
# required_vars=(
#     "OPENAI_API_KEY"
#     "ANTHROPIC_API_KEY"
#     "AZURE_OPENAI_API_KEY"
#     "JWT_SECRET_KEY"
# )

required_vars=(
    "AZURE_API_KEY"
)

# Check each required variable
missing_vars=()
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    else
        echo -e "${GREEN}Found environment variable: $var${NC}"
    fi
done

# If any required variables are missing, show error and exit
if [ ${#missing_vars[@]} -ne 0 ]; then
    echo -e "${RED}Error: The following required environment variables are not set:${NC}"
    printf '%s\n' "${missing_vars[@]}"
    echo -e "\n${YELLOW}Please ensure these variables are set in HCP or your environment.${NC}"
    exit 1
fi

# Start the application
echo -e "${YELLOW}Starting the application...${NC}"
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 