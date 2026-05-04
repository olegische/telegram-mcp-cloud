import os

from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class ServiceConfig:
    TELEGRAM_API_ID: Optional[int] = (
        int(api_id) if (api_id := os.getenv("TELEGRAM_API_ID")) else None
    )
    TELEGRAM_API_HASH: Optional[str] = os.getenv("TELEGRAM_API_HASH")
    TELEGRAM_SESSION_NAME: Optional[str] = os.getenv("TELEGRAM_SESSION_NAME")
    SESSION_STRING: Optional[str] = os.getenv("TELEGRAM_SESSION_STRING")
    MCP_TRANSPORT: str = os.getenv("MCP_TRANSPORT", "stdio")
    MCP_HOST: str = os.getenv("MCP_HOST", "0.0.0.0")
    MCP_PORT: int = int(os.getenv("MCP_PORT", "8000"))
