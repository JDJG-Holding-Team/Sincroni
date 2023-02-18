from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Optional, Union

import discord
from discord import Guild, TextChannel, Thread, Webhook
from discord.abc import GuildChannel, PrivateChannel

from utils.extra import ChatType

if TYPE_CHECKING:
    from aiohttp import ClientSession

    from .connection import DatabaseConnection
    from .types import ChatType as ChatTypePayload
    from .types import GlobalChat as GlobalChatPayload


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

    def __init__(
        self, connection: DatabaseConnection, data: GlobalChatPayload, /
    ) -> None:
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
