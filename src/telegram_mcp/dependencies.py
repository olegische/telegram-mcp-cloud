"""MCP dependencies for dependency injection."""
import logging
import contextlib
from typing import AsyncGenerator

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


def get_config(context: Context = None) -> ServiceConfig:
    """Get ServiceConfig object for the current request.

    Loads ServiceConfig from the environment and overrides credentials with
    values from request headers if they are present. Session names cannot be
    passed via headers and are only supported for local configuration.

    Args:
        context: MCP server context

    Returns:
        ServiceConfig object

    Raises:
        ValueError: If partial or forbidden credentials are provided in headers.
    """
    config = ServiceConfig()
    if not context:
        return config
        
    headers = get_authentication_headers(context)

    # If no headers are present (e.g., stdio mode), use default config.
    if not headers:
        return config

    if headers.get("x-telegram-session-name"):
        raise ValueError(
            "Passing session name via headers is not supported. "
            "Please use a session string (X-Telegram-Session-String)."
        )

    header_creds = {
        "api_id": headers.get("x-telegram-api-id"),
        "api_hash": headers.get("x-telegram-api-hash"),
        "session_string": headers.get("x-telegram-session-string"),
    }

    # If any credential headers are present, all must be.
    if any(header_creds.values()):
        missing_keys = [k for k, v in header_creds.items() if v is None]
        if missing_keys:
            raise ValueError(
                f"Missing required Telegram credential headers: {', '.join(missing_keys)}"
            )

        logger.debug("Overriding config with credentials from headers.")
        config.TELEGRAM_API_ID = int(header_creds["api_id"])
        config.TELEGRAM_API_HASH = header_creds["api_hash"]
        config.SESSION_STRING = header_creds["session_string"]
        # Ensure session name from env is ignored when string is from header
        config.TELEGRAM_SESSION_NAME = None

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
