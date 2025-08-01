import os
import json
import logging

from telethon import TelegramClient, functions
from telethon.tl.types import (
    BotCommand,
    BotCommandScopeDefault,
    InputMessagesFilterGif,
)

from ..config import json_serializer, log_and_format_error


logger = logging.getLogger("telegram_mcp")

async def get_sticker_sets(client: TelegramClient) -> str:
    """
    Get all sticker sets.
    """
    try:
        result = await client(functions.messages.GetAllStickersRequest(hash=0))
        return json.dumps([s.title for s in result.sets], indent=2)
    except Exception as e:
        return log_and_format_error("get_sticker_sets", e)

async def send_sticker(client: TelegramClient, chat_id: int, file_path: str) -> str:
    """
    Send a sticker to a chat. File must be a valid .webp sticker file.
    Args:
        chat_id: The chat ID.
        file_path: Absolute path to the .webp sticker file.
    """
    try:
        if not os.path.isfile(file_path):
            return f"Sticker file not found: {file_path}"
        if not os.access(file_path, os.R_OK):
            return f"Sticker file is not readable: {file_path}"
        if not file_path.lower().endswith(".webp"):
            return "Sticker file must be a .webp file."
        entity = await client.get_entity(chat_id)
        await client.send_file(entity, file_path, force_document=False)
        return f"Sticker sent to chat {chat_id}."
    except Exception as e:
        return log_and_format_error(
            "send_sticker", e, chat_id=chat_id, file_path=file_path
        )

async def get_gif_search(
    client: TelegramClient, query: str, limit: int = 10
) -> str:
    """
    Search for GIFs by query. Returns a list of Telegram document IDs (not file paths).
    Args:
        query: Search term for GIFs.
        limit: Max number of GIFs to return.
    """
    try:
        try:
            result = await client(
                functions.messages.SearchGifsRequest(
                    q=query, offset_id=0, limit=limit
                )
            )
            if not result.gifs:
                return "[]"
            return json.dumps(
                [g.document.id for g in result.gifs],
                indent=2,
                default=json_serializer,
            )
        except (AttributeError, ImportError):
            try:
                result = await client(
                    functions.messages.SearchRequest(
                        peer="gif",
                        q=query,
                        filter=InputMessagesFilterGif(),
                        min_date=None,
                        max_date=None,
                        offset_id=0,
                        add_offset=0,
                        limit=limit,
                        max_id=0,
                        min_id=0,
                        hash=0,
                    )
                )
                if (
                    not result
                    or not hasattr(result, "messages")
                    or not result.messages
                ):
                    return "[]"
                gif_ids = []
                for msg in result.messages:
                    if (
                        hasattr(msg, "media")
                        and msg.media
                        and hasattr(msg.media, "document")
                    ):
                        gif_ids.append(msg.media.document.id)
                return json.dumps(gif_ids, default=json_serializer)
            except Exception as inner_e:
                return f"Could not search GIFs using available methods: {inner_e}"
    except Exception as e:
        logger.exception(
            f"get_gif_search failed (query={query}, limit={limit})"
        )
        return log_and_format_error(
            "get_gif_search", e, query=query, limit=limit
        )

async def send_gif(client: TelegramClient, chat_id: int, gif_id: int) -> str:
    """
    Send a GIF to a chat by Telegram GIF document ID (not a file path).
    Args:
        chat_id: The chat ID.
        gif_id: Telegram document ID for the GIF (from get_gif_search).
    """
    try:
        if not isinstance(gif_id, int):
            return "gif_id must be a Telegram document ID (integer), not a file path. Use get_gif_search to find IDs."
        entity = await client.get_entity(chat_id)
        await client.send_file(entity, gif_id)
        return f"GIF sent to chat {chat_id}."
    except Exception as e:
        return log_and_format_error("send_gif", e, chat_id=chat_id, gif_id=gif_id)

async def get_bot_info(client: TelegramClient, bot_username: str) -> str:
    """
    Get information about a bot by username.
    """
    try:
        entity = await client.get_entity(bot_username)
        if not entity:
            return f"Bot with username {bot_username} not found."

        result = await client(functions.users.GetFullUserRequest(id=entity))

        if hasattr(result, "to_dict"):
            return json.dumps(result.to_dict(), indent=2, default=json_serializer)
        else:
            info = {
                "bot_info": {
                    "id": entity.id,
                    "username": entity.username,
                    "first_name": entity.first_name,
                    "last_name": getattr(entity, "last_name", ""),
                    "is_bot": getattr(entity, "bot", False),
                    "verified": getattr(entity, "verified", False),
                }
            }
            if hasattr(result, "full_user") and hasattr(
                result.full_user, "about"
            ):
                info["bot_info"]["about"] = result.full_user.about

            return json.dumps(info, indent=2)
    except Exception as e:
        logger.exception(
            f"get_bot_info failed (bot_username={bot_username})"
        )
        return log_and_format_error(
            "get_bot_info", e, bot_username=bot_username
        )

async def set_bot_commands(
    client: TelegramClient, bot_username: str, commands: list
) -> str:
    """
    Set bot commands for a bot you own.
    Note: This function can only be used if the Telegram client is a bot account.
    Regular user accounts cannot set bot commands.

    Args:
        bot_username: The username of the bot to set commands for.
        commands: List of command dictionaries with 'command' and 'description' keys.
    """
    try:
        me = await client.get_me()
        if not getattr(me, "bot", False):
            return "Error: This function can only be used by bot accounts. Your current Telegram account is a regular user account, not a bot."

        bot_commands = [
            BotCommand(command=c["command"], description=c["description"])
            for c in commands
        ]

        bot = await client.get_entity(bot_username)

        await client(
            functions.bots.SetBotCommandsRequest(
                scope=BotCommandScopeDefault(),
                lang_code="en",
                commands=bot_commands,
            )
        )

        return f"Bot commands set for {bot_username}."
    except Exception as e:
        logger.exception(
            f"set_bot_commands failed (bot_username={bot_username})"
        )
        return log_and_format_error(
            "set_bot_commands", e, bot_username=bot_username
        )
