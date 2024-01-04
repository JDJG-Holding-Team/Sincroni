from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Optional, Union

import discord
from discord import Guild, TextChannel, Thread, Webhook
from discord.abc import GuildChannel, PrivateChannel

from utils.extra import ChatType, FilterType

if TYPE_CHECKING:
    from aiohttp import ClientSession

    from .connection import DatabaseConnection
    from .types import Blacklist as BlacklistPayload
    from .types import ChatType as ChatTypePayload
    from .types import FilterType as FilterTypePayload
    from .types import GlobalChat as GlobalChatPayload
    from .types import LinkedChannels as LinkedChannelsPayload
    from .types import Whitelist as WhitelistPayload
    from .types import EmbedColors as EmbedColorsPayload


class GlobalChat:
    """Represents a global chat channel.

    Parameters
    ----------
    connection : DatabaseConnection
        The database connection.
    data : GlobalChatPayload
        The data for the global chat.

    Attributes
    ----------
    server_id : int
        The ID of the server the channel is in.
    channel_id : int
        The ID of the channel.
    raw_chat_type : int
        The raw chat type.
    webhook_url : Optional[str]
        The webhook URL for the channel. ``None`` if there is no webhook.

    __int__ : int
        The channel's ID.
    __repr__ : str
        The representation of the global chat.
    """

    def __init__(self, connection: DatabaseConnection, data: GlobalChatPayload, /) -> None:
        self._connection: DatabaseConnection = connection

        self.server_id: int = data["server_id"]
        self.channel_id: int = data["channel_id"]
        self.raw_chat_type: ChatTypePayload = data["chat_type"]
        self.webhook_url: Optional[str] = data["webhook_url"]

        self._webhook: Optional[Webhook] = None

    def __repr__(self) -> str:
        return f"<GlobalChat server_id={self.server_id} channel_id={self.channel_id} chat_type={self.chat_type.name}>"

    def __int__(self) -> int:
        return self.channel_id

    @property
    def chat_type(self) -> ChatType:
        return ChatType(self.raw_chat_type)

    @cached_property
    def webhook(self) -> Optional[Webhook]:
        if self.webhook_url is None:
            return None

        if not self._webhook:
            self._webhook = self._connection.bot.get_webhook_from_url(self.webhook_url)

        return self._webhook

    @property
    def guild(self) -> Optional[Guild]:
        return self._connection.bot.get_guild(self.server_id)

    @property
    def channel(self) -> Optional[TextChannel | discord.DMChannel | Thread]:
        if self.guild:
            return self.guild.get_channel_or_thread(self.channel_id)  # type: ignore

        return self._connection.bot.get_channel(self.channel_id)  # type: ignore


class Blacklist:
    def __init__(self, connection: DatabaseConnection, data: BlacklistPayload, /) -> None:
        self._connection: DatabaseConnection = connection

        self.id: int = data["id"]
        self.server_id: int = data["server_id"]
        self.entity_id: int = data["entity_id"]
        self.pub: bool = data["pub"]
        self.dev: bool = data["dev"]
        self.private: bool = data["private"]
        self.raw_blacklist_type: FilterTypePayload = data["blacklist_type"]
        self.reason : str = data["reason"]

    def __repr__(self) -> str:
        return f"<Blacklist id={self.id} server_id={self.server_id} entity_id={self.entity_id} blacklist_type={self.blacklist_type.name}>"

    @property
    def blacklist_type(self) -> FilterType:
        return FilterType(self.raw_blacklist_type)

    @property
    def server(self) -> Optional[Guild]:
        """The server that is blacklisting the entity from discord.py cache."""
        return self._connection.bot.get_guild(self.server_id)

    @property
    def entity(self) -> Optional[Union[Guild, discord.Member, discord.User]]:
        """The entity that is blacklisted from discord.py cache."""
        if self.blacklist_type is FilterType.user:
            if self.server:
                return self.server.get_member(self.entity_id)
            return self._connection.bot.get_user(self.entity_id)
        elif self.blacklist_type is FilterType.server:
            return self._connection.bot.get_guild(self.entity_id)


    @property
    def _global(self) -> bool:
        """Whether or not the blacklist is enforced at a server or blacklist level."""
        return not bool(self.server_id)


class Whitelist:
    def __init__(self, connection: DatabaseConnection, data: WhitelistPayload, /) -> None:
        self._connection: DatabaseConnection = connection

        self.id: int = data["id"]
        self.entity_id: int = data["entity_id"]
        self.raw_whitelist_type: FilterTypePayload = data["whitelist_type"]
        self.reason : str = data["reason"]

    def __repr__(self) -> str:
        return f"<Whitelist id={self.id} entity_id={self.entity_id} whitelist_type={self.whitelist_type.name}>"

    @property
    def whitelist_type(self) -> FilterType:
        return FilterType(self.raw_whitelist_type)

    @property
    def entity(self) -> Optional[Union[Guild, discord.User]]:
        """The entity that is whitelisted from discord.py cache."""
        if self.whitelist_type is FilterType.user:
            return self._connection.bot.get_user(self.entity_id)
        elif self.whitelist_type is FilterType.server:
            return self._connection.bot.get_guild(self.entity_id)


class LinkedChannel:
    def __init__(self, connection: DatabaseConnection, data: LinkedChannelsPayload, /) -> None:
        self._connection: DatabaseConnection = connection

        self.id: int = data["id"]
        self.origin_channel_id: int = data["origin_channel_id"]
        self.destination_channel_id: int = data["destination_channel_id"]

    def __repr__(self) -> str:
        return f"<LinkedChannel id={self.id} origin_channel_id={self.origin_channel_id} destination_channel_id={self.destination_channel_id}>"

    @property
    def origin_channel(self) -> Optional[TextChannel | discord.DMChannel | Thread]:
        return self._connection.bot.get_channel(self.origin_channel_id)  # type: ignore

    @property
    def destination_channel(self) -> Optional[TextChannel | discord.DMChannel | Thread]:
        return self._connection.bot.get_channel(self.destination_channel_id)  # type: ignore


class EmbedColor:
    def __init__(self, connection: DatabaseConnection, data: EmbedColorsPayload, /) -> None:
        self._connection: DatabaseConnection = connection

        self.server_id : int = data["server_id"]
        self.raw_chat_type: ChatTypePayload = data["chat_type"]
        self.raw_custom_color : int = data["custom_color"]

    def __repr__(self) -> str:
        return f"<EmbedColor server_id={self.server_id} chat_type={self.raw_chat_type} custom_color={self.custom_color}>"

    @property
    def server(self) -> Optional[Guild]:
        """The server that is blacklisting the entity from discord.py cache."""
        return self._connection.bot.get_guild(self.server_id)

    @property
    def chat_type(self) -> ChatType:
        return ChatType(self.raw_chat_type)

    @property
    def custom_color(self) -> discord.Color:
        return discord.Color(self.raw_custom_color)