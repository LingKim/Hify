"""RBAC module error codes."""

from enum import IntEnum


class RbacErrorCode(IntEnum):
    """RBAC error codes."""

    ROLE_NOT_FOUND = 8001
    PERMISSION_NOT_FOUND = 8002
    ROLE_CODE_EXISTS = 8003
    SYSTEM_ROLE_PROTECTED = 8004
    RBAC_SELF_LOCK_RISK = 8005
    ROLE_DISABLED = 8006
    EMPTY_ROLE_ASSIGNMENT = 8007
