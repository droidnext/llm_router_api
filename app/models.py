from pydantic import BaseModel
from typing import Optional, List

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False

class ErrorResponse(BaseModel):
    error: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str 