import pytest
from fastapi import FastAPI, Request
from starlette.testclient import TestClient
from app.middleware.url_rewrite import URLRewriteMiddleware
from urllib.parse import urlparse, parse_qs
from app.models import ChatCompletionRequest
from app.services.llm_service import LLMService
import json

# Test application setup
app = FastAPI()
app.add_middleware(URLRewriteMiddleware)

# Mock LLMService for testing
class MockLLMService:
    async def create_chat_completion(self, request: ChatCompletionRequest):
        return {
            "id": "test-id",
            "created": 1234567890,
            "model": request.model,
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Test response",
                        "tool_calls": None,
                        "function_call": None,
                        "provider_specific_fields": None
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

    def get_supported_models(self):
        return {
            "openai": ["gpt-3.5-turbo", "gpt-4"],
            "azure": ["gpt-4.1-mini"]
        }

# Add routes for testing
@app.get("/models/list")
async def list_models():
    service = MockLLMService()
    return service.get_supported_models()

@app.post("/models/{provider}/{model_id}")
async def create_chat_completion(
    request: Request,
    chat_request: ChatCompletionRequest,
    provider: str,
    model_id: str
):
    service = MockLLMService()
    chat_request.model = f"{provider}/{model_id}"
    return await service.create_chat_completion(chat_request)

client = TestClient(app)

def test_list_models():
    """Test the list models endpoint"""
    response = client.get("/models/list")
    assert response.status_code == 200
    data = response.json()
    assert "openai" in data
    assert "azure" in data
    assert "gpt-3.5-turbo" in data["openai"]
    assert "gpt-4.1-mini" in data["azure"]

def test_create_chat_completion():
    """Test the chat completion endpoint"""
    response = client.post(
        "/models/azure/gpt-4.1-mini",
        json={
            "messages": [
                {"role": "user", "content": "Hello!"}
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-id"
    assert data["model"] == "azure/gpt-4.1-mini"
    assert len(data["choices"]) == 1
    assert data["choices"][0]["message"]["content"] == "Test response"
    assert data["usage"]["total_tokens"] == 30

def test_single_query_parameter():
    """Test URL with single query parameter in the middle"""
    response = client.get("/models/openai/gpt-4?session=abc/chat/completions")
    assert response.status_code == 200
    data = response.json()
    assert data["url"].endswith("/models/openai/gpt-4/chat/completions?session=abc")
    assert data["query_params"] == {"session": "abc"}

def test_multiple_query_parameters():
    """Test URL with multiple query parameters in the middle"""
    response = client.get("/models/openai/gpt-4?session=abc&id=test/chat/completions")
    assert response.status_code == 200
    data = response.json()
    assert data["url"].endswith("/models/openai/gpt-4/chat/completions?session=abc&id=test")
    assert data["query_params"] == {"session": "abc", "id": "test"}

def test_special_characters_in_parameters():
    """Test URL with special characters in query parameters"""
    response = client.get("/models/openai/gpt-4?session=abc%20def&id=test%2F123/chat/completions")
    assert response.status_code == 200
    data = response.json()
    assert "session=abc%20def" in data["url"]
    assert "id=test%2F123" in data["url"]
    assert data["query_params"] == {"session": "abc def", "id": "test/123"}

def test_existing_query_parameters():
    """Test URL with existing query parameters at the end"""
    response = client.get("/models/openai/gpt-4?session=abc/chat/completions?existing=param")
    assert response.status_code == 200
    data = response.json()
    assert data["url"].endswith("/models/openai/gpt-4/chat/completions?session=abc&existing=param")
    assert data["query_params"] == {"session": "abc", "existing": "param"}

def test_no_query_parameters():
    """Test URL without any query parameters"""
    response = client.get("/models/openai/gpt-4/chat/completions")
    assert response.status_code == 200
    data = response.json()
    assert data["url"].endswith("/models/openai/gpt-4/chat/completions")
    assert data["query_params"] == {}

def test_query_at_end():
    """Test URL with query parameters already at the end"""
    response = client.get("/models/openai/gpt-4/chat/completions?session=abc")
    assert response.status_code == 200
    data = response.json()
    assert data["url"].endswith("/models/openai/gpt-4/chat/completions?session=abc")
    assert data["query_params"] == {"session": "abc"}

def test_multiple_path_segments():
    """Test URL with multiple path segments after query parameters"""
    response = client.get("/models/openai/gpt-4?session=abc/chat/completions/stream")
    assert response.status_code == 200
    data = response.json()
    assert data["url"].endswith("/models/openai/gpt-4/chat/completions/stream?session=abc")
    assert data["query_params"] == {"session": "abc"}

def test_empty_query_parameter():
    """Test URL with empty query parameter value"""
    response = client.get("/models/openai/gpt-4?session=/chat/completions")
    assert response.status_code == 200
    data = response.json()
    assert data["url"].endswith("/models/openai/gpt-4/chat/completions?session=")
    assert data["query_params"] == {"session": ""}

def test_multiple_same_parameters():
    """Test URL with multiple instances of the same parameter"""
    response = client.get("/models/openai/gpt-4?session=abc&session=def/chat/completions")
    assert response.status_code == 200
    data = response.json()
    assert data["url"].endswith("/models/openai/gpt-4/chat/completions?session=abc&session=def")
    assert data["query_params"] == {"session": ["abc", "def"]}

def test_complex_url():
    """Test URL with multiple path segments and query parameters"""
    response = client.get("/models/openai/gpt-4?session=abc&id=test/chat/completions/stream?format=json")
    assert response.status_code == 200
    data = response.json()
    assert data["url"].endswith("/models/openai/gpt-4/chat/completions/stream?session=abc&id=test&format=json")
    assert data["query_params"] == {"session": "abc", "id": "test", "format": "json"} 