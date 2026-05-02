"""Conversation module error codes."""

from enum import IntEnum


class ConversationErrorCode(IntEnum):
    """Conversation error codes."""

    CONVERSATION_NOT_FOUND = 7001
    AGENT_MODEL_NOT_CONFIGURED = 7002
    SSE_CONNECTION_ERROR = 7003
    EMPTY_MESSAGE_CONTENT = 7004
    CONVERSATION_CLOSED = 7005
