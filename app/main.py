from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from dotenv import load_dotenv
from .routes import router
from .middleware.auth_middleware import AuthMiddleware
from .middleware.url_rewrite import URLRewriteMiddleware
import logging
import sys

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

tags_metadata = [
    {
        "name": "Authentication",
        "description": "Operations related to authentication and authorization",
    },
    {
        "name": "Models",
        "description": "Operations related to LLM models and providers",
    },
    {
        "name": "Chat",
        "description": "Operations related to chat completions",
    },
    {
        "name": "Health",
        "description": "Health check and monitoring endpoints",
    }
]

app = FastAPI(
    title="LLM Proxy Service",
    description="""
    A proxy service for various LLM providers.
    
    ## Features
    * Support for multiple LLM providers (OpenAI, Anthropic, Azure)
    * Authentication and authorization
    * Rate limiting
    * Request/response logging
    * Health monitoring
    
    ## API Documentation
    * Swagger UI: `/docs` or `/swagger`
    * ReDoc: `/redoc`
    * OpenAPI JSON: `/openapi.json`
    
    ## Authentication
    Most endpoints require a JWT token. You can get one by calling the `/generate-token` endpoint.
    Include the token in the Authorization header: `Bearer <token>`
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "docExpansion": "list",
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "persistAuthorization": True,
        "displayRequestDuration": True,
    },
    openapi_tags=tags_metadata
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
app.add_middleware(AuthMiddleware)

# Add URL rewrite middleware
app.add_middleware(URLRewriteMiddleware)

# Include routes
app.include_router(router, prefix="")

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="LLM Proxy Service",
        version="1.0.0",
        description="""
        A proxy service for various LLM providers.
        
        ## Features
        * Support for multiple LLM providers (OpenAI, Anthropic, Azure)
        * Authentication and authorization
        * Rate limiting
        * Request/response logging
        * Health monitoring
        """,
        routes=app.routes,
        tags=tags_metadata,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token in the format: Bearer <token>"
        }
    }
    
    # Add security requirements
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    # Add examples
    openapi_schema["components"]["schemas"]["ChatCompletionRequest"]["example"] = {
        "model": "gpt-4",
        "messages": [
            {
                "role": "user",
                "content": "Hello, how are you?"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    openapi_schema["components"]["schemas"]["TokenResponse"]["example"] = {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 3600
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 