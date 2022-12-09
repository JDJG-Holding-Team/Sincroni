from typing import Literal, Optional, TypedDict

ChatType = Literal[1, 2, 3]


class _GlobalChatOptions(TypedDict):
    webhook_url: Optional[str]


class GlobalChat(_GlobalChatOptions):
    server_id: int
    channel_id: int
    chat_type: ChatType
