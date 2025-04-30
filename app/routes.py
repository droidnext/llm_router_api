from fastapi import APIRouter, HTTPException, Request, Path, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .models import ChatCompletionRequest, TokenResponse, ErrorResponse
from .services.llm_service import LLMService
from .services.auth_service import AuthService
from typing import List, Dict, Any, Optional
import requests
import os
import json

router = APIRouter()
security = HTTPBearer()
llm_service = LLMService()
auth_service = AuthService()

@router.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: A dictionary containing the health status of the service.
    """
    return {"status": "healthy"}

@router.get("/models/list", response_model=Dict[str, List[str]])
async def list_models():
    """List all models from all providers"""
    try:
        models = llm_service.config.get_supported_models()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/{provider}/{model_id}", response_model=Dict[str, Any])
async def create_chat_completion(
    request: Request,
    chat_request: ChatCompletionRequest,
    provider: str = Path(..., description="The provider name"),
    model_id: str = Path(..., description="The model ID"),
    session: Optional[str] = Query(None, description="Session ID")
):
    """Create a chat completion for a specific model"""
    try:
        # Update the model in the request to include provider
        chat_request.model = f"{provider}/{model_id}"
        if session:
            chat_request.session = session
        response = await llm_service.create_chat_completion(chat_request)
        
        # Convert ModelResponse to dictionary
        response_dict = {
            "id": response.id,
            "created": response.created,
            "model": response.model,
            "object": response.object,
            "choices": [
                {
                    "index": choice.index,
                    "message": {
                        "role": choice.message.role,
                        "content": choice.message.content,
                        "tool_calls": choice.message.tool_calls,
                        "function_call": choice.message.function_call,
                        "provider_specific_fields": choice.message.provider_specific_fields
                    },
                    "finish_reason": choice.finish_reason
                }
                for choice in response.choices
            ],
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
        
        return response_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/generate-token",
    response_model=TokenResponse,
    summary="Generate an access token",
    description="Generate an access token using client credentials",
    tags=["Authentication"]
)
async def generate_token(client_id: str, client_secret: str) -> Dict[str, str]:
    """
    Generate an access token using client credentials.
    
    Args:
        client_id (str): The client ID from Auth0
        client_secret (str): The client secret from Auth0
        
    Returns:
        Dict[str, str]: The access token and token type
        
    Raises:
        HTTPException: If token generation fails or required environment variables are not set
    """
    try:
        # Check for required environment variables
        auth0_domain = os.getenv("AUTH0_DOMAIN")
        if not auth0_domain:
            raise HTTPException(
                status_code=500,
                detail="AUTH0_DOMAIN environment variable is not set"
            )
            
        audience = os.getenv("AUTH0_AUDIENCE")
        if not audience:
            raise HTTPException(
                status_code=500,
                detail="AUTH0_AUDIENCE environment variable is not set"
            )
        
        # Request token from Auth0
        response = requests.post(
            f"https://{auth0_domain}/oauth/token",
            headers={"Content-Type": "application/json"},
            json={
                "client_id": client_id,
                "client_secret": client_secret,
                "audience": audience,
                "grant_type": "client_credentials"
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to generate token: {response.text}"
            )
            
        return response.json()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Token generation failed: {str(e)}"
        ) 