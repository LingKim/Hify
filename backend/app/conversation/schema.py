"""Conversation module request and response schemas."""

from pydantic import BaseModel


class ConversationChatPreviewResp(BaseModel):
    """Response schema for the conversation preview endpoint."""

    module: str
    status: str
    capabilities: list[str]
