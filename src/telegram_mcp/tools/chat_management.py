import os
import json
import logging
import asyncio

from telethon import TelegramClient, functions
from telethon.tl.types import (
    User,
    Chat,
    Channel,
    ChatAdminRights,
    ChatBannedRights,
    ChannelParticipantsKicked,
    ChannelParticipantsAdmins,
    InputChatUploadedPhoto,
    InputChatPhotoEmpty,
)
import telethon.errors.rpcerrorlist

from ..config import json_serializer, log_and_format_error


logger = logging.getLogger("telegram_mcp")

async def get_chats(client: TelegramClient, page: int = 1, page_size: int = 20) -> str:
    """
    Get a paginated list of chats.
    Args:
        page: Page number (1-indexed).
        page_size: Number of chats per page.
    """
    try:
        dialogs = await client.get_dialogs()
        start = (page - 1) * page_size
        end = start + page_size
        if start >= len(dialogs):
            return "Page out of range."
        chats = dialogs[start:end]
        lines = []
        for dialog in chats:
            entity = dialog.entity
            chat_id = entity.id
            title = getattr(entity, "title", None) or getattr(
                entity, "first_name", "Unknown"
            )
            lines.append(f"Chat ID: {chat_id}, Title: {title}")
        return "\n".join(lines)
    except Exception as e:
        return log_and_format_error("get_chats", e)

async def list_chats(
    client: TelegramClient, chat_type: str = None, limit: int = 20
) -> str:
    """
    List available chats with metadata.

    Args:
        chat_type: Filter by chat type ('user', 'group', 'channel', or None for all)
        limit: Maximum number of chats to retrieve.
    """
    try:
        dialogs = await client.get_dialogs(limit=limit)
        results = []
        for dialog in dialogs:
            entity = dialog.entity
            current_type = None
            if isinstance(entity, User):
                current_type = "user"
            elif isinstance(entity, Chat):
                current_type = "group"
            elif isinstance(entity, Channel):
                if getattr(entity, "broadcast", False):
                    current_type = "channel"
                else:
                    current_type = "group"
            if chat_type and current_type != chat_type.lower():
                continue
            chat_info = f"Chat ID: {entity.id}"
            if hasattr(entity, "title"):
                chat_info += f", Title: {entity.title}"
            elif hasattr(entity, "first_name"):
                name = f"{entity.first_name}"
                if hasattr(entity, "last_name") and entity.last_name:
                    name += f" {entity.last_name}"
                chat_info += f", Name: {name}"
            chat_info += f", Type: {current_type}"
            if hasattr(entity, "username") and entity.username:
                chat_info += f", Username: @{entity.username}"
            if hasattr(dialog, "unread_count") and dialog.unread_count > 0:
                chat_info += f", Unread: {dialog.unread_count}"
            results.append(chat_info)
        if not results:
            return f"No chats found matching the criteria."
        return "\n".join(results)
    except Exception as e:
        return log_and_format_error(
            "list_chats", e, chat_type=chat_type, limit=limit
        )

