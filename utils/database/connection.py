from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

import asyncpg

from utils.extra import ChatType, FilterType

from .models import Blacklist, GlobalChat, LinkedChannel, Whitelist

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
        # id: Blacklist
        self._blacklists: Dict[int, Blacklist] = {}
        # id: Whitelist
        self._whitelists: Dict[int, Whitelist] = {}
        # id: LinkedChannels
        self._linked_channels: Dict[int, LinkedChannel] = {}

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
        entries = await self.fetch("SELECT * FROM SICRONI_GLOBAL_CHAT")

        row: GlobalChatPayload
        for row in entries:
            self._global_chats[row["channel_id"]] = GlobalChat(self, row)

        return self.global_chats

    async def fetch_global_chat(self, channel_id: int) -> Optional[GlobalChat]:
        res = await self.fetchrow("SELECT * FROM SICRONI_GLOBAL_CHAT WHERE channel_id = $1", channel_id)
        if res is None:
            return None

        self._global_chats[channel_id] = GlobalChat(self, res)
        return self._global_chats[channel_id]

    def get_global_chat(self, channel_id: int) -> Optional[GlobalChat]:
        return self._global_chats.get(channel_id)

    async def remove_global_chat(self, channel_id: int) -> Optional[GlobalChat]:
        await self.execute("DELETE FROM SICRONI_GLOBAL_CHAT WHERE channel_id = $1", channel_id)
        return self._global_chats.pop(channel_id, None)

    async def add_global_chat(
        self,
        server_id: int,
        channel_id: int,
        chat_type: ChatType = ChatType.public,
        webhook_url: Optional[str] = None,
    ) -> GlobalChat:
        query = "INSERT INTO SICRONI_GLOBAL_CHAT (server_id, channel_id, chat_type, webhook_url) VALUES ($1, $2, $3, $4) RETURNING *"
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
        entries = await self.fetch("SELECT * FROM SICRONI_BLACKLIST")

        row: Blacklist
        for row in entries:
            self._blacklists[row["id"]] = Blacklist(self, row)

        return self.blacklists

    async def fetch_blacklist(self, _id: int, /) -> Optional[Blacklist]:
        query = "SELECT * FROM SICRONI_BLACKLIST WHERE id = $1"
        ...

    def get_blacklist(self, _id: int) -> Optional[Blacklist]:
        ...

    async def remove_blacklist(self, _id: int, /) -> Optional[Blacklist]:
        query = "DELETE FROM SICRONI_BLACKLIST WHERE id = $1"
        ...

    async def add_blacklist(
        self,
        server_id: int,
        entity_id: int,
        pub: bool = False,
        dev: bool = False,
        private: bool = False,
        blacklist_type: FilterType = FilterType.user,
    ) -> Blacklist:
        query = """
            INSERT INTO SICRONI_BLACKLIST (
                server_id,
                entity_id,
                pub,
                dev,
                private,
                blacklist_type
            ) 
            VALUES ($1, $2, $3, $4, $5, $6) 
            RETURNING *
            """
        ...

    # Whitelist

    @property
    def whitelists(self) -> List[Whitelist]:
        return list(self._whitelists.values())

    async def fetch_whitelists(self) -> List[Whitelist]:
        entries = await self.fetch("SELECT * FROM SICRONI_WHITELIST")

        row: Whitelist
        for row in entries:
            self._whitelists[row["id"]] = Whitelist(self, row)

        return self.whitelists

    async def fetch_whitelist(self, _id: int, /) -> Optional[Whitelist]:
        query = "SELECT * FROM SICRONI_WHITELIST WHERE id = $1"
        ...

    def get_whitelist(self, _id: int, /) -> Optional[Whitelist]:
        ...

    async def remove_whitelist(self, _id: int, /) -> Optional[Whitelist]:
        query = "DELETE FROM SICRONI_WHITELIST WHERE id = $1"
        ...

    async def add_whitelist(
        self,
        entity_id: int,
        whitelist_type: FilterType = FilterType.user,
    ) -> Whitelist:
        query = """
            INSERT INTO SICRONI_WHITELIST (
                entity_id,
                whitelist_type
            ) 
            VALUES ($1, $2) 
            RETURNING *
            """
        ...

    # Linked Channels

    @property
    def linked_channels(self) -> List[LinkedChannel]:
        return list(self._linked_channels.values())

    async def fetch_linked_channels(self) -> List[LinkedChannel]:
        entries = await self.fetch("SELECT * FROM SICRONI_LINKED_CHANNELS")

        row: LinkedChannel
        for row in entries:
            self._linked_channels[row["id"]] = LinkedChannel(self, row)

        return self.linked_channels

    async def fetch_linked_channel(self, _id: int, /) -> Optional[LinkedChannel]:
        query = "SELECT * FROM SICRONI_LINKED_CHANNELS WHERE id = $1"
        ...

    def get_linked_channel(self, _id: int) -> Optional[LinkedChannel]:
        ...

    async def remove_linked_channel(self, _id: int, /) -> Optional[LinkedChannel]:
        query = "DELETE FROM SICRONI_LINKED_CHANNELS WHERE id = $1"
        ...

    async def add_linked_channel(
        self,
        origin_channel_id: int,
        destination_channel_id: int,
    ) -> LinkedChannel:
        query = """
            INSERT INTO SICRONI_LINKED_CHANNELS (
                origin_channel_id,
                destination_channel_id
            ) 
            VALUES ($1, $2) 
            RETURNING *
            """
        ...
