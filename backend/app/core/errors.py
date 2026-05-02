"""Common business error codes."""

from enum import IntEnum


class CommonErrorCode(IntEnum):
    """Common error codes shared across modules."""

    UNKNOWN_ERROR = 1000
    VALIDATION_ERROR = 1001
    RESOURCE_NOT_FOUND = 1002
    RESOURCE_ALREADY_EXISTS = 1003
    TOO_MANY_REQUESTS = 1004
