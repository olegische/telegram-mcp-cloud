import json
import logging

from telethon import TelegramClient, functions

from config import format_entity, log_and_format_error


logger = logging.getLogger("telegram_mcp")

async def search_public_chats(client: TelegramClient, query: str) -> str:
    """
    Search for public chats, channels, or bots by username or title.
    """
    try:
        result = await client(functions.contacts.SearchRequest(q=query, limit=20))
        return json.dumps([format_entity(u) for u in result.users], indent=2)
    except Exception as e:
        return log_and_format_error("search_public_chats", e, query=query)

async def search_messages(
    client: TelegramClient, chat_id: int, query: str, limit: int = 20
) -> str:
    """
    Search for messages in a chat by text.
    """
    try:
        entity = await client.get_entity(chat_id)
        messages = await client.get_messages(entity, limit=limit, search=query)
        return "\n".join(
            [f"ID: {m.id} | {m.date} | {m.message}" for m in messages]
        )
    except Exception as e:
        return log_and_format_error(
            "search_messages", e, chat_id=chat_id, query=query, limit=limit
        )

async def resolve_username(client: TelegramClient, username: str) -> str:
    """
    Resolve a username to a user or chat ID.
    """
    try:
        result = await client(
            functions.contacts.ResolveUsernameRequest(username=username)
        )
        return str(result)
    except Exception as e:
        return log_and_format_error("resolve_username", e, username=username)
