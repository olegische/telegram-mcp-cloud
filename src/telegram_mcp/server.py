import logging
from mcp.server.fastmcp import FastMCP, Context

# Import tool implementation functions
from .tools import (
    chat_management,
    messaging,
    contact_management,
    user_profile,
    media,
    search_discovery,
    stickers_gifs_bots,
    privacy_settings_misc,
)
from .config import ServiceConfig
from .dependencies import get_telegram_client

logger = logging.getLogger("telegram_mcp")


def build_server() -> FastMCP:
    """Build and configure the FastMCP server instance.

    Returns:
        A configured FastMCP instance.
    """
    logger.info("Initializing FastMCP server")
    config = ServiceConfig()

    if config.MCP_TRANSPORT == "stdio":
        return FastMCP("telegram")
    else:
        return FastMCP(
            "telegram",
            host=config.MCP_HOST,
            port=config.MCP_PORT,
        )


# Create the global server instance that will be used by decorators
mcp_server = build_server()


# --- Tool Definitions ---


@mcp_server.tool()
async def get_chats(
    context: Context, 
    page: int = 1, 
    page_size: int = 20
) -> str:
    """
    Get a paginated list of chats.

    Args:
        page: Page number (1-indexed).
        page_size: Number of chats per page.

    Returns:
        A string containing the list of chats with their IDs and titles.
    """
    async with get_telegram_client(context) as client:
        return await chat_management.get_chats(client, page, page_size)


@mcp_server.tool()
async def list_chats(
    context: Context,
    chat_type: str = None,
    limit: int = 20,
) -> str:
    """
    List available chats with metadata.

    Args:
        chat_type: Filter by chat type ('user', 'group', 'channel', or None for all).
        limit: Maximum number of chats to retrieve.

    Returns:
        A string containing the list of chats with their metadata.
    """
    async with get_telegram_client(context) as client:
        return await chat_management.list_chats(client, chat_type, limit)


@mcp_server.tool()
async def get_chat(
    chat_id: int, context: Context
) -> str:
    """
    Get detailed information about a specific chat.

    Args:
        chat_id: The ID of the chat.

    Returns:
        A string containing detailed information about the chat.
    """
    async with get_telegram_client(context) as client:
        return await chat_management.get_chat(client, chat_id)


@mcp_server.tool()
async def create_group(
    title: str, user_ids: list, context: Context
) -> str:
    """
    Create a new group or supergroup and add users.

    Args:
        title: Title for the new group.
        user_ids: List of user IDs to add to the group.

    Returns:
        A string confirming the group creation and its ID.
    """
    async with get_telegram_client(context) as client:
        return await chat_management.create_group(client, title, user_ids)


@mcp_server.tool()
async def create_channel(
    context: Context,
    title: str,
    about: str = "",
    megagroup: bool = False,
) -> str:
    """
    Create a new channel or supergroup.

    Args:
        title: Title for the new channel.
        about: Description for the new channel (optional).
        megagroup: Whether to create a supergroup (optional).

    Returns:
        A string confirming the channel creation and its ID.
    """
    async with get_telegram_client(context) as client:
        return await chat_management.create_channel(client, title, about, megagroup)


@mcp_server.tool()
async def edit_chat_title(
    chat_id: int, title: str, context: Context
) -> str:
    """
    Edit the title of a chat, group, or channel.

    Args:
        chat_id: The ID of the chat.
        title: The new title for the chat.

    Returns:
        A string confirming the title has been updated.
    """
    async with get_telegram_client(context) as client:
        return await chat_management.edit_chat_title(client, chat_id, title)


@mcp_server.tool()
async def delete_chat_photo(
    chat_id: int, context: Context
) -> str:
    """
    Delete the photo of a chat, group, or channel.

    Args:
        chat_id: The ID of the chat.

    Returns:
        A string confirming the photo has been deleted.
    """
    async with get_telegram_client(context) as client:
        return await chat_management.delete_chat_photo(client, chat_id)


@mcp_server.tool()
async def leave_chat(
    chat_id: int, context: Context
) -> str:
    """
    Leave a group or channel by chat ID.

    Args:
        chat_id: The chat ID to leave.

    Returns:
        A string confirming that you have left the chat.
    """
    async with get_telegram_client(context) as client:
        return await chat_management.leave_chat(client, chat_id)