async def get_chat(client: TelegramClient, chat_id: int) -> str:
    """
    Get detailed information about a specific chat.

    Args:
        chat_id: The ID of the chat.
    """
    try:
        entity = await client.get_entity(chat_id)
        result = []
        result.append(f"ID: {entity.id}")
        is_channel = isinstance(entity, Channel)
        is_chat = isinstance(entity, Chat)
        is_user = isinstance(entity, User)
        if hasattr(entity, "title"):
            result.append(f"Title: {entity.title}")
            chat_type = (
                "Channel"
                if is_channel and getattr(entity, "broadcast", False)
                else "Group"
            )
            if is_channel and getattr(entity, "megagroup", False):
                chat_type = "Supergroup"
            elif is_chat:
                chat_type = "Group (Basic)"
            result.append(f"Type: {chat_type}")
            if hasattr(entity, "username") and entity.username:
                result.append(f"Username: @{entity.username}")
            try:
                participants_count = (
                    await client.get_participants(entity, limit=0)
                ).total
                result.append(f"Participants: {participants_count}")
            except Exception as pe:
                result.append(f"Participants: Error fetching ({pe})")
        elif is_user:
            name = f"{entity.first_name}"
            if entity.last_name:
                name += f" {entity.last_name}"
            result.append(f"Name: {name}")
            result.append(f"Type: User")
            if entity.username:
                result.append(f"Username: @{entity.username}")
            if entity.phone:
                result.append(f"Phone: {entity.phone}")
            result.append(f"Bot: {'Yes' if entity.bot else 'No'}")
            result.append(f"Verified: {'Yes' if entity.verified else 'No'}")
        try:
            dialog = await client.get_dialogs(
                limit=1, offset_id=0, offset_peer=entity
            )
            if dialog:
                dialog = dialog[0]
                result.append(f"Unread Messages: {dialog.unread_count}")
                if dialog.message:
                    last_msg = dialog.message
                    sender_name = "Unknown"
                    if last_msg.sender:
                        sender_name = (
                            getattr(last_msg.sender, "first_name", "")
                            or getattr(last_msg.sender, "title", "Unknown")
                        )
                        if (
                            hasattr(last_msg.sender, "last_name")
                            and last_msg.sender.last_name
                        ):
                            sender_name += f" {last_msg.sender.last_name}"
                    sender_name = sender_name.strip() or "Unknown"
                    result.append(
                        f"Last Message: From {sender_name} at {last_msg.date}"
                    )
                    result.append(
                        f"Message: {last_msg.message or '[Media/No text]'}"
                    )
        except Exception as diag_ex:
            logger.warning(f"Could not get dialog info for {chat_id}: {diag_ex}")
            pass
        return "\n".join(result)
    except Exception as e:
        return log_and_format_error("get_chat", e, chat_id=chat_id)

async def create_group(client: TelegramClient, title: str, user_ids: list) -> str:
    """
    Create a new group or supergroup and add users.

    Args:
        title: Title for the new group
        user_ids: List of user IDs to add to the group
    """
    try:
        users = []
        for user_id in user_ids:
            try:
                user = await client.get_entity(user_id)
                users.append(user)
            except Exception as e:
                logger.error(f"Failed to get entity for user ID {user_id}: {e}")
                return f"Error: Could not find user with ID {user_id}"
        if not users:
            return "Error: No valid users provided"
        try:
            result = await client(
                functions.messages.CreateChatRequest(users=users, title=title)
            )
            if hasattr(result, "chats") and result.chats:
                created_chat = result.chats[0]
                return f"Group created with ID: {created_chat.id}"
            elif hasattr(result, "chat") and result.chat:
                return f"Group created with ID: {result.chat.id}"
            elif hasattr(result, "chat_id"):
                return f"Group created with ID: {result.chat_id}"
            else:
                await asyncio.sleep(1)
                dialogs = await client.get_dialogs(limit=5)
                for dialog in dialogs:
                    if dialog.title == title:
                        return f"Group created with ID: {dialog.id}"
                return f"Group created successfully. Please check your recent chats for '{title}'."
        except Exception as create_err:
            if "PEER_FLOOD" in str(create_err):
                return "Error: Cannot create group due to Telegram limits. Try again later."
            else:
                raise
    except Exception as e:
        logger.exception(
            f"create_group failed (title={title}, user_ids={user_ids})"
        )
        return log_and_format_error(
            "create_group", e, title=title, user_ids=user_ids
        )

async def invite_to_group(
    client: TelegramClient, group_id: int, user_ids: list
) -> str:
    """
    Invite users to a group or channel.

    Args:
        group_id: The ID of the group/channel.
        user_ids: List of user IDs to invite.
    """
    try:
        entity = await client.get_entity(group_id)
        users_to_add = []
        for user_id in user_ids:
            try:
                user = await client.get_entity(user_id)
                users_to_add.append(user)
            except ValueError as e:
                return f"Error: User with ID {user_id} could not be found. {e}"
        try:
            result = await client(
                functions.channels.InviteToChannelRequest(
                    channel=entity, users=users_to_add
                )
            )
            invited_count = 0
            if hasattr(result, "users") and result.users:
                invited_count = len(result.users)
            elif hasattr(result, "count"):
                invited_count = result.count
            return f"Successfully invited {invited_count} users to {entity.title}"
        except telethon.errors.rpcerrorlist.UserNotMutualContactError:
            return "Error: Cannot invite users who are not mutual contacts. Please ensure the users are in your contacts and have added you back."
        except telethon.errors.rpcerrorlist.UserPrivacyRestrictedError:
            return "Error: One or more users have privacy settings that prevent you from adding them."
        except Exception as e:
            return log_and_format_error(
                "invite_to_group", e, group_id=group_id, user_ids=user_ids
            )
    except Exception as e:
        logger.error(
            f"telegram_mcp invite_to_group failed (group_id={group_id}, user_ids={user_ids})",
            exc_info=True,
        )
        return log_and_format_error(
            "invite_to_group", e, group_id=group_id, user_ids=user_ids
        )

