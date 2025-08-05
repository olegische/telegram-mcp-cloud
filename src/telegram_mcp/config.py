import os
import logging

from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, Any

from telethon.tl.types import (
    Chat,
)

load_dotenv()

class ServiceConfig:
    TELEGRAM_API_ID: int = int(os.getenv("TELEGRAM_API_ID"))
    TELEGRAM_API_HASH: str = os.getenv("TELEGRAM_API_HASH")
    TELEGRAM_SESSION_NAME: str = os.getenv("TELEGRAM_SESSION_NAME")
    SESSION_STRING: str = os.getenv("TELEGRAM_SESSION_STRING")
    MCP_TRANSPORT: str = os.getenv("MCP_TRANSPORT", "stdio")
    MCP_HOST: str = os.getenv("MCP_HOST", "0.0.0.0")
    MCP_PORT: int = int(os.getenv("MCP_PORT", "8000"))
