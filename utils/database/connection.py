from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, cast

from asyncpg import Record, create_pool

from utils.extra import ChatType

from .models import GlobalChat

if TYPE_CHECKING:
    from asyncpg import Connection

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
    connection: Connection

    def __init__(self, bot: Sincroni, dsn: str) -> None:
        self.bot: Sincroni = bot
        self.__dsn: str = dsn

        # channel_id: GlobalChat
        self._global_chats: Dict[int, GlobalChat]

    async def create_connection(self) -> None:
        con = await create_pool(self.__dsn, record_class=CustomRecordClass)
        self.connection = con

    async def close(self) -> None:
        if self.connection and not self.connection.is_closed():
            await self.connection.close()
        self.connection = None  # type: ignore

    async def fetch(self, query: str, *args: Any) -> list[CustomRecordClass]:
        return await self.connection.fetch(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> Optional[CustomRecordClass]:
        return await self.connection.fetchrow(query, *args)

    async def fetchval(self, query: str, *args: Any) -> Any:
        return await self.connection.fetchval(query, *args)

    async def execute(self, query: str, *args: Any) -> None:
        await self.connection.execute(query, *args)

    async def executemany(self, query: str, *args: Any) -> None:
        await self.connection.executemany(query, *args)

    # Global Chat
    async def fetch_global_chats(self) -> List[GlobalChat]:
        entries = await self.fetch("SELECT * FROM SICRONI_GLOBAL_CHAT")

        for row in entries:
            row = cast(GlobalChatPayload, dict(row))
            self._global_chats[row["channel_id"]] = GlobalChat(self, data=row)

        return list(self._global_chats.values())

    def get_global_chat(self, channel_id: int) -> Optional[GlobalChat]:
        return self._global_chats.get(channel_id)

    async def remove_global_chat(self, channel_id: int) -> Optional[GlobalChat]:
        await self.execute("DELETE FROM SICRONI_GLOBAL_CHAT WHERE channel_id = $1", channel_id)
        return self._global_chats.pop(channel_id, None)

    async def add_global_chat(
        self, server_id: int, channel_id: int, chat_type: ChatType, webhook_url: Optional[str] = None
    ) -> GlobalChat:
        ...  # Insert into database
