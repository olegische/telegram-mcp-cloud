import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from telethon import TelegramClient, utils

from config import log_and_format_error


logger = logging.getLogger("telegram_mcp")

def format_message(message) -> Dict[str, Any]:
    """Helper function to format message information consistently."""
    result = {
        "id": message.id,
        "date": message.date.isoformat(),
        "text": message.message or "",
    }

    if message.from_id:
        result["from_id"] = utils.get_peer_id(message.from_id)

    if message.media:
        result["has_media"] = True
        result["media_type"] = type(message.media).__name__

    return result

async def get_messages(
    client: TelegramClient, chat_id: int, page: int = 1, page_size: int = 20
) -> str:
    """
    Get paginated messages from a specific chat.
    Args:
        chat_id: The ID of the chat.
        page: Page number (1-indexed).
        page_size: Number of messages per page.
    """
    try:
        entity = await client.get_entity(chat_id)
        offset = (page - 1) * page_size
        messages = await client.get_messages(
            entity, limit=page_size, add_offset=offset
        )
        if not messages:
            return "No messages found for this page."
        lines = []
        for msg in messages:
            lines.append(f"ID: {msg.id} | Date: {msg.date} | Message: {msg.message}")
        return "\n".join(lines)
    except Exception as e:
        return log_and_format_error(
            "get_messages", e, chat_id=chat_id, page=page, page_size=page_size
        )

async def send_message(client: TelegramClient, chat_id: int, message: str) -> str:
    """
    Send a message to a specific chat.
    Args:
        chat_id: The ID of the chat.
        message: The message content to send.
    """
    try:
        entity = await client.get_entity(chat_id)
        await client.send_message(entity, message)
        return "Message sent successfully."
    except Exception as e:
        return log_and_format_error("send_message", e, chat_id=chat_id)

async def list_messages(
    client: TelegramClient,
    chat_id: int,
    limit: int = 20,
    search_query: str = None,
    from_date: str = None,
    to_date: str = None,
) -> str:
    """
    Retrieve messages with optional filters.

    Args:
        chat_id: The ID of the chat to get messages from.
        limit: Maximum number of messages to retrieve.
        search_query: Filter messages containing this text.
        from_date: Filter messages starting from this date (format: YYYY-MM-DD).
        to_date: Filter messages until this date (format: YYYY-MM-DD).
    """
    try:
        entity = await client.get_entity(chat_id)

        from_date_obj = None
        to_date_obj = None

        if from_date:
            try:
                from_date_obj = datetime.strptime(from_date, "%Y-%m-%d")
                try:
                    from_date_obj = from_date_obj.replace(
                        tzinfo=datetime.timezone.utc
                    )
                except AttributeError:
                    from datetime import timezone

                    from_date_obj = from_date_obj.replace(tzinfo=timezone.utc)
            except ValueError:
                return f"Invalid from_date format. Use YYYY-MM-DD."

        if to_date:
            try:
                to_date_obj = datetime.strptime(to_date, "%Y-%m-%d")
                to_date_obj = to_date_obj + timedelta(days=1, microseconds=-1)
                try:
                    to_date_obj = to_date_obj.replace(tzinfo=datetime.timezone.utc)
                except AttributeError:
                    from datetime import timezone

                    to_date_obj = to_date_obj.replace(tzinfo=timezone.utc)
            except ValueError:
                return f"Invalid to_date format. Use YYYY-MM-DD."

        params = {}
        if search_query:
            params["search"] = search_query

        messages = await client.get_messages(entity, limit=limit, **params)

        if from_date_obj or to_date_obj:
            filtered_messages = []
            for msg in messages:
                if from_date_obj and msg.date < from_date_obj:
                    continue
                if to_date_obj and msg.date > to_date_obj:
                    continue
                filtered_messages.append(msg)
            messages = filtered_messages

        if not messages:
            return "No messages found matching the criteria."

        lines = []
        for msg in messages:
            sender = ""
            if msg.sender:
                sender_name = getattr(
                    msg.sender, "first_name", ""
                ) or getattr(msg.sender, "title", "Unknown")
                sender = f"{sender_name} | "

            lines.append(
                f"ID: {msg.id} | {sender}Date: {msg.date} | Message: {msg.message or '[Media/No text]'}"
            )

        return "\n".join(lines)
    except Exception as e:
        return log_and_format_error("list_messages", e, chat_id=chat_id)