async def leave_chat(client: TelegramClient, chat_id: int) -> str:
    """
    Leave a group or channel by chat ID.

    Args:
        chat_id: The chat ID to leave.
    """
    try:
        entity = await client.get_entity(chat_id)
        if isinstance(entity, Channel):
            try:
                await client(functions.channels.LeaveChannelRequest(channel=entity))
                chat_name = getattr(entity, "title", str(chat_id))
                return f"Left channel/supergroup {chat_name} (ID: {chat_id})."
            except Exception as chan_err:
                return log_and_format_error("leave_chat", chan_err, chat_id=chat_id)
        elif isinstance(entity, Chat):
            try:
                me = await client.get_me(input_peer=True)
                await client(
                    functions.messages.DeleteChatUserRequest(
                        chat_id=entity.id, user_id=me
                    )
                )
                chat_name = getattr(entity, "title", str(chat_id))
                return f"Left basic group {chat_name} (ID: {chat_id})."
            except Exception as chat_err:
                logger.warning(
                    f"First leave attempt failed: {chat_err}, trying alternative method"
                )
                try:
                    me_full = await client.get_me()
                    await client(
                        functions.messages.DeleteChatUserRequest(
                            chat_id=entity.id, user_id=me_full.id
                        )
                    )
                    chat_name = getattr(entity, "title", str(chat_id))
                    return f"Left basic group {chat_name} (ID: {chat_id})."
                except Exception as alt_err:
                    return log_and_format_error(
                        "leave_chat", alt_err, chat_id=chat_id
                    )
        else:
            entity_type = type(entity).__name__
            return log_and_format_error(
                "leave_chat",
                Exception(
                    f"Cannot leave chat ID {chat_id} of type {entity_type}. This function is for groups and channels only."
                ),
                chat_id=chat_id,
            )
    except Exception as e:
        logger.exception(f"leave_chat failed (chat_id={chat_id})")
        error_str = str(e).lower()
        if "invalid" in error_str and "chat" in error_str:
            return log_and_format_error(
                "leave_chat",
                Exception(
                    f"Error leaving chat: This appears to be a channel/supergroup. Please check the chat ID and try again."
                ),
                chat_id=chat_id,
            )
        return log_and_format_error("leave_chat", e, chat_id=chat_id)

async def get_participants(client: TelegramClient, chat_id: int) -> str:
    """
    List all participants in a group or channel.
    Args:
        chat_id: The group or channel ID.
    """
    try:
        participants = await client.get_participants(chat_id)
        lines = [
            f"ID: {p.id}, Name: {getattr(p, 'first_name', '')} {getattr(p, 'last_name', '')}"
            for p in participants
        ]
        return "\n".join(lines)
    except Exception as e:
        return log_and_format_error("get_participants", e, chat_id=chat_id)

async def promote_admin(
    client: TelegramClient, group_id: int, user_id: int, rights: dict = None
) -> str:
    """
    Promote a user to admin in a group/channel.

    Args:
        group_id: ID of the group/channel
        user_id: User ID to promote
        rights: Admin rights to give (optional)
    """
    try:
        chat = await client.get_entity(group_id)
        user = await client.get_entity(user_id)
        if not rights:
            rights = {
                "change_info": True,
                "post_messages": True,
                "edit_messages": True,
                "delete_messages": True,
                "ban_users": True,
                "invite_users": True,
                "pin_messages": True,
                "add_admins": False,
                "anonymous": False,
                "manage_call": True,
                "other": True,
            }
        admin_rights = ChatAdminRights(
            change_info=rights.get("change_info", True),
            post_messages=rights.get("post_messages", True),
            edit_messages=rights.get("edit_messages", True),
            delete_messages=rights.get("delete_messages", True),
            ban_users=rights.get("ban_users", True),
            invite_users=rights.get("invite_users", True),
            pin_messages=rights.get("pin_messages", True),
            add_admins=rights.get("add_admins", False),
            anonymous=rights.get("anonymous", False),
            manage_call=rights.get("manage_call", True),
            other=rights.get("other", True),
        )
        try:
            result = await client(
                functions.channels.EditAdminRequest(
                    channel=chat,
                    user_id=user,
                    admin_rights=admin_rights,
                    rank="Admin",
                )
            )
            return f"Successfully promoted user {user_id} to admin in {chat.title}"
        except telethon.errors.rpcerrorlist.UserNotMutualContactError:
            return "Error: Cannot promote users who are not mutual contacts. Please ensure the user is in your contacts and has added you back."
        except Exception as e:
            return log_and_format_error(
                "promote_admin", e, group_id=group_id, user_id=user_id
            )
    except Exception as e:
        logger.error(
            f"telegram_mcp promote_admin failed (group_id={group_id}, user_id={user_id})",
            exc_info=True,
        )
        return log_and_format_error(
            "promote_admin", e, group_id=group_id, user_id=user_id
        )

