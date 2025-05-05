import os
from typing import Optional

class PhoenixConfig:
    PHOENIX_API_KEY: Optional[str] = os.getenv("PHOENIX_API_KEY")
    PHOENIX_PROJECT_NAME: str = os.getenv("PHOENIX_PROJECT_NAME", "llm-proxy-service")
    PHOENIX_COLLECTOR_ENDPOINT: str = os.getenv(
        "PHOENIX_COLLECTOR_ENDPOINT", 
        "http://localhost:6006"  # Default to local Phoenix instance
    )

    @classmethod
    def setup_environment(cls):
        """Set up Phoenix environment variables"""
        if cls.PHOENIX_API_KEY:
            os.environ["PHOENIX_CLIENT_HEADERS"] = f"api_key={cls.PHOENIX_API_KEY}"
        os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = cls.PHOENIX_COLLECTOR_ENDPOINT 