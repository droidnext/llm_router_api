# LLM Proxy Service

A FastAPI-based proxy service for LLM model requests using LiteLLM.

## Features

- OpenAI-compatible API endpoints
- JWT token authentication
- Support for multiple LLM providers through LiteLLM
- Docker support
- Environment variable configuration
- Poetry for dependency management
- HashiCorp Vault integration for secrets management

## Project Structure

```
llm-proxy-service/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── chat_models.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── config.yaml
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth_middleware.py
│   └── services/
│       ├── __init__.py
│       ├── auth_service.py
│       └── llm_service.py
├── pyproject.toml
├── README.md
└── Dockerfile
```

## Setup

### Local Development

1. Clone the repository
2. Create a `.env` file with the following variables:
   ```
   JWT_SECRET_KEY=your-super-secret-key-change-in-production
   OPENAI_API_KEY=your-openai-api-key
   ANTHROPIC_API_KEY=your-anthropic-api-key
   AUTH0_DOMAIN=your-auth0-domain
   AUTH0_AUDIENCE=your-auth0-audience
   ```

3. Install dependencies using Poetry:
   ```bash
   # Install Poetry if you haven't already
   curl -sSL https://install.python-poetry.org | python3 -
   
   # Install dependencies
   poetry install
   ```

### HashiCorp Vault Setup

1. Install the Vault CLI:
   ```bash
   # For macOS
   brew install vault

   # For Linux
   curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
   sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
   sudo apt-get update && sudo apt-get install vault
   ```

2. Login to HCP Vault:
   ```bash
   vault login -method=oidc
   ```

3. Store secrets in Vault:
   ```bash
   vault kv put secret/llm-proxy \
     JWT_SECRET_KEY="your-super-secret-key" \
     OPENAI_API_KEY="your-openai-api-key" \
     ANTHROPIC_API_KEY="your-anthropic-api-key" \
     AUTH0_DOMAIN="your-auth0-domain" \
     AUTH0_AUDIENCE="your-auth0-audience"
   ```

## Running the Service

### Local Development
```bash
# Using Poetry
poetry run uvicorn app.main:app --reload

# Or using Python directly
python -m uvicorn app.main:app --reload
```

### Using Docker with Vault
```bash
# Build the image
docker build -t llm-proxy-service .

# Run the container with Vault environment variables
docker run -p 8000:8000 \
  -e VAULT_ADDR="https://vault.hashicorp.cloud" \
  -e VAULT_NAMESPACE="admin" \
  -e VAULT_TOKEN="your-vault-token" \
  llm-proxy-service
```

## API Usage

1. Generate a JWT token:
```bash
curl -X POST "http://localhost:8000/generate-token" \
     -H "Content-Type: application/json" \
     -d '{
       "client_id": "your-auth0-client-id",
       "client_secret": "your-auth0-client-secret"
     }'
```

2. List available models:
```bash
curl -X GET "http://localhost:8000/models/list"
```

3. Make a chat completion request:
```bash
curl -X POST "http://localhost:8000/models/azure/gpt-4.1-mini" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "messages": [
         {"role": "user", "content": "Hello!"}
       ]
     }'
```

## API Endpoints

- GET `/models/list` - List all available models (no auth required)
- POST `/models/{provider}/{model_id}` - Chat completion endpoint (requires auth)
- POST `/generate-token` - Generate JWT token using Auth0 credentials
- GET `/health` - Health check endpoint

## Response Format

### Chat Completion Response
```json
{
  "id": "chatcmpl-123",
  "created": 1234567890,
  "model": "azure/gpt-4.1-mini",
  "object": "chat.completion",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you?",
        "tool_calls": null,
        "function_call": null,
        "provider_specific_fields": null
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

### List Models Response
```json
{
  "openai": ["gpt-3.5-turbo", "gpt-4"],
  "azure": ["gpt-4.1-mini"]
}
```

## Security Notes

- Change the JWT_SECRET_KEY in production
- Configure CORS settings appropriately in production
- Secure your API keys using HashiCorp Vault
- Consider adding rate limiting for production use
- Use appropriate Vault policies to restrict access to secrets 