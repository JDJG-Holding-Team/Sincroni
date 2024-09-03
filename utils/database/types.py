from __future__ import annotations

from typing import Literal, Optional, TypedDict

ChatType = Literal[0, 1, 2, 3]
FilterType = Literal[0, 1]


class GlobalChat(TypedDict):
    server_id: int  # BIGINT, NOT NULL, UNIQUE, PRIMARY KEY
    channel_id: int  # BIGINT, NOT NULL, UNIQUE
    webhook_url: Optional[str]  # TEXT, NULL
    chat_type: ChatType  # SMALLINT, DEFAULT 0, NOT NULL


class Blacklist(TypedDict):
    id: int  # serial, NOT NULL
    server_id: int  # BIGINT, NOT NULL
    entity_id: int  # BIGINT, NOT NULL
    pub: bool  # BOOLEAN, DEFAULT FALSE
    dev: bool  # BOOLEAN, DEFAULT FALSE
    private: bool  # BOOLEAN, DEFAULT FALSE
    blacklist_type: FilterType  # SMALLINT, DEFAULT 0
    reason: str  # TEXT DEFAULT "No reason provided"
    repeat: bool  # BOOLEAN, DEFAULT FALSE


class Whitelist(TypedDict):
    id: int  # serial, NOT NULL
    entity_id: int  # BIGINT, NOT NULL
    whitelist_type: FilterType  # SMALLINT, DEFAULT 0
    reason: str  # TEXT DEFAULT "No reason provided"


class LinkedChannels(TypedDict):
    id: int  # serial, NOT NULL
    origin_channel_id: int  # BIGINT, NOT NULL
    origin_webhook_url: Optional[str]  # TEXT, NULL
    destination_channel_id: int  # BIGINT, NOT NULL
    destination_webhook_url: Optional[str]  # TEXT, NULL


class EmbedColors(TypedDict):
    server_id: int  # BIGINT, NOT NULL
    chat_type: ChatType  # SMALLINT, DEFAULT 0, NOT NULL
    custom_color: int  # INTEGER, NOT NULL


class GlobalChatConfig(TypedDict):
    server_id: int  # BIGINT, NOT NULL
    webhook_embed: bool  # BOOLEAN, DEFAULT TRUE
    censor_messages: bool  # BOOLEAN, DEFAULT FALSE
    censor_links: bool  # BOOLEAN, DEFAULT FALSE
    censor_invites: bool  # BOOLEAN, DEFAULT FALSE
    chat_type: ChatType  # SMALLINT, DEFAULT 0, NOT NULL
