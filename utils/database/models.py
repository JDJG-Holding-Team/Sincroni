from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Optional, Union

from discord import Guild, Thread, Webhook
from discord.abc import GuildChannel, PrivateChannel

from utils.extra import ChatType

if TYPE_CHECKING:
    from aiohttp import ClientSession

    from .connection import DatabaseConnection
    from .types import ChatType as ChatTypePayload
    from .types import GlobalChat as GlobalChatPayload


class GlobalChat:
    def __init__(self, connection: DatabaseConnection, data: GlobalChatPayload, /) -> None:
        self._connection: DatabaseConnection = connection

        self.server_id: int = data["server_id"]
        self.channel_id: int = data["channel_id"]
        self.raw_chat_type: ChatTypePayload = data["chat_type"]
        self.webhook_url: Optional[str] = data["webhook_url"]

        self._webhook: Optional[Webhook] = None

    @property
    def chat_type(self) -> ChatType:
        return ChatType(self.raw_chat_type)

    @staticmethod
    def __try_from_url(url: str, session: ClientSession) -> Optional[Webhook]:
        try:
            return Webhook.from_url(url, session=session)
        except Exception:
            return None

    @cached_property
    def webhook(self) -> Optional[Webhook]:
        if self.webhook_url is None:
            return None

        if not self._webhook:
            self._webhook = self.__try_from_url(self.webhook_url, self._connection.bot.session)

        return self._webhook

    @property
    def guild(self) -> Optional[Guild]:
        return self._connection.bot.get_guild(self.server_id)

    @property
    def channel(self) -> Optional[GuildChannel | PrivateChannel | Thread]:
        if self.guild:
            return self.guild.get_channel_or_thread(self.channel_id)

        return self._connection.bot.get_channel(self.channel_id)
