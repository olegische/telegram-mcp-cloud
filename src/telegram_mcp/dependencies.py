"""MCP dependencies for dependency injection."""
import logging
import contextlib
from typing import Optional, AsyncGenerator

from mcp.server.fastmcp import Context
from telethon import TelegramClient
from telethon.sessions import StringSession

from .config import ServiceConfig

logger = logging.getLogger(__name__)


def get_authentication_headers(context: Context) -> dict[str, str]:
    """Get authentication headers from the request context.

    Args:
        context: MCP server context containing request information

    Returns:
        Dictionary of headers with lowercase keys

    Raises:
        RuntimeError: If request context is not available
    """
    if context.request_context is None or context.request_context.request is None:
        # This can happen in stdio transport mode
        return {}

    if not hasattr(context.request_context.request, "headers"):
        raise RuntimeError("Request object does not have headers")

    headers: dict[str, str] = context.request_context.request.headers
    # Convert to lowercase for case-insensitive lookup
    return {k.lower(): v for k, v in headers.items()}


def get_config(context: Context) -> ServiceConfig:
    """Get ServiceConfig object for the current request.

    Loads ServiceConfig from the environment and overrides credentials with
    values from request headers if they are present.

    Args:
        context: MCP server context

    Returns:
        ServiceConfig object

    Raises:
        ValueError: If partial or conflicting credentials are provided in headers.
    """
    config = ServiceConfig()
    headers = get_authentication_headers(context)

    api_id = headers.get("x-telegram-api-id")
    api_hash = headers.get("x-telegram-api-hash")
    session_string = headers.get("x-telegram-session-string")
    session_name = headers.get("x-telegram-session-name")

    # If no credential headers are present, return the default config
    if not any([api_id, api_hash, session_string, session_name]):
        return config

    # If some but not all required headers are present, it's an error
    if not all([api_id, api_hash]):
        raise ValueError("Both X-Telegram-API-ID and X-Telegram-API-Hash are required when overriding credentials.")

    if not (session_string or session_name):
        raise ValueError("Either X-Telegram-Session-String or X-Telegram-Session-Name is required for override.")
    
    if session_string and session_name:
        raise ValueError("Provide either X-Telegram-Session-String or X-Telegram-Session-Name, not both.")

    logger.debug("Overriding config with credentials from headers.")
    config.TELEGRAM_API_ID = int(api_id)
    config.TELEGRAM_API_HASH = api_hash
    
    if session_string:
        config.SESSION_STRING = session_string
        config.TELEGRAM_SESSION_NAME = None
    else:
        config.TELEGRAM_SESSION_NAME = session_name
        config.SESSION_STRING = None

    return config


@contextlib.asynccontextmanager
async def get_telegram_client(context: Context) -> AsyncGenerator[TelegramClient, None]:
    """An async context manager to provide an authorized Telegram client.

    Args:
        context: MCP server context

    Yields:
        An authorized and connected TelegramClient instance.

    Raises:
        ValueError: If required credentials are missing or user is not authorized.
    """
    config = get_config(context)

    if not all([config.TELEGRAM_API_ID, config.TELEGRAM_API_HASH]):
        raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be configured.")

    if config.SESSION_STRING:
        session = StringSession(config.SESSION_STRING)
    elif config.TELEGRAM_SESSION_NAME:
        session = config.TELEGRAM_SESSION_NAME
    else:
        raise ValueError("Either SESSION_STRING or TELEGRAM_SESSION_NAME must be provided.")

    client = TelegramClient(
        session,
        config.TELEGRAM_API_ID,
        config.TELEGRAM_API_HASH,
    )
    
    logger.debug("Connecting to Telegram for request...")
    await client.connect()

    if not await client.is_user_authorized():
        await client.disconnect()
        raise ValueError("Telegram user is not authorized. Check your credentials.")
    
    logger.debug("Telegram client connected and authorized.")
    
    try:
        yield client
    finally:
        logger.debug("Disconnecting Telegram client after request.")
        await client.disconnect()
