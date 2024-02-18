from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

import asyncpg

from utils.extra import ChatType, FilterType

from .models import Blacklist, EmbedColor, GlobalChat, LinkedChannel, Whitelist

if TYPE_CHECKING:
    from main import Sincroni

    from .types import GlobalChat as GlobalChatPayload


class CustomRecordClass(asyncpg.Record):
    def __getattr__(self, name: str) -> Any:
        if name in self.keys():
            return self[name]
        return super().__getattr__(name)

    def __dict__(self) -> dict[str, Any]:
        return dict(self)


class DatabaseConnection:
    _pool: asyncpg.Pool

    def __init__(self, bot: Sincroni, dsn: str) -> None:
        self.bot: Sincroni = bot
        self.__dsn: str = dsn

        # channel_id: GlobalChat
        self._global_chats: Dict[int, GlobalChat] = {}
        # (server_id, entity_id): Blacklist
        self._blacklists: Dict[tuple, Blacklist] = {}
        # entity_id: Whitelist
        self._whitelists: Dict[int, Whitelist] = {}
        # origin_channel_id: LinkedChannels
        self._linked_channels: Dict[int, LinkedChannel] = {}
        # (server_id, chat_type) : EmbedColor
        self._embed_colors: Dict[tuple, EmbedColor] = {}

    async def create_connection(self) -> None:
        self._pool = await asyncpg.create_pool(self.__dsn, record_class=CustomRecordClass)  # type: ignore

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
        self._pool = None  # type: ignore

    async def fetch(self, query: str, *args: Any) -> list[CustomRecordClass]:
        con = await self._pool.acquire()
        try:
            return await con.fetch(query, *args)
        finally:
            await self._pool.release(con)

    async def fetchrow(self, query: str, *args: Any) -> Optional[CustomRecordClass]:
        con = await self._pool.acquire()
        try:
            return await con.fetchrow(query, *args)
        finally:
            await self._pool.release(con)

    async def fetchval(self, query: str, *args: Any) -> Any:
        con = await self._pool.acquire()
        try:
            return await con.fetchval(query, *args)
        finally:
            await self._pool.release(con)

    async def execute(self, query: str, *args: Any) -> None:
        con = await self._pool.acquire()
        try:
            return await con.execute(query, *args)
        finally:
            await self._pool.release(con)

    async def executemany(self, query: str, *args: Any) -> None:
        con = await self._pool.acquire()
        try:
            return await con.executemany(query, *args)
        finally:
            await self._pool.release(con)

    # Global Chat

    @property
    def global_chats(self) -> List[GlobalChat]:
        return list(self._global_chats.values())

    async def fetch_global_chats(self) -> List[GlobalChat]:
        entries = await self.fetch("SELECT * FROM SINCRONI_GLOBAL_CHAT")

        row: GlobalChatPayload
        for row in entries:
            self._global_chats[row["channel_id"]] = GlobalChat(self, row)

        return self.global_chats

    async def fetch_global_chat(self, channel_id: int) -> Optional[GlobalChat]:
        res = await self.fetchrow("SELECT * FROM SINCRONI_GLOBAL_CHAT WHERE channel_id = $1", channel_id)
        if res is None:
            return None

        self._global_chats[channel_id] = GlobalChat(self, res)
        return self._global_chats[channel_id]

    def get_global_chat(self, channel_id: int) -> Optional[GlobalChat]:
        return self._global_chats.get(channel_id)

    async def remove_global_chat(self, channel_id: int) -> Optional[GlobalChat]:
        await self.execute("DELETE FROM SINCRONI_GLOBAL_CHAT WHERE channel_id = $1", channel_id)
        return self._global_chats.pop(channel_id, None)

    async def add_global_chat(
        self,
        server_id: int,
        channel_id: int,
        chat_type: ChatType = ChatType.public,
        webhook_url: Optional[str] = None,
    ) -> GlobalChat:
        query = "INSERT INTO SINCRONI_GLOBAL_CHAT (server_id, channel_id, chat_type, webhook_url) VALUES ($1, $2, $3, $4) RETURNING *"
        res = await self.fetchrow(
            query,
            server_id,
            channel_id,
            chat_type.value,
            webhook_url,
        )
        self._global_chats[channel_id] = GlobalChat(self, res)
        return self._global_chats[channel_id]

    # Blacklist

    @property
    def blacklists(self) -> List[Blacklist]:
        return list(self._blacklists.values())

    async def fetch_blacklists(self) -> List[Blacklist]:
        entries = await self.fetch("SELECT * FROM SINCRONI_BLACKLIST")

        row: Blacklist
        for row in entries:
            self._blacklists[(row["server_id"], row["entity_id"])] = Blacklist(self, row)

        return self.blacklists

    async def fetch_blacklist(self, server_id: int, entity_id: int, /) -> Optional[Blacklist]:
        query = "SELECT * FROM SINCRONI_BLACKLIST WHERE server_id = $1 AND entity_id = $2"

        res = await self.fetchrow(query, server_id, entity_id)
        if res is None:
            return None

        self._blacklists[(server_id, entity_id)] = Blacklist(self, res)
        return self._blacklists[(server_id, entity_id)]

    def get_blacklist(self, server_id: int, entity_id: int) -> Optional[Blacklist]:
        return self._blacklists.get((server_id, entity_id))

    async def remove_blacklist(self, server_id, entity_id: int, /) -> Optional[Blacklist]:
        query = "DELETE FROM SINCRONI_BLACKLIST WHERE server_id = $1 AND entity_id = $2"

        await self.execute(query, server_id, entity_id)

        return self._blacklists.pop((server_id, entity_id), None)

    async def add_blacklist(
        self,
        server_id: int,
        entity_id: int,
        pub: bool = False,
        dev: bool = False,
        private: bool = False,
        blacklist_type: FilterType = FilterType.user,
        reason: Optional[str] = None,
    ) -> Blacklist:
        query = """
            INSERT INTO SINCRONI_BLACKLIST (
                server_id,
                entity_id,
                pub,
                dev,
                private,
                blacklist_type,
                reason
            ) 
            VALUES ($1, $2, $3, $4, $5, $6, $7) 
            RETURNING *
            """

        res = await self.fetchrow(query, server_id, entity_id, pub, dev, private, blacklist_type, reason)

        self._blacklists[(server_id, entity_id)] = Blacklist(self, res)
        return self._blacklists[(server_id, entity_id)]

    # Whitelist

    @property
    def whitelists(self) -> List[Whitelist]:
        return list(self._whitelists.values())

    async def fetch_whitelists(self) -> List[Whitelist]:
        entries = await self.fetch("SELECT * FROM SINCRONI_WHITELIST")

        row: Whitelist
        for row in entries:
            self._whitelists[row["entity_id"]] = Whitelist(self, row)

        return self.whitelists

    async def fetch_whitelist(self, entity_id: int, /) -> Optional[Whitelist]:
        query = "SELECT * FROM SINCRONI_WHITELIST WHERE entity_id = $1"

        res = await self.fetchrow(query, entity_id)
        if res is None:
            return None

        self._whitelists[entity_id] = Whitelist(self, res)
        return self._whitelists[entity_id]

    def get_whitelist(self, entity_id: int, /) -> Optional[Whitelist]:
        return self._whitelists.get(entity_id)

    async def remove_whitelist(self, entity_id: int, /) -> Optional[Whitelist]:
        query = "DELETE FROM SINCRONI_WHITELIST WHERE entity_id = $1"

        await self.execute(query, entity_id)
        return self._whitelists.pop(entity_id, None)

    async def add_whitelist(
        self,
        entity_id: int,
        whitelist_type: FilterType = FilterType.user,
        reason: Optional[str] = None,
    ) -> Whitelist:
        query = """
            INSERT INTO SINCRONI_WHITELIST (
                entity_id,
                whitelist_type,
                reason
            ) 
            VALUES ($1, $2, $3) 
            RETURNING *
            """

        res = await self.fetchrow(
            query,
            entity_id,
            whitelist_type,
            reason,
        )

        self._whitelists[entity_id] = Whitelist(self, res)
        return self._whitelists[entity_id]

    # Linked Channels

    @property
    def linked_channels(self) -> List[LinkedChannel]:
        return list(self._linked_channels.values())

    async def fetch_linked_channels(self) -> List[LinkedChannel]:
        entries = await self.fetch("SELECT * FROM SINCRONI_LINKED_CHANNELS")

        row: LinkedChannel
        for row in entries:
            self._linked_channels[row["origin_channel_id"]] = LinkedChannel(self, row)

        return self.linked_channels

    async def fetch_linked_channel(self, origin_channel_id, /) -> Optional[LinkedChannel]:
        query = "SELECT * FROM SINCRONI_LINKED_CHANNELS WHERE origin_channel_id = $1"

        res = await self.fetchrow(query, origin_channel_id)
        if res is None:
            return None

        self._linked_channels[origin_channel_id] = LinkedChannel(self, res)
        return self._linked_channels[origin_channel_id]

    def get_linked_channel(self, origin_channel_id: int) -> Optional[LinkedChannel]:
        return self._linked_channels.get(origin_channel_id)

    async def remove_linked_channel(self, origin_channel_id: int, /) -> Optional[LinkedChannel]:
        query = "DELETE FROM SINCRONI_LINKED_CHANNELS WHERE origin_channel_id = $1"

        await self.execute(query, origin_channel_id)
        return self._linked_channels.pop(origin_channel_id, None)

    async def add_linked_channel(
        self,
        origin_channel_id: int,
        destination_channel_id: int,
    ) -> LinkedChannel:
        query = """
            INSERT INTO SINCRONI_LINKED_CHANNELS (
                origin_channel_id,
                destination_channel_id
            ) 
            VALUES ($1, $2) 
            RETURNING *
            """

        res = await self.fetchrow(
            query,
            origin_channel_id,
            destination_channel_id,
        )

        self._linked_channels[origin_channel_id] = LinkedChannel(self, res)
        return self._linked_channels[origin_channel_id]

    # Embed Colors

    @property
    def embed_colors(self) -> List[EmbedColor]:
        return list(self._embed_colors.values())

    async def fetch_embed_colors(self) -> List[EmbedColor]:
        entries = await self.fetch("SELECT * FROM SINCRONI_EMBED_COLOR")

        row: EmbedColor
        for row in entries:
            self._embed_colors[(row["server_id"], row["chat_type"])] = EmbedColor(self, row)

        return self.embed_colors

    async def fetch_embed_color(self, server_id: int, chat_type: ChatType = ChatType.public, /) -> Optional[EmbedColor]:
        query = "SELECT * FROM SINCRONI_EMBED_COLOR WHERE server_id = $1 AND chat_type = $2"

        res = await self.fetchrow(query, server_id, chat_type)
        if res is None:
            return None

        self._embed_colors[(server_id, chat_type)] = EmbedColor(self, res)
        return self._embed_colors[(server_id, chat_type)]

    def get_embed_color(self, server_id: int, chat_type: ChatType = ChatType.public) -> Optional[EmbedColor]:
        return self._embed_colors.get((server_id, chat_type))

    async def remove_embed_color(self, server_id, chat_type: ChatType = ChatType.public, /) -> Optional[EmbedColor]:
        query = "DELETE FROM SINCRONI_EMBED_COLOR WHERE server_id = $1 AND chat_type = $2"

        await self.execute(query, server_id, chat_type)

        return self._embed_colors.pop((server_id, chat_type), None)

    async def add_embed_color(
        self,
        server_id: int,
        chat_type: ChatType = ChatType.public,
        custom_color: int = 2067276,
    ) -> EmbedColor:
        query = """
            INSERT INTO SINCRONI_EMBED_COLOR (
                server_id,
                chat_type,
                custom_color
            ) 
            VALUES ($1, $2, $3) 
            RETURNING *
            """

        res = await self.fetchrow(query, server_id, chat_type, custom_color)

        self._embed_colors[(server_id, chat_type)] = EmbedColor(self, res)
        return self._embed_colors[(server_id, chat_type)]