async def demote_admin(client: TelegramClient, group_id: int, user_id: int) -> str:
    """
    Demote a user from admin in a group/channel.

    Args:
        group_id: ID of the group/channel
        user_id: User ID to demote
    """
    try:
        chat = await client.get_entity(group_id)
        user = await client.get_entity(user_id)
        admin_rights = ChatAdminRights(
            change_info=False,
            post_messages=False,
            edit_messages=False,
            delete_messages=False,
            ban_users=False,
            invite_users=False,
            pin_messages=False,
            add_admins=False,
            anonymous=False,
            manage_call=False,
            other=False,
        )
        try:
            result = await client(
                functions.channels.EditAdminRequest(
                    channel=chat, user_id=user, admin_rights=admin_rights, rank=""
                )
            )
            return f"Successfully demoted user {user_id} from admin in {chat.title}"
        except telethon.errors.rpcerrorlist.UserNotMutualContactError:
            return "Error: Cannot modify admin status of users who are not mutual contacts. Please ensure the user is in your contacts and has added you back."
        except Exception as e:
            return log_and_format_error(
                "demote_admin", e, group_id=group_id, user_id=user_id
            )
    except Exception as e:
        logger.error(
            f"telegram_mcp demote_admin failed (group_id={group_id}, user_id={user_id})",
            exc_info=True,
        )
        return log_and_format_error(
            "demote_admin", e, group_id=group_id, user_id=user_id
        )

async def ban_user(client: TelegramClient, chat_id: int, user_id: int) -> str:
    """
    Ban a user from a group or channel.

    Args:
        chat_id: ID of the group/channel
        user_id: User ID to ban
    """
    try:
        chat = await client.get_entity(chat_id)
        user = await client.get_entity(user_id)
        banned_rights = ChatBannedRights(
            until_date=None,
            view_messages=True,
            send_messages=True,
            send_media=True,
            send_stickers=True,
            send_gifs=True,
            send_games=True,
            send_inline=True,
            embed_links=True,
            send_polls=True,
            change_info=True,
            invite_users=True,
            pin_messages=True,
        )
        try:
            await client(
                functions.channels.EditBannedRequest(
                    channel=chat, participant=user, banned_rights=banned_rights
                )
            )
            return f"User {user_id} banned from chat {chat.title} (ID: {chat_id})."
        except telethon.errors.rpcerrorlist.UserNotMutualContactError:
            return "Error: Cannot ban users who are not mutual contacts. Please ensure the user is in your contacts and has added you back."
        except Exception as e:
            return log_and_format_error(
                "ban_user", e, chat_id=chat_id, user_id=user_id
            )
    except Exception as e:
        logger.exception(
            f"ban_user failed (chat_id={chat_id}, user_id={user_id})"
        )
        return log_and_format_error(
            "ban_user", e, chat_id=chat_id, user_id=user_id
        )

async def unban_user(client: TelegramClient, chat_id: int, user_id: int) -> str:
    """
    Unban a user from a group or channel.

    Args:
        chat_id: ID of the group/channel
        user_id: User ID to unban
    """
    try:
        chat = await client.get_entity(chat_id)
        user = await client.get_entity(user_id)
        unbanned_rights = ChatBannedRights(
            until_date=None,
            view_messages=False,
            send_messages=False,
            send_media=False,
            send_stickers=False,
            send_gifs=False,
            send_games=False,
            send_inline=False,
            embed_links=False,
            send_polls=False,
            change_info=False,
            invite_users=False,
            pin_messages=False,
        )
        try:
            await client(
                functions.channels.EditBannedRequest(
                    channel=chat, participant=user, banned_rights=unbanned_rights
                )
            )
            return f"User {user_id} unbanned from chat {chat.title} (ID: {chat_id})."
        except telethon.errors.rpcerrorlist.UserNotMutualContactError:
            return "Error: Cannot modify status of users who are not mutual contacts. Please ensure the user is in your contacts and has added you back."
        except Exception as e:
            return log_and_format_error(
                "unban_user", e, chat_id=chat_id, user_id=user_id
            )
    except Exception as e:
        logger.exception(
            f"unban_user failed (chat_id={chat_id}, user_id={user_id})"
        )
        return log_and_format_error(
            "unban_user", e, chat_id=chat_id, user_id=user_id
        )

