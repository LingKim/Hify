"""Auth module error codes."""

from enum import IntEnum


class AuthErrorCode(IntEnum):
    """Auth error codes."""

    INVALID_CREDENTIALS = 2001
    TOKEN_EXPIRED = 2002
    TOKEN_INVALID = 2003
    PERMISSION_DENIED = 2004
    ACCOUNT_DISABLED = 2005
