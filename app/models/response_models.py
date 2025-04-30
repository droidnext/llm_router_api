from typing import Optional
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error: str
    code: Optional[int] = None
    message: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None 