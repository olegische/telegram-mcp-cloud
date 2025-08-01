import json
import logging

from telethon import TelegramClient, functions

from ..config import format_entity, log_and_format_error


logger = logging.getLogger("telegram_mcp")

async def get_me(client: TelegramClient) -> str:
    """
    Get your own user information.
    """
    try:
        me = await client.get_me()
        return json.dumps(format_entity(me), indent=2)
    except Exception as e:
        return log_and_format_error("get_me", e)

async def update_profile(
    client: TelegramClient,
    first_name: str = None,
    last_name: str = None,
    about: str = None,
) -> str:
    """
    Update your profile information (name, bio).
    """
    try:
        await client(
            functions.account.UpdateProfileRequest(
                first_name=first_name, last_name=last_name, about=about
            )
        )
        return "Profile updated."
    except Exception as e:
        return log_and_format_error(
            "update_profile",
            e,
            first_name=first_name,
            last_name=last_name,
            about=about,
        )

async def set_profile_photo(client: TelegramClient, file_path: str) -> str:
    """
    Set a new profile photo.
    """
    try:
        await client(
            functions.photos.UploadProfilePhotoRequest(
                file=await client.upload_file(file_path)
            )
        )
        return "Profile photo updated."
    except Exception as e:
        return log_and_format_error("set_profile_photo", e, file_path=file_path)

async def delete_profile_photo(client: TelegramClient) -> str:
    """
    Delete your current profile photo.
    """
    try:
        photos = await client(
            functions.photos.GetUserPhotosRequest(
                user_id="me", offset=0, max_id=0, limit=1
            )
        )
        if not photos.photos:
            return "No profile photo to delete."
        await client(functions.photos.DeletePhotosRequest(id=[photos.photos[0].id]))
        return "Profile photo deleted."
    except Exception as e:
        return log_and_format_error("delete_profile_photo", e)

async def get_user_photos(
    client: TelegramClient, user_id: int, limit: int = 10
) -> str:
    """
    Get profile photos of a user.
    """
    try:
        user = await client.get_entity(user_id)
        photos = await client(
            functions.photos.GetUserPhotosRequest(
                user_id=user, offset=0, max_id=0, limit=limit
            )
        )
        return json.dumps([p.id for p in photos.photos], indent=2)
    except Exception as e:
        return log_and_format_error(
            "get_user_photos", e, user_id=user_id, limit=limit
        )

async def get_user_status(client: TelegramClient, user_id: int) -> str:
    """
    Get the online status of a user.
    """
    try:
        user = await client.get_entity(user_id)
        return str(user.status)
    except Exception as e:
        return log_and_format_error("get_user_status", e, user_id=user_id)