@mcp_server.tool()
async def get_participants(
    chat_id: int, context: Context
) -> str:
    """
    List all participants in a group or channel.

    Args:
        chat_id: The group or channel ID.

    Returns:
        A string containing the list of participants with their IDs and names.
    """
    async with get_telegram_client(context) as client:
        return await chat_management.get_participants(client, chat_id)


@mcp_server.tool()
async def get_admins(
    chat_id: int, context: Context
) -> str:
    """
    Get all admins in a group or channel.

    Args:
        chat_id: The group or channel ID.

    Returns:
        A string containing the list of admins with their IDs and names.
    """
    async with get_telegram_client(context) as client:
        return await chat_management.get_admins(client, chat_id)


@mcp_server.tool()
async def get_banned_users(
    chat_id: int, context: Context
) -> str:
    """
    Get all banned users in a group or channel.

    Args:
        chat_id: The group or channel ID.

    Returns:
        A string containing the list of banned users with their IDs and names.
    """
    async with get_telegram_client(context) as client:
        return await chat_management.get_banned_users(client, chat_id)


@mcp_server.tool()
async def promote_admin(
    context: Context,
    group_id: int,
    user_id: int,
    rights: dict = None,
) -> str:
    """
    Promote a user to admin in a group/channel.

    Args:
        group_id: ID of the group/channel.
        user_id: User ID to promote.
        rights: Admin rights to give (optional).

    Returns:
        A string confirming the promotion of the user.
    """
    async with get_telegram_client(context) as client:
        return await chat_management.promote_admin(client, group_id, user_id, rights)


@mcp_server.tool()
async def demote_admin(
    group_id: int, user_id: int, context: Context
) -> str:
    """
    Demote a user from admin in a group/channel.

    Args:
        group_id: ID of the group/channel.
        user_id: User ID to demote.

    Returns:
        A string confirming the demotion of the user.
    """
    async with get_telegram_client(context) as client:
        return await chat_management.demote_admin(client, group_id, user_id)


@mcp_server.tool()
async def ban_user(
    chat_id: int, user_id: int, context: Context
) -> str:
    """
    Ban a user from a group or channel.

    Args:
        chat_id: ID of the group/channel.
        user_id: User ID to ban.

    Returns:
        A string confirming the user has been banned.
    """
    async with get_telegram_client(context) as client:
        return await chat_management.ban_user(client, chat_id, user_id)


@mcp_server.tool()
async def unban_user(
    chat_id: int, user_id: int, context: Context
) -> str:
    """
    Unban a user from a group or channel.

    Args:
        chat_id: ID of the group/channel.
        user_id: User ID to unban.

    Returns:
        A string confirming the user has been unbanned.
    """
    async with get_telegram_client(context) as client:
        return await chat_management.unban_user(client, chat_id, user_id)


@mcp_server.tool()
async def get_invite_link(
    chat_id: int, context: Context
) -> str:
    """
    Get the invite link for a group or channel.

    Args:
        chat_id: The group or channel ID.

    Returns:
        A string containing the invite link.
    """
    async with get_telegram_client(context) as client:
        return await chat_management.get_invite_link(client, chat_id)


@mcp_server.tool()
async def export_chat_invite(
    chat_id: int, context: Context
) -> str:
    """
    Export a chat invite link.

    Args:
        chat_id: The group or channel ID.

    Returns:
        A string containing the exported invite link.
    """
    async with get_telegram_client(context) as client:
        return await chat_management.export_chat_invite(client, chat_id)


@mcp_server.tool()
async def import_chat_invite(
    hash: str, context: Context
) -> str:
    """
    Import a chat invite by hash.

    Args:
        hash: The invite hash to join.

    Returns:
        A string confirming that you have joined the chat.
    """
    async with get_telegram_client(context) as client:
        return await chat_management.import_chat_invite(client, hash)


@mcp_server.tool()
async def join_chat_by_link(
    link: str, context: Context
) -> str:
    """
    Join a chat by invite link.

    Args:
        link: The invite link to join.

    Returns:
        A string confirming that you have joined the chat.
    """
    async with get_telegram_client(context) as client:
        return await chat_management.join_chat_by_link(client, link)


