import os
import sys
import asyncio
import logging

from dotenv import load_dotenv

def setup_environment() -> bool:
    """
    Loads environment variables and configures application-wide logging.
    """
    load_dotenv()

    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.info("Environment and logging configured.")
    return True

async def run_server() -> None:
    """
    Sets up the environment and runs the MCP server.
    """
    if not setup_environment():
        logging.critical("Initial environment setup failed. Exiting.")
        sys.exit(1)

    from .server import mcp_server
    from .dependencies import get_config

    server_config = get_config()
    logger = logging.getLogger(__name__)
    logger.info("--- Telegram MCP Server ---")
    logger.info("Starting server with transport: %s", server_config.MCP_TRANSPORT)

    try:
        logger.info("Running MCP server...")
        try:
            # Check if an event loop is already running (e.g., under `uv run`)
            asyncio.get_running_loop()
            is_async_context = True
        except RuntimeError:
            is_async_context = False

        if is_async_context:
            # If in an async context, call the async version of the server's run method
            if server_config.MCP_TRANSPORT == "stdio":
                await mcp_server.run_stdio_async()
            elif server_config.MCP_TRANSPORT == "sse":
                # The server is already an ASGI app, we can run it with uvicorn
                # The host/port are configured in the server instance now
                await mcp_server.run_sse_async()
            else:
                logger.critical(
                    f"Unsupported transport for async execution: {server_config.MCP_TRANSPORT}"
                )
                sys.exit(1)
        else:
            # Otherwise, use the blocking run method
            mcp_server.run(transport=server_config.MCP_TRANSPORT)

        logger.info("MCP server stopped.")

    except Exception as e:
        logger.critical(f"Fatal error in main server loop: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_server())
