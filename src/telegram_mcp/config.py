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

ERROR_PREFIXES = {
    "chat": "CHAT",
    "msg": "MSG",
    "contact": "CONTACT",
    "group": "GROUP",
    "media": "MEDIA",
    "profile": "PROFILE",
    "auth": "AUTH",
    "admin": "ADMIN",
}

logger = logging.getLogger("telegram_mcp")

def get_config() -> ServiceConfig:
    """Returns the service configuration."""
    return ServiceConfig()

def json_serializer(obj):
    """Helper function to convert non-serializable objects for JSON serialization."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def log_and_format_error(
    function_name: str, error: Exception, prefix: str = None, **kwargs
) -> str:
    if prefix is None:
        for key, value in ERROR_PREFIXES.items():
            if key in function_name.lower():
                prefix = value
                break
        if prefix is None:
            prefix = "GEN"

    error_code = f"{prefix}-ERR-{abs(hash(function_name)) % 1000:03d}"
    context = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.exception(f"{function_name} failed ({context}): {error}")
    return f"An error occurred (code: {error_code}). Check mcp_errors.log for details."

def format_entity(entity) -> Dict[str, Any]:
    result = {"id": entity.id}
    if hasattr(entity, "title"):
        result["name"] = entity.title
        result["type"] = "group" if isinstance(entity, Chat) else "channel"
    elif hasattr(entity, "first_name"):
        name_parts = []
        if entity.first_name:
            name_parts.append(entity.first_name)
        if hasattr(entity, "last_name") and entity.last_name:
            name_parts.append(entity.last_name)
        result["name"] = " ".join(name_parts)
        result["type"] = "user"
        if hasattr(entity, "username") and entity.username:
            result["username"] = entity.username
        if hasattr(entity, "phone") and entity.phone:
            result["phone"] = entity.phone
    return result
