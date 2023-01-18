from __future__ import annotations

from typing import Literal, Optional, TypedDict

ChatType = Literal[0, 1, 2]


class GlobalChat(TypedDict):
    server_id: int  # BIGINT, NOT NULL, UNIQUE, PRIMARY KEY
    channel_id: int  # BIGINT, NOT NULL, UNIQUE
    webhook_url: Optional[str]  # TEXT, NULL
    chat_type: ChatType  # SMALLINT, DEFAULT 0, NOT NULL