async def get_message_context(
    client: TelegramClient, chat_id: int, message_id: int, context_size: int = 3
) -> str:
    """
    Retrieve context around a specific message.

    Args:
        chat_id: The ID of the chat.
        message_id: The ID of the central message.
        context_size: Number of messages before and after to include.
    """
    try:
        chat = await client.get_entity(chat_id)
        messages_before = await client.get_messages(
            chat, limit=context_size, max_id=message_id
        )
        central_message = await client.get_messages(chat, ids=message_id)
        if central_message is not None and not isinstance(central_message, list):
            central_message = [central_message]
        elif central_message is None:
            central_message = []
        messages_after = await client.get_messages(
            chat, limit=context_size, min_id=message_id, reverse=True
        )
        if not central_message:
            return f"Message with ID {message_id} not found in chat {chat_id}."
        all_messages = (
            list(messages_before) + list(central_message) + list(messages_after)
        )
        all_messages.sort(key=lambda m: m.id)
        results = [f"Context for message {message_id} in chat {chat_id}:"]
        for msg in all_messages:
            sender_name = "Unknown"
            if msg.sender:
                sender_name = getattr(
                    msg.sender, "first_name", ""
                ) or getattr(msg.sender, "title", "Unknown")
            highlight = " [THIS MESSAGE]" if msg.id == message_id else ""
            results.append(
                f"ID: {msg.id} | {sender_name} | {msg.date}{highlight}\n{msg.message or '[Media/No text]'}\n"
            )
        return "\n".join(results)
    except Exception as e:
        return log_and_format_error(
            "get_message_context",
            e,
            chat_id=chat_id,
            message_id=message_id,
            context_size=context_size,
        )

async def forward_message(
    client: TelegramClient, from_chat_id: int, message_id: int, to_chat_id: int
) -> str:
    """
    Forward a message from one chat to another.
    """
    try:
        from_entity = await client.get_entity(from_chat_id)
        to_entity = await client.get_entity(to_chat_id)
        await client.forward_messages(to_entity, message_id, from_entity)
        return (
            f"Message {message_id} forwarded from {from_chat_id} to {to_chat_id}."
        )
    except Exception as e:
        return log_and_format_error(
            "forward_message",
            e,
            from_chat_id=from_chat_id,
            message_id=message_id,
            to_chat_id=to_chat_id,
        )

async def edit_message(
    client: TelegramClient, chat_id: int, message_id: int, new_text: str
) -> str:
    """
    Edit a message you sent.
    """
    try:
        entity = await client.get_entity(chat_id)
        await client.edit_message(entity, message_id, new_text)
        return f"Message {message_id} edited."
    except Exception as e:
        return log_and_format_error(
            "edit_message",
            e,
            chat_id=chat_id,
            message_id=message_id,
            new_text=new_text,
        )

async def delete_message(
    client: TelegramClient, chat_id: int, message_id: int
) -> str:
    """
    Delete a message by ID.
    """
    try:
        entity = await client.get_entity(chat_id)
        await client.delete_messages(entity, message_id)
        return f"Message {message_id} deleted."
    except Exception as e:
        return log_and_format_error(
            "delete_message", e, chat_id=chat_id, message_id=message_id
        )

async def pin_message(client: TelegramClient, chat_id: int, message_id: int) -> str:
    """
    Pin a message in a chat.
    """
    try:
        entity = await client.get_entity(chat_id)
        await client.pin_message(entity, message_id)
        return f"Message {message_id} pinned in chat {chat_id}."
    except Exception as e:
        return log_and_format_error(
            "pin_message", e, chat_id=chat_id, message_id=message_id
        )

async def unpin_message(client: TelegramClient, chat_id: int, message_id: int) -> str:
    """
    Unpin a message in a chat.
    """
    try:
        entity = await client.get_entity(chat_id)
        await client.unpin_message(entity, message_id)
        return f"Message {message_id} unpinned in chat {chat_id}."
    except Exception as e:
        return log_and_format_error(
            "unpin_message", e, chat_id=chat_id, message_id=message_id
        )

async def mark_as_read(client: TelegramClient, chat_id: int) -> str:
    """
    Mark all messages as read in a chat.
    """
    try:
        entity = await client.get_entity(chat_id)
        await client.send_read_acknowledge(entity)
        return f"Marked all messages as read in chat {chat_id}."
    except Exception as e:
        return log_and_format_error("mark_as_read", e, chat_id=chat_id)

async def reply_to_message(
    client: TelegramClient, chat_id: int, message_id: int, text: str
) -> str:
    """
    Reply to a specific message in a chat.
    """
    try:
        entity = await client.get_entity(chat_id)
        await client.send_message(entity, text, reply_to=message_id)
        return f"Replied to message {message_id} in chat {chat_id}."
    except Exception as e:
        return log_and_format_error(
            "reply_to_message", e, chat_id=chat_id, message_id=message_id, text=text
        )

async def get_history(client: TelegramClient, chat_id: int, limit: int = 100) -> str:
    """
    Get full chat history (up to limit).
    """
    try:
        entity = await client.get_entity(chat_id)
        messages = await client.get_messages(entity, limit=limit)
        return "\n".join(
            [f"ID: {m.id} | {m.date} | {m.message}" for m in messages]
        )
    except Exception as e:
        return log_and_format_error("get_history", e, chat_id=chat_id, limit=limit)
