"""Tool module error codes."""

from enum import IntEnum


class ToolErrorCode(IntEnum):
    """Tool error codes."""

    TOOL_NOT_FOUND = 6001
    INVALID_OPENAPI_SCHEMA = 6002
    TOOL_EXECUTION_FAILED = 6003
    TOOL_EXECUTION_TIMEOUT = 6004
    TOOL_IN_USE = 6005
    INVALID_TOOL_CONFIGURATION = 6006
    TOOL_SECURITY_BLOCKED = 6007