async def get_admins(client: TelegramClient, chat_id: int) -> str:
    """
    Get all admins in a group or channel.
    """
    try:
        participants = await client.get_participants(
            chat_id, filter=ChannelParticipantsAdmins()
        )
        lines = [
            f"ID: {p.id}, Name: {getattr(p, 'first_name', '')} {getattr(p, 'last_name', '')}".strip()
            for p in participants
        ]
        return "\n".join(lines) if lines else "No admins found."
    except Exception as e:
        logger.exception(f"get_admins failed (chat_id={chat_id})")
        return log_and_format_error("get_admins", e, chat_id=chat_id)

async def get_banned_users(client: TelegramClient, chat_id: int) -> str:
    """
    Get all banned users in a group or channel.
    """
    try:
        participants = await client.get_participants(
            chat_id, filter=ChannelParticipantsKicked(q="")
        )
        lines = [
            f"ID: {p.id}, Name: {getattr(p, 'first_name', '')} {getattr(p, 'last_name', '')}".strip()
            for p in participants
        ]
        return "\n".join(lines) if lines else "No banned users found."
    except Exception as e:
        logger.exception(f"get_banned_users failed (chat_id={chat_id})")
        return log_and_format_error("get_banned_users", e, chat_id=chat_id)

async def get_invite_link(client: TelegramClient, chat_id: int) -> str:
    """
    Get the invite link for a group or channel.
    """
    try:
        entity = await client.get_entity(chat_id)
        try:
            from telethon.tl import functions

            result = await client(
                functions.messages.ExportChatInviteRequest(peer=entity)
            )
            return result.link
        except AttributeError:
            logger.warning(
                "ExportChatInviteRequest not available, using alternative method"
            )
        except Exception as e1:
            logger.warning(f"ExportChatInviteRequest failed: {e1}")
        try:
            invite_link = await client.export_chat_invite_link(entity)
            return invite_link
        except Exception as e2:
            logger.warning(f"export_chat_invite_link failed: {e2}")
        try:
            if isinstance(entity, (Chat, Channel)):
                full_chat = await client(
                    functions.messages.GetFullChatRequest(chat_id=entity.id)
                )
                if hasattr(full_chat, "full_chat") and hasattr(
                    full_chat.full_chat, "invite_link"
                ):
                    return (
                        full_chat.full_chat.invite_link
                        or "No invite link available."
                    )
        except Exception as e3:
            logger.warning(f"GetFullChatRequest failed: {e3}")
        return "Could not retrieve invite link for this chat."
    except Exception as e:
        logger.exception(f"get_invite_link failed (chat_id={chat_id})")
        return log_and_format_error("get_invite_link", e, chat_id=chat_id)

async def join_chat_by_link(client: TelegramClient, link: str) -> str:
    """
    Join a chat by invite link.
    """
    try:
        if "/" in link:
            hash_part = link.split("/")[-1]
            if hash_part.startswith("+"):
                hash_part = hash_part[1:]
        else:
            hash_part = link
        try:
            from telethon.errors import (
                InviteHashExpiredError,
                InviteHashInvalidError,
                UserAlreadyParticipantError,
                ChatAdminRequiredError,
                UsersTooMuchError,
            )

            invite_info = await client(
                functions.messages.CheckChatInviteRequest(hash=hash_part)
            )
            if hasattr(invite_info, "chat") and invite_info.chat:
                chat_title = getattr(invite_info.chat, "title", "Unknown Chat")
                return f"You are already a member of this chat: {chat_title}"
        except Exception as check_err:
            pass
        try:
            result = await client(
                functions.messages.ImportChatInviteRequest(hash=hash_part)
            )
            if result and hasattr(result, "chats") and result.chats:
                chat_title = getattr(result.chats[0], "title", "Unknown Chat")
                return f"Successfully joined chat: {chat_title}"
            return f"Joined chat via invite hash."
        except Exception as join_err:
            err_str = str(join_err).lower()
            if "expired" in err_str:
                return "The invite hash has expired and is no longer valid."
            elif "invalid" in err_str:
                return "The invite hash is invalid or malformed."
            elif "already" in err_str and "participant" in err_str:
                return "You are already a member of this chat."
            elif "admin" in err_str:
                return "Cannot join this chat - requires admin approval."
            elif "too much" in err_str or "too many" in err_str:
                return "Cannot join this chat - it has reached maximum number of participants."
            else:
                raise
    except Exception as e:
        logger.exception(f"join_chat_by_link failed (link={link})")
        return log_and_format_error("join_chat_by_link", e, link=link)

