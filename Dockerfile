FROM python:3.9-slim

# Install required packages
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY pyproject.toml poetry.lock ./

# Install Poetry
RUN pip install poetry

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . .

# Create a script to fetch secrets from HCP
RUN echo '#!/bin/sh\n\
# Check for required HCP credentials\n\
if [ -z "$HCP_CLIENT_ID" ] || [ -z "$HCP_CLIENT_SECRET" ]; then\n\
    echo "Error: HCP_CLIENT_ID and HCP_CLIENT_SECRET must be set"\n\
    exit 1\n\
fi\n\
\n\
# Get HCP API token\n\
HCP_API_TOKEN=$(curl -s --location "https://auth.idp.hashicorp.com/oauth2/token" \\\n\
    --header "Content-Type: application/x-www-form-urlencoded" \\\n\
    --data-urlencode "client_id=$HCP_CLIENT_ID" \\\n\
    --data-urlencode "client_secret=$HCP_CLIENT_SECRET" \\\n\
    --data-urlencode "grant_type=client_credentials" \\\n\
    --data-urlencode "audience=https://api.hashicorp.cloud" | jq -r .access_token)\n\
\n\
if [ -z "$HCP_API_TOKEN" ] || [ "$HCP_API_TOKEN" = "null" ]; then\n\
    echo "Error: Failed to get HCP API token"\n\
    exit 1\n\
fi\n\
\n\
# Set default HCP configuration if not set\n\
export HCP_ORG_ID=${HCP_ORG_ID:-"2abf3ad3-2b28-4909-bf15-f0380e35bccf"}\n\
export HCP_PROJECT_ID=${HCP_PROJECT_ID:-"03640df7-f56b-4385-be8c-76ec82925e07"}\n\
export HCP_APP_NAME=${HCP_APP_NAME:-"my-llm-router"}\n\
\n\
# Function to read secrets from HCP\n\
read_hcp_secrets() {\n\
    echo "Reading secrets from HCP..."\n\
    \n\
    # Get secrets from HCP\n\
    local response=$(curl -s --location \\\n\
        "https://api.cloud.hashicorp.com/secrets/2023-11-28/organizations/$HCP_ORG_ID/projects/$HCP_PROJECT_ID/apps/$HCP_APP_NAME/secrets:open" \\\n\
        --header "Authorization: Bearer $HCP_API_TOKEN")\n\
    \n\
    if [ $? -ne 0 ] || [ "$response" = "null" ]; then\n\
        echo "Error: Failed to get secrets from HCP"\n\
        exit 1\n\
    fi\n\
    \n\
    # Debug: Print raw response\n\
    # echo "Raw HCP response:"\n\
    # echo "$response" | jq .\n\
    \n\
    # Process each secret\n\
    echo "Processing secrets..."\n\
    while IFS="=" read -r key value; do\n\
        if [ -n "$key" ] && [ -n "$value" ]; then\n\
            local env_var=$(echo "$key" | tr "[:lower:]" "[:upper:]" | tr "-" "_")\n\
            export "$env_var"="$value"\n\
            echo "Set environment variable: $env_var=$value"\n\
        fi\n\
    done < <(echo "$response" | jq -r '.secrets[] | select(.static_version != null) | "\\(.name)=\\(.static_version.value)"')\n\
    \n\
    # Debug: Print all environment variables\n\
    echo "Current environment variables:"\n\
    env | grep -i "azure\\|api\\|key"\n\
}\n\
\n\
# Read secrets from HCP\n\
read_hcp_secrets\n\
\n\
# Check for required environment variables\n\
echo "Checking required environment variables..."\n\
\n\
# List of required environment variables\n\
# required_vars=(\n\
#     "OPENAI_API_KEY"\n\
#     "ANTHROPIC_API_KEY"\n\
#     "AZURE_OPENAI_API_KEY"\n\
#     "JWT_SECRET_KEY"\n\
# )\n\

required_vars=(\n\
    "AZURE_API_KEY"\n\
)\n\

\n\
# Check each required variable\n\
missing_vars=()\n\
for var in "${required_vars[@]}"; do\n\
    if [ -z "${!var}" ]; then\n\
        missing_vars+=("$var")\n\
    else\n\
        echo "Found environment variable: $var"\n\
    fi\n\
done\n\
\n\
# If any required variables are missing, show error and exit\n\
if [ ${#missing_vars[@]} -ne 0 ]; then\n\
    echo "Error: The following required environment variables are not set:"\n\
    printf "%s\n" "${missing_vars[@]}"\n\
    echo "Please ensure these variables are set in HCP or your environment."\n\
    exit 1\n\
fi\n\
\n\
# Run the application\n\
exec "$@"' > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 