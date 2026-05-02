"""Agent module error codes."""

from enum import IntEnum


class AgentErrorCode(IntEnum):
    """Agent error codes."""

    AGENT_NOT_FOUND = 4001
    INVALID_CONFIGURATION = 4002
    MODEL_NOT_FOUND = 4003
    KNOWLEDGE_BASE_NOT_FOUND = 4004
    TOOL_NOT_FOUND = 4005
