from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, cast

from asyncpg import Record, create_pool

from utils.extra import ChatType

from .models import GlobalChat

if TYPE_CHECKING:
    from asyncpg import Pool

    from main import Sincroni

    from .types import GlobalChat as GlobalChatPayload


class CustomRecordClass(Record):
    def __getattr__(self, name: str) -> Any:
        if name in self.keys():
            return self[name]
        return super().__getattr__(name)

    def __dict__(self) -> dict[str, Any]:
        return dict(self)


class DatabaseConnection:
    _pool: Pool

    def __init__(self, bot: Sincroni, dsn: str) -> None:
        self.bot: Sincroni = bot
        self.__dsn: str = dsn

        # channel_id: GlobalChat
        self._global_chats: Dict[int, GlobalChat] = {}

    async def create_connection(self) -> None:
        self._pool = await create_pool(self.__dsn, record_class=CustomRecordClass)

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

    def get_global_chat(self, channel_id: int) -> Optional[GlobalChat]:
        return self._global_chats.get(channel_id)

    async def remove_global_chat(self, channel_id: int) -> Optional[GlobalChat]:
        await self.execute("DELETE FROM SICRONI_GLOBAL_CHAT WHERE channel_id = $1", channel_id)
        return self._global_chats.pop(channel_id, None)

    async def add_global_chat(
        self, server_id: int, channel_id: int, chat_type: ChatType = ChatType.public, webhook_url: Optional[str] = None
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
