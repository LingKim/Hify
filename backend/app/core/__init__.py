"""Shared application core infrastructure."""

from app.core.config import Settings, get_settings, settings
from app.core.database import Base, TimestampSoftDeleteMixin, get_db_session
from app.core.errors import CommonErrorCode
from app.core.exceptions import BizException, register_exception_handlers
from app.core.responses import PageResult, Result

__all__ = [
    "Base",
    "BizException",
    "CommonErrorCode",
    "PageResult",
    "Result",
    "Settings",
    "TimestampSoftDeleteMixin",
    "get_db_session",
    "get_settings",
    "register_exception_handlers",
    "settings",
]