async def export_chat_invite(client: TelegramClient, chat_id: int) -> str:
    """
    Export a chat invite link.
    """
    try:
        entity = await client.get_entity(chat_id)
        try:
            from telethon.tl import functions

            result = await client(
                functions.messages.ExportChatInviteRequest(peer=entity)
            )
            return result.link
        except AttributeError:
            logger.warning(
                "ExportChatInviteRequest not available, using alternative method"
            )
        except Exception as e1:
            logger.warning(f"ExportChatInviteRequest failed: {e1}")
        try:
            invite_link = await client.export_chat_invite_link(entity)
            return invite_link
        except Exception as e2:
            logger.warning(f"export_chat_invite_link failed: {e2}")
            return log_and_format_error("export_chat_invite", e2, chat_id=chat_id)
    except Exception as e:
        logger.exception(f"export_chat_invite failed (chat_id={chat_id})")
        return log_and_format_error("export_chat_invite", e, chat_id=chat_id)

async def import_chat_invite(client: TelegramClient, hash: str) -> str:
    """
    Import a chat invite by hash.
    """
    try:
        if hash.startswith("+"):
            hash = hash[1:]
        try:
            from telethon.errors import (
                InviteHashExpiredError,
                InviteHashInvalidError,
                UserAlreadyParticipantError,
                ChatAdminRequiredError,
                UsersTooMuchError,
            )

            invite_info = await client(
                functions.messages.CheckChatInviteRequest(hash=hash)
            )
            if hasattr(invite_info, "chat") and invite_info.chat:
                chat_title = getattr(invite_info.chat, "title", "Unknown Chat")
                return f"You are already a member of this chat: {chat_title}"
        except Exception as check_err:
            pass
        try:
            result = await client(
                functions.messages.ImportChatInviteRequest(hash=hash)
            )
            if result and hasattr(result, "chats") and result.chats:
                chat_title = getattr(result.chats[0], "title", "Unknown Chat")
                return f"Successfully joined chat: {chat_title}"
            return f"Joined chat via invite hash."
        except Exception as join_err:
            err_str = str(join_err).lower()
            if "expired" in err_str:
                return "The invite hash has expired and is no longer valid."
            elif "invalid" in err_str:
                return "The invite hash is invalid or malformed."
            elif "already" in err_str and "participant" in err_str:
                return "You are already a member of this chat."
            elif "admin" in err_str:
                return "Cannot join this chat - requires admin approval."
            elif "too much" in err_str or "too many" in err_str:
                return "Cannot join this chat - it has reached maximum number of participants."
            else:
                raise
    except Exception as e:
        logger.exception(f"import_chat_invite failed (hash={hash})")
        return log_and_format_error("import_chat_invite", e, hash=hash)

async def get_recent_actions(client: TelegramClient, chat_id: int) -> str:
    """
    Get recent admin actions (admin log) in a group or channel.
    """
    try:
        result = await client(
            functions.channels.GetAdminLogRequest(
                channel=chat_id,
                q="",
                events_filter=None,
                admins=[],
                max_id=0,
                min_id=0,
                limit=20,
            )
        )
        if not result or not result.events:
            return "No recent admin actions found."
        return json.dumps(
            [e.to_dict() for e in result.events],
            indent=2,
            default=json_serializer,
        )
    except Exception as e:
        logger.exception(f"get_recent_actions failed (chat_id={chat_id})")
        return log_and_format_error("get_recent_actions", e, chat_id=chat_id)

