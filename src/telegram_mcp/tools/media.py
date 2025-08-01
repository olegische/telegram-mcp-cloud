import os
import logging
import mimetypes

from telethon import TelegramClient

from config import log_and_format_error


logger = logging.getLogger("telegram_mcp")

async def send_file(
    client: TelegramClient, chat_id: int, file_path: str, caption: str = None
) -> str:
    """
    Send a file to a chat.
    Args:
        chat_id: The chat ID.
        file_path: Absolute path to the file to send (must exist and be readable).
        caption: Optional caption for the file.
    """
    try:
        if not os.path.isfile(file_path):
            return f"File not found: {file_path}"
        if not os.access(file_path, os.R_OK):
            return f"File is not readable: {file_path}"
        entity = await client.get_entity(chat_id)
        await client.send_file(entity, file_path, caption=caption)
        return f"File sent to chat {chat_id}."
    except Exception as e:
        return log_and_format_error(
            "send_file", e, chat_id=chat_id, file_path=file_path, caption=caption
        )

async def download_media(
    client: TelegramClient, chat_id: int, message_id: int, file_path: str
) -> str:
    """
    Download media from a message in a chat.
    Args:
        chat_id: The chat ID.
        message_id: The message ID containing the media.
        file_path: Absolute path to save the downloaded file (must be writable).
    """
    try:
        entity = await client.get_entity(chat_id)
        msg = await client.get_messages(entity, ids=message_id)
        if not msg or not msg.media:
            return "No media found in the specified message."
        dir_path = os.path.dirname(file_path) or "."
        if not os.access(dir_path, os.W_OK):
            return f"Directory not writable: {dir_path}"
        await client.download_media(msg, file=file_path)
        if not os.path.isfile(file_path):
            return f"Download failed: file not created at {file_path}"
        return f"Media downloaded to {file_path}."
    except Exception as e:
        return log_and_format_error(
            "download_media",
            e,
            chat_id=chat_id,
            message_id=message_id,
            file_path=file_path,
        )

async def send_voice(client: TelegramClient, chat_id: int, file_path: str) -> str:
    """
    Send a voice message to a chat. File must be an OGG/OPUS voice note.
    Args:
        chat_id: The chat ID.
        file_path: Absolute path to the OGG/OPUS file.
    """
    try:
        if not os.path.isfile(file_path):
            return f"File not found: {file_path}"
        if not os.access(file_path, os.R_OK):
            return f"File is not readable: {file_path}"
        mime, _ = mimetypes.guess_type(file_path)
        if not (
            mime
            and (
                mime == "audio/ogg"
                or file_path.lower().endswith(".ogg")
                or file_path.lower().endswith(".opus")
            )
        ):
            return "Voice file must be .ogg or .opus format."
        entity = await client.get_entity(chat_id)
        await client.send_file(entity, file_path, voice_note=True)
        return f"Voice message sent to chat {chat_id}."
    except Exception as e:
        return log_and_format_error(
            "send_voice", e, chat_id=chat_id, file_path=file_path
        )

async def get_media_info(
    client: TelegramClient, chat_id: int, message_id: int
) -> str:
    """
    Get info about media in a message.
    Args:
        chat_id: The chat ID.
        message_id: The message ID.
    """
    try:
        entity = await client.get_entity(chat_id)
        msg = await client.get_messages(entity, ids=message_id)
        if not msg or not msg.media:
            return "No media found in the specified message."
        return str(msg.media)
    except Exception as e:
        return log_and_format_error(
            "get_media_info", e, chat_id=chat_id, message_id=message_id
        )
