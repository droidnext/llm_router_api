from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..services.auth_service import AuthService
from typing import Callable
import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.auth_service = AuthService()
        self.security = HTTPBearer()
        # List of paths that don't require authentication
        self.excluded_paths = [
            r"^/$",  # Root path
            r"^/docs",
            r"^/redoc",
            r"^/openapi.json",
            r"^/generate-token",
            r"^/health",
            r"^/swagger"  # Swagger UI alternative path
        ]

    async def dispatch(self, request: Request, call_next: Callable):
        logger.info(f"Processing request for path: {request.url.path}")
        
        # Check if the path is in the excluded list
        if any(re.match(pattern, request.url.path) for pattern in self.excluded_paths):
            logger.info(f"Path {request.url.path} is excluded from authentication")
            return await call_next(request)

        # Get the authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.error("Authorization header is missing")
            return JSONResponse(
                status_code=401,
                content={"detail": "Authorization header is missing"}
            )

        try:
            # Extract the token
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                logger.error(f"Invalid authentication scheme: {scheme}")
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid authentication scheme"}
                )

            logger.info("Verifying token...")
            # Verify the token
            payload = self.auth_service.verify_token(token)
            logger.info(f"Token verified successfully. Payload: {payload}")
            
            # Set the user in request state
            request.state.user = payload
            logger.info("User payload set in request state")
            
            # Continue with the request
            response = await call_next(request)
            logger.info("Request processed successfully")
            return response

        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return JSONResponse(
                status_code=401,
                content={"detail": str(e)}
            ) 