async def get_pinned_messages(client: TelegramClient, chat_id: int) -> str:
    """
    Get all pinned messages in a chat.
    """
    try:
        entity = await client.get_entity(chat_id)
        try:
            from telethon.tl.types import InputMessagesFilterPinned

            messages = await client.get_messages(
                entity, filter=InputMessagesFilterPinned()
            )
        except (ImportError, AttributeError):
            all_messages = await client.get_messages(entity, limit=50)
            messages = [m for m in all_messages if getattr(m, "pinned", False)]
        if not messages:
            return "No pinned messages found in this chat."
        return "\n".join(
            [
                f"ID: {m.id} | {m.date} | {m.message or '[Media/No text]'}"
                for m in messages
            ]
        )
    except Exception as e:
        logger.exception(f"get_pinned_messages failed (chat_id={chat_id})")
        return log_and_format_error("get_pinned_messages", e, chat_id=chat_id)

async def create_channel(
    client: TelegramClient, title: str, about: str = "", megagroup: bool = False
) -> str:
    """
    Create a new channel or supergroup.
    """
    try:
        result = await client(
            functions.channels.CreateChannelRequest(
                title=title, about=about, megagroup=megagroup
            )
        )
        return f"Channel '{title}' created with ID: {result.chats[0].id}"
    except Exception as e:
        return log_and_format_error(
            "create_channel", e, title=title, about=about, megagroup=megagroup
        )

async def edit_chat_title(client: TelegramClient, chat_id: int, title: str) -> str:
    """
    Edit the title of a chat, group, or channel.
    """
    try:
        entity = await client.get_entity(chat_id)
        if isinstance(entity, Channel):
            await client(
                functions.channels.EditTitleRequest(channel=entity, title=title)
            )
        elif isinstance(entity, Chat):
            await client(
                functions.messages.EditChatTitleRequest(chat_id=chat_id, title=title)
            )
        else:
            return f"Cannot edit title for this entity type ({type(entity)})."
        return f"Chat {chat_id} title updated to '{title}'."
    except Exception as e:
        logger.exception(
            f"edit_chat_title failed (chat_id={chat_id}, title='{title}')"
        )
        return log_and_format_error(
            "edit_chat_title", e, chat_id=chat_id, title=title
        )

async def edit_chat_photo(
    client: TelegramClient, chat_id: int, file_path: str
) -> str:
    """
    Edit the photo of a chat, group, or channel. Requires a file path to an image.
    """
    try:
        if not os.path.isfile(file_path):
            return f"Photo file not found: {file_path}"
        if not os.access(file_path, os.R_OK):
            return f"Photo file not readable: {file_path}"
        entity = await client.get_entity(chat_id)
        uploaded_file = await client.upload_file(file_path)
        if isinstance(entity, Channel):
            input_photo = InputChatUploadedPhoto(file=uploaded_file)
            await client(
                functions.channels.EditPhotoRequest(channel=entity, photo=input_photo)
            )
        elif isinstance(entity, Chat):
            input_photo = InputChatUploadedPhoto(file=uploaded_file)
            await client(
                functions.messages.EditChatPhotoRequest(
                    chat_id=chat_id, photo=input_photo
                )
            )
        else:
            return f"Cannot edit photo for this entity type ({type(entity)})."
        return f"Chat {chat_id} photo updated."
    except Exception as e:
        logger.exception(
            f"edit_chat_photo failed (chat_id={chat_id}, file_path='{file_path}')"
        )
        return log_and_format_error(
            "edit_chat_photo", e, chat_id=chat_id, file_path=file_path
        )

async def delete_chat_photo(client: TelegramClient, chat_id: int) -> str:
    """
    Delete the photo of a chat, group, or channel.
    """
    try:
        entity = await client.get_entity(chat_id)
        if isinstance(entity, Channel):
            await client(
                functions.channels.EditPhotoRequest(
                    channel=entity, photo=InputChatPhotoEmpty()
                )
            )
        elif isinstance(entity, Chat):
            await client(
                functions.messages.EditChatPhotoRequest(
                    chat_id=chat_id, photo=InputChatPhotoEmpty()
                )
            )
        else:
            return f"Cannot delete photo for this entity type ({type(entity)})."
        return f"Chat {chat_id} photo deleted."
    except Exception as e:
        logger.exception(f"delete_chat_photo failed (chat_id={chat_id})")
        return log_and_format_error("delete_chat_photo", e, chat_id=chat_id)