@mcp_server.tool()
async def get_messages(
    context: Context,
    chat_id: int,
    page: int = 1,
    page_size: int = 20,
) -> str:
    """
    Get paginated messages from a specific chat.

    Args:
        chat_id: The ID of the chat.
        page: Page number (1-indexed).
        page_size: Number of messages per page.

    Returns:
        A string containing the list of messages.
    """
    async with get_telegram_client(context) as client:
        return await messaging.get_messages(client, chat_id, page, page_size)


@mcp_server.tool()
async def list_messages(
    context: Context,
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

    Returns:
        A string containing the list of filtered messages.
    """
    async with get_telegram_client(context) as client:
        return await messaging.list_messages(
            client, chat_id, limit, search_query, from_date, to_date
        )


@mcp_server.tool()
async def send_message(
    chat_id: int, message: str, context: Context
) -> str:
    """
    Send a message to a specific chat.

    Args:
        chat_id: The ID of the chat.
        message: The message content to send.

    Returns:
        A string confirming the message was sent.
    """
    async with get_telegram_client(context) as client:
        return await messaging.send_message(client, chat_id, message)


@mcp_server.tool()
async def reply_to_message(
    chat_id: int,
    message_id: int,
    text: str,
    context: Context,
) -> str:
    """
    Reply to a specific message in a chat.

    Args:
        chat_id: The ID of the chat.
        message_id: The ID of the message to reply to.
        text: The reply text.

    Returns:
        A string confirming the reply was sent.
    """
    async with get_telegram_client(context) as client:
        return await messaging.reply_to_message(client, chat_id, message_id, text)


@mcp_server.tool()
async def edit_message(
    context: Context,
    chat_id: int,
    message_id: int,
    new_text: str,
) -> str:
    """
    Edit a message you sent.

    Args:
        chat_id: The ID of the chat.
        message_id: The ID of the message to edit.
        new_text: The new text for the message.

    Returns:
        A string confirming the message was edited.
    """
    async with get_telegram_client(context) as client:
        return await messaging.edit_message(client, chat_id, message_id, new_text)


@mcp_server.tool()
async def delete_message(
    context: Context,
    chat_id: int,
    message_id: int,
) -> str:
    """
    Delete a message by ID.

    Args:
        chat_id: The ID of the chat.
        message_id: The ID of the message to delete.

    Returns:
        A string confirming the message was deleted.
    """
    async with get_telegram_client(context) as client:
        return await messaging.delete_message(client, chat_id, message_id)


@mcp_server.tool()
async def forward_message(
    context: Context,
    from_chat_id: int,
    message_id: int,
    to_chat_id: int,
) -> str:
    """
    Forward a message from one chat to another.

    Args:
        from_chat_id: The source chat ID.
        message_id: The ID of the message to forward.
        to_chat_id: The destination chat ID.

    Returns:
        A string confirming the message was forwarded.
    """
    async with get_telegram_client(context) as client:
        return await messaging.forward_message(
            client, from_chat_id, message_id, to_chat_id
        )


@mcp_server.tool()
async def pin_message(
    context: Context,
    chat_id: int,
    message_id: int,
) -> str:
    """
    Pin a message in a chat.

    Args:
        chat_id: The ID of the chat.
        message_id: The ID of the message to pin.

    Returns:
        A string confirming the message was pinned.
    """
    async with get_telegram_client(context) as client:
        return await messaging.pin_message(client, chat_id, message_id)


@mcp_server.tool()
async def unpin_message(
    context: Context,
    chat_id: int,
    message_id: int,
) -> str:
    """
    Unpin a message in a chat.

    Args:
        chat_id: The ID of the chat.
        message_id: The ID of the message to unpin.

    Returns:
        A string confirming the message was unpinned.
    """
    async with get_telegram_client(context) as client:
        return await messaging.unpin_message(client, chat_id, message_id)


@mcp_server.tool()
async def mark_as_read(
    chat_id: int, context: Context
) -> str:
    """
    Mark all messages as read in a chat.

    Args:
        chat_id: The ID of the chat.

    Returns:
        A string confirming the chat was marked as read.
    """
    async with get_telegram_client(context) as client:
        return await messaging.mark_as_read(client, chat_id)


@mcp_server.tool()
async def get_message_context(
    context: Context,
    chat_id: int,
    message_id: int,
    context_size: int = 3,
) -> str:
    """
    Retrieve context around a specific message.

    Args:
        chat_id: The ID of the chat.
        message_id: The ID of the central message.
        context_size: Number of messages before and after to include.

    Returns:
        A string containing the message context.
    """
    async with get_telegram_client(context) as client:
        return await messaging.get_message_context(
            client, chat_id, message_id, context_size
        )


@mcp_server.tool()
async def get_history(
    context: Context,
    chat_id: int, 
    limit: int = 100, 
) -> str:
    """
    Get full chat history (up to limit).

    Args:
        chat_id: The ID of the chat.
        limit: Maximum number of messages to retrieve.

    Returns:
        A string containing the chat history.
    """
    async with get_telegram_client(context) as client:
        return await messaging.get_history(client, chat_id, limit)


@mcp_server.tool()
async def get_pinned_messages(
    chat_id: int, context: Context
) -> str:
    """
    Get all pinned messages in a chat.

    Args:
        chat_id: The ID of the chat.

    Returns:
        A string containing the list of pinned messages.
    """
    async with get_telegram_client(context) as client:
        return await chat_management.get_pinned_messages(client, chat_id)


@mcp_server.tool()
async def get_last_interaction(
    contact_id: int, context: Context
) -> str:
    """
    Get the most recent message with a contact.

    Args:
        contact_id: The ID of the contact.

    Returns:
        A string containing the last few messages with the contact.
    """
    async with get_telegram_client(context) as client:
        return await contact_management.get_last_interaction(client, contact_id)


@mcp_server.tool()
async def list_contacts(context: Context) -> str:
    """
    List all contacts in your Telegram account.

    Returns:
        A string containing the list of contacts.
    """
    async with get_telegram_client(context) as client:
        return await contact_management.list_contacts(client)


@mcp_server.tool()
async def search_contacts(
    query: str, context: Context
) -> str:
    """
    Search for contacts by name, username, or phone number.

    Args:
        query: The search term.

    Returns:
        A string containing the list of matching contacts.
    """
    async with get_telegram_client(context) as client:
        return await contact_management.search_contacts(client, query)


@mcp_server.tool()
async def add_contact(
    context: Context,
    phone: str,
    first_name: str,
    last_name: str = "",
) -> str:
    """
    Add a new contact to your Telegram account.

    Args:
        phone: The phone number of the contact (with country code).
        first_name: The contact's first name.
        last_name: The contact's last name (optional).

    Returns:
        A string confirming the contact was added.
    """
    async with get_telegram_client(context) as client:
        return await contact_management.add_contact(client, phone, first_name, last_name)


@mcp_server.tool()
async def delete_contact(
    user_id: int, context: Context
) -> str:
    """
    Delete a contact by user ID.

    Args:
        user_id: The Telegram user ID of the contact to delete.

    Returns:
        A string confirming the contact was deleted.
    """
    async with get_telegram_client(context) as client:
        return await contact_management.delete_contact(client, user_id)


@mcp_server.tool()
async def block_user(
    user_id: int, context: Context
) -> str:
    """
    Block a user by user ID.

    Args:
        user_id: The Telegram user ID to block.

    Returns:
        A string confirming the user was blocked.
    """
    async with get_telegram_client(context) as client:
        return await contact_management.block_user(client, user_id)


@mcp_server.tool()
async def unblock_user(
    user_id: int, context: Context
) -> str:
    """
    Unblock a user by user ID.

    Args:
        user_id: The Telegram user ID to unblock.

    Returns:
        A string confirming the user was unblocked.
    """
    async with get_telegram_client(context) as client:
        return await contact_management.unblock_user(client, user_id)


@mcp_server.tool()
async def import_contacts(
    contacts: list, context: Context
) -> str:
    """
    Import a list of contacts. Each contact should be a dict with phone, first_name, last_name.

    Args:
        contacts: A list of contact dictionaries.

    Returns:
        A string confirming how many contacts were imported.
    """
    async with get_telegram_client(context) as client:
        return await contact_management.import_contacts(client, contacts)


@mcp_server.tool()
async def export_contacts(context: Context) -> str:
    """
    Export all contacts as a JSON string.

    Returns:
        A JSON string of all contacts.
    """
    async with get_telegram_client(context) as client:
        return await contact_management.export_contacts(client)


@mcp_server.tool()
async def get_blocked_users(
    context: Context,
) -> str:
    """
    Get a list of blocked users.

    Returns:
        A JSON string of all blocked users.
    """
    async with get_telegram_client(context) as client:
        return await contact_management.get_blocked_users(client)


@mcp_server.tool()
async def get_contact_ids(context: Context) -> str:
    """
    Get all contact IDs in your Telegram account.

    Returns:
        A string containing a comma-separated list of contact IDs.
    """
    async with get_telegram_client(context) as client:
        return await contact_management.get_contact_ids(client)


@mcp_server.tool()
async def get_direct_chat_by_contact(
    contact_query: str, context: Context
) -> str:
    """
    Find a direct chat with a specific contact by name, username, or phone.

    Args:
        contact_query: Name, username, or phone number to search for.

    Returns:
        A string containing information about the direct chat if found.
    """
    async with get_telegram_client(context) as client:
        return await contact_management.get_direct_chat_by_contact(client, contact_query)


@mcp_server.tool()
async def get_contact_chats(
    contact_id: int, context: Context
) -> str:
    """
    List all chats involving a specific contact.

    Args:
        contact_id: The ID of the contact.

    Returns:
        A string listing all chats involving the contact.
    """
    async with get_telegram_client(context) as client:
        return await contact_management.get_contact_chats(client, contact_id)


@mcp_server.tool()
async def get_me(context: Context) -> str:
    """
    Get your own user information.

    Returns:
        A JSON string with your user information.
    """
    async with get_telegram_client(context) as client:
        return await user_profile.get_me(client)


@mcp_server.tool()
async def update_profile(
    context: Context,
    first_name: str = None,
    last_name: str = None,
    about: str = None,
) -> str:
    """
    Update your profile information (name, bio).

    Args:
        first_name: Your new first name (optional).
        last_name: Your new last name (optional).
        about: Your new bio/about text (optional).

    Returns:
        A string confirming the profile was updated.
    """
    async with get_telegram_client(context) as client:
        return await user_profile.update_profile(client, first_name, last_name, about)


@mcp_server.tool()
async def delete_profile_photo(
    context: Context,
) -> str:
    """
    Delete your current profile photo.

    Returns:
        A string confirming the photo was deleted.
    """
    async with get_telegram_client(context) as client:
        return await user_profile.delete_profile_photo(client)


@mcp_server.tool()
async def get_user_photos(
    context: Context,
    user_id: int, 
    limit: int = 10, 
) -> str:
    """
    Get a user's profile photos.

    Args:
        user_id: The ID of the user.
        limit: The maximum number of photos to retrieve.

    Returns:
        A JSON string containing a list of photo IDs.
    """
    async with get_telegram_client(context) as client:
        return await user_profile.get_user_photos(client, user_id, limit)


@mcp_server.tool()
async def get_user_status(
    user_id: int, context: Context
) -> str:
    """
    Get a user's online status.

    Args:
        user_id: The ID of the user.

    Returns:
        A string describing the user's status.
    """
    async with get_telegram_client(context) as client:
        return await user_profile.get_user_status(client, user_id)


@mcp_server.tool()
async def get_media_info(
    context: Context,
    chat_id: int,
    message_id: int,
) -> str:
    """
    Get info about media in a message.

    Args:
        chat_id: The chat ID.
        message_id: The message ID.

    Returns:
        A string representation of the media object.
    """
    async with get_telegram_client(context) as client:
        return await media.get_media_info(client, chat_id, message_id)


@mcp_server.tool()
async def search_public_chats(
    query: str, context: Context
) -> str:
    """
    Search for public chats, channels, or bots by username or title.

    Args:
        query: The search term.

    Returns:
        A JSON string of matching chats/users.
    """
    async with get_telegram_client(context) as client:
        return await search_discovery.search_public_chats(client, query)


@mcp_server.tool()
async def search_messages(
    context: Context,
    chat_id: int,
    query: str,
    limit: int = 20,
) -> str:
    """
    Search for messages in a chat by text.

    Args:
        chat_id: The ID of the chat.
        query: The text to search for.
        limit: The maximum number of messages to return.

    Returns:
        A string containing the matching messages.
    """
    async with get_telegram_client(context) as client:
        return await search_discovery.search_messages(client, chat_id, query, limit)


@mcp_server.tool()
async def resolve_username(
    username: str, context: Context
) -> str:
    """
    Resolve a username to a user or chat ID.

    Args:
        username: The username to resolve (without @).

    Returns:
        A string containing information about the resolved entity.
    """
    async with get_telegram_client(context) as client:
        return await search_discovery.resolve_username(client, username)


@mcp_server.tool()
async def get_sticker_sets(
    context: Context,
) -> str:
    """
    Get all your sticker sets.

    Returns:
        A JSON string containing a list of your sticker set titles.
    """
    async with get_telegram_client(context) as client:
        return await stickers_gifs_bots.get_sticker_sets(client)


@mcp_server.tool()
async def get_bot_info(
    bot_username: str, context: Context
) -> str:
    """
    Get information about a bot by username.

    Args:
        bot_username: The username of the bot (without @).

    Returns:
        A JSON string with detailed information about the bot.
    """
    async with get_telegram_client(context) as client:
        return await stickers_gifs_bots.get_bot_info(client, bot_username)


@mcp_server.tool()
async def set_bot_commands(
    context: Context,
    bot_username: str,
    commands: list,
) -> str:
    """
    Set bot commands for a bot you own (bot accounts only).

    Args:
        bot_username: The username of the bot.
        commands: List of command dictionaries with 'command' and 'description' keys.

    Returns:
        A string confirming the commands were set.
    """
    async with get_telegram_client(context) as client:
        return await stickers_gifs_bots.set_bot_commands(client, bot_username, commands)


@mcp_server.tool()
async def get_privacy_settings(
    context: Context,
) -> str:
    """
    Get your privacy settings for last seen status.

    Returns:
        A string representation of your privacy settings.
    """
    async with get_telegram_client(context) as client:
        return await privacy_settings_misc.get_privacy_settings(client)


@mcp_server.tool()
async def set_privacy_settings(
    context: Context,
    key: str,
    allow_users: list = None,
    disallow_users: list = None,
) -> str:
    """
    Set privacy settings (e.g., last seen, phone, etc.).

    Args:
        key: The privacy setting to modify ('status', 'phone', 'profile_photo').
        allow_users: List of user IDs to allow (optional).
        disallow_users: List of user IDs to disallow (optional).

    Returns:
        A string confirming the settings were updated.
    """
    async with get_telegram_client(context) as client:
        return await privacy_settings_misc.set_privacy_settings(
            client, key, allow_users, disallow_users
        )


@mcp_server.tool()
async def mute_chat(
    chat_id: int, context: Context
) -> str:
    """
    Mute notifications for a chat.

    Args:
        chat_id: The ID of the chat to mute.

    Returns:
        A string confirming the chat was muted.
    """
    async with get_telegram_client(context) as client:
        return await privacy_settings_misc.mute_chat(client, chat_id)


@mcp_server.tool()
async def unmute_chat(
    chat_id: int, context: Context
) -> str:
    """
    Unmute notifications for a chat.

    Args:
        chat_id: The ID of the chat to unmute.

    Returns:
        A string confirming the chat was unmuted.
    """
    async with get_telegram_client(context) as client:
        return await privacy_settings_misc.unmute_chat(client, chat_id)


@mcp_server.tool()
async def archive_chat(
    chat_id: int, context: Context
) -> str:
    """
    Archive a chat.

    Args:
        chat_id: The ID of the chat to archive.

    Returns:
        A string confirming the chat was archived.
    """
    async with get_telegram_client(context) as client:
        return await privacy_settings_misc.archive_chat(client, chat_id)


@mcp_server.tool()
async def unarchive_chat(
    chat_id: int, context: Context
) -> str:
    """
    Unarchive a chat.

    Args:
        chat_id: The ID of the chat to unarchive.

    Returns:
        A string confirming the chat was unarchived.
    """
    async with get_telegram_client(context) as client:
        return await privacy_settings_misc.unarchive_chat(client, chat_id)
