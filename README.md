# LLM Proxy Service

A FastAPI-based proxy service for LLM model requests using LiteLLM, with observability powered by Arize Phoenix.

## Features

- OpenAI-compatible API endpoints
- JWT token authentication via Auth0
- Support for multiple LLM providers through LiteLLM:
  - OpenAI
  - Azure OpenAI
  - Anthropic
  - Google Gemini
- Observability and evaluation using Arize Phoenix
- Docker support
- Environment variable configuration
- Poetry for dependency management

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
├── Dockerfile
├── start.sh
├── start_phoenix.sh
├── stop.sh
└── start_phoenix.py
```

## Setup

### Local Development

1. Clone the repository
2. Create a `local.env` file with the following variables:
   ```
   # Auth0 Configuration
   AUTH0_DOMAIN=your-auth0-domain
   AUTH0_AUDIENCE=your-auth0-audience

   # Azure OpenAI Configuration
   AZURE_API_KEY=your-azure-api-key
   AZURE_API_BASE=your-azure-api-base

   # Phoenix Configuration
   PHOENIX_PROJECT_NAME=llm-proxy-service
   PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006

   # Logging
   LOG_LEVEL=INFO
   ```

3. Install dependencies using Poetry:
   ```bash
   # Install Poetry if you haven't already
   curl -sSL https://install.python-poetry.org | python3 -
   
   # Install dependencies with Phoenix support
   poetry install --with phoenix
   ```

4. Make the scripts executable:
   ```bash
   chmod +x start.sh start_phoenix.sh stop.sh
   ```

## Running the Service

### Local Development

1. Start the Phoenix server (for observability):
   ```bash
   ./start_phoenix.sh
   ```

2. Start the main service:
   ```bash
   ./start.sh
   ```

3. To stop all services:
   ```bash
   ./stop.sh
   ```

The services can be started in any order, but it's recommended to start Phoenix first to ensure all requests are tracked from the beginning.

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
curl -X POST "http://localhost:8000/models/azure/gpt-4" \
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
  "model": "azure/gpt-4",
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
  "openai": ["gpt-4o", "gpt-4o-mini"],
  "anthropic": ["claude-2", "claude-instant-1"],
  "azure": ["gpt-4"],
  "gemini": ["gemini-1.5-flash-002", "gemini-2.0-flash-lite"]
}
```

## Observability with Phoenix

The service integrates with Arize Phoenix for LLM observability and evaluation. The Phoenix server runs on port 6006 and provides:

- Request/response tracking
- Latency monitoring
- Error tracking
- Token usage analytics
- Model performance evaluation

Access the Phoenix dashboard at `http://localhost:6006` when the service is running.

### Starting Phoenix Server

The Phoenix server can be started independently using:
```bash
./start_phoenix.sh
```

This script:
- Checks if Phoenix is already running
- Loads environment variables from local.env
- Starts the Phoenix server in the background
- Stores the process ID for clean shutdown

## Security Notes

- Configure Auth0 settings appropriately for your environment
- Set appropriate CORS settings in production
- Use environment variables for sensitive configuration
- Consider adding rate limiting for production use
- Monitor token usage and costs through Phoenix dashboard 