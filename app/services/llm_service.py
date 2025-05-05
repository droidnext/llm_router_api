from typing import List, Dict, Any, Optional, AsyncGenerator
import litellm
from litellm import completion
from ..models.chat_models import ChatCompletionRequest, ChatMessage, Tool
from ..config.config import Config
import os
import json
import logging

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.litellm = litellm
        self.config = Config()

    async def create_chat_completion(self, request: ChatCompletionRequest) -> Dict[str, Any]:
        try:
            # Extract provider and model name from the request
            # Format: provider:model (e.g., "openai:gpt-4o")
            model_name = request.model.split("/")
            if len(model_name) != 2:
                raise ValueError("Missing provider/model_name")
            
            provider_name = model_name[0]
            logger.debug(f"Provider name: {provider_name}")
            model_name = model_name[1]
            logger.debug(f"Model name: {model_name}")

            # Get provider configuration
            provider_config = self.config.get_provider(provider_name)
            
            # Convert request to dict and remove None values
            completion_params = request.dict(exclude_none=True)
            
            # Update model name to use the actual model name without provider prefix
            completion_params["model"] = provider_name+"/"+model_name

            # Add provider-specific configuration
            completion_params["api_base"] = provider_config.api_base
            if provider_config.api_version:
                completion_params["api_version"] = provider_config.api_version
            
            # Set provider-specific API key
            if provider_name == "azure":
                completion_params["api_key"] = os.getenv("AZURE_API_KEY")
            elif provider_name == "openai":
                completion_params["api_key"] = os.getenv("OPENAI_API_KEY")
            elif provider_name == "anthropic":
                completion_params["api_key"] = os.getenv("ANTHROPIC_API_KEY")
            elif provider_name == "gemini":
                completion_params["api_key"] = os.getenv("GOOGLE_API_KEY")
            
            logger.debug(f"Completion params: {completion_params}")
            
            if request.stream:
                return self._handle_streaming_response(completion(**completion_params))
            else:
                response = completion(**completion_params)
                return response
        except Exception as e:
            logger.error(f"Error creating chat completion: {str(e)}")
            raise Exception(f"Error creating chat completion: {str(e)}")

    async def _handle_streaming_response(self, response_stream) -> AsyncGenerator[str, None]:
        try:
            async for chunk in response_stream:
                if chunk:
                    # Convert the chunk to a string and yield it
                    yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            error_response = {
                "error": {
                    "message": f"Error in streaming response: {str(e)}",
                    "type": "streaming_error"
                }
            }
            yield f"data: {json.dumps(error_response)}\n\n"
            yield "data: [DONE]\n\n" 