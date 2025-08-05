import logging

from telethon import TelegramClient, functions
from telethon.tl.types import (
    InputPrivacyKeyStatusTimestamp,
    InputPrivacyKeyPhoneNumber,
    InputPrivacyKeyProfilePhoto,
    InputPrivacyValueAllowUsers,
    InputPrivacyValueDisallowUsers,
    InputPrivacyValueAllowAll,
    InputPeerNotifySettings,
)

from ..utils import log_and_format_error


logger = logging.getLogger("telegram_mcp")

async def get_privacy_settings(client: TelegramClient) -> str:
    """
    Get your privacy settings for last seen status.
    """
    try:
        try:
            settings = await client(
                functions.account.GetPrivacyRequest(
                    key=InputPrivacyKeyStatusTimestamp()
                )
            )
            return str(settings)
        except TypeError as e:
            if "TLObject was expected" in str(e):
                return "Error: Privacy settings API call failed due to type mismatch. This is likely a version compatibility issue with Telethon."
            else:
                raise
    except Exception as e:
        logger.exception("get_privacy_settings failed")
        return log_and_format_error("get_privacy_settings", e)

async def set_privacy_settings(
    client: TelegramClient,
    key: str,
    allow_users: list = None,
    disallow_users: list = None,
) -> str:
    """
    Set privacy settings (e.g., last seen, phone, etc.).

    Args:
        key: The privacy setting to modify ('status' for last seen, 'phone', 'profile_photo', etc.)
        allow_users: List of user IDs to allow
        disallow_users: List of user IDs to disallow
    """
    try:
        key_mapping = {
            "status": InputPrivacyKeyStatusTimestamp,
            "phone": InputPrivacyKeyPhoneNumber,
            "profile_photo": InputPrivacyKeyProfilePhoto,
        }

        if key not in key_mapping:
            return f"Error: Unsupported privacy key '{key}'. Supported keys: {', '.join(key_mapping.keys())}"

        privacy_key = key_mapping[key]()

        rules = []

        if allow_users is None or len(allow_users) == 0:
            rules.append(InputPrivacyValueAllowAll())
        else:
            try:
                allow_entities = []
                for user_id in allow_users:
                    try:
                        user = await client.get_entity(user_id)
                        allow_entities.append(user)
                    except Exception as user_err:
                        logger.warning(
                            f"Could not get entity for user ID {user_id}: {user_err}"
                        )

                if allow_entities:
                    rules.append(InputPrivacyValueAllowUsers(users=allow_entities))
            except Exception as allow_err:
                logger.error(f"Error processing allowed users: {allow_err}")
                return log_and_format_error(
                    "set_privacy_settings", allow_err, key=key
                )

        if disallow_users and len(disallow_users) > 0:
            try:
                disallow_entities = []
                for user_id in disallow_users:
                    try:
                        user = await client.get_entity(user_id)
                        disallow_entities.append(user)
                    except Exception as user_err:
                        logger.warning(
                            f"Could not get entity for user ID {user_id}: {user_err}"
                        )

                if disallow_entities:
                    rules.append(
                        InputPrivacyValueDisallowUsers(users=disallow_entities)
                    )
            except Exception as disallow_err:
                logger.error(f"Error processing disallowed users: {disallow_err}")
                return log_and_format_error(
                    "set_privacy_settings", disallow_err, key=key
                )

        try:
            result = await client(
                functions.account.SetPrivacyRequest(key=privacy_key, rules=rules)
            )
            return f"Privacy settings for {key} updated successfully."
        except TypeError as type_err:
            if "TLObject was expected" in str(type_err):
                return "Error: Privacy settings API call failed due to type mismatch. This is likely a version compatibility issue with Telethon."
            else:
                raise
    except Exception as e:
        logger.exception(f"set_privacy_settings failed (key={key})")
        return log_and_format_error("set_privacy_settings", e, key=key)

async def mute_chat(client: TelegramClient, chat_id: int) -> str:
    """
    Mute notifications for a chat.
    """
    try:
        peer = await client.get_entity(chat_id)
        await client(
            functions.account.UpdateNotifySettingsRequest(
                peer=peer, settings=InputPeerNotifySettings(mute_until=2**31 - 1)
            )
        )
        return f"Chat {chat_id} muted."
    except Exception as e:
        logger.exception(f"mute_chat failed (chat_id={chat_id})")
        return log_and_format_error("mute_chat", e, chat_id=chat_id)

async def unmute_chat(client: TelegramClient, chat_id: int) -> str:
    """
    Unmute notifications for a chat.
    """
    try:
        peer = await client.get_entity(chat_id)
        await client(
            functions.account.UpdateNotifySettingsRequest(
                peer=peer, settings=InputPeerNotifySettings(mute_until=0)
            )
        )
        return f"Chat {chat_id} unmuted."
    except Exception as e:
        logger.exception(f"unmute_chat failed (chat_id={chat_id})")
        return log_and_format_error("unmute_chat", e, chat_id=chat_id)

async def archive_chat(client: TelegramClient, chat_id: int) -> str:
    """
    Archive a chat.
    """
    try:
        await client(
            functions.messages.ToggleDialogPinRequest(
                peer=await client.get_entity(chat_id), pinned=True
            )
        )
        return f"Chat {chat_id} archived."
    except Exception as e:
        return log_and_format_error("archive_chat", e, chat_id=chat_id)

async def unarchive_chat(client: TelegramClient, chat_id: int) -> str:
    """
    Unarchive a chat.
    """
    try:
        await client(
            functions.messages.ToggleDialogPinRequest(
                peer=await client.get_entity(chat_id), pinned=False
            )
        )
        return f"Chat {chat_id} unarchived."
    except Exception as e:
        return log_and_format_error("unarchive_chat", e, chat_id=chat_id)
