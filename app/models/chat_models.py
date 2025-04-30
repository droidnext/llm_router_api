from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str
    content: str

class Function(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any]

class Tool(BaseModel):
    type: str
    function: Function

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    tools: Optional[List[Tool]] = None
    tool_choice: Optional[str] = None
    stream: Optional[bool] = False
    top_p: Optional[float] = 1.0
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    stop: Optional[List[str]] = None 