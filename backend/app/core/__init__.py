"""Shared application core infrastructure."""

from app.core.auth import AccessTokenPayload, create_access_token
from app.core.cache import CacheInvalidationPlan, JsonCache, get_cache
from app.core.config import Settings, get_settings, settings
from app.core.database import Base, TimestampSoftDeleteMixin, get_db_session
from app.core.deps import get_current_user, get_optional_current_user
from app.core.errors import CommonErrorCode
from app.core.exceptions import BizException, register_exception_handlers
from app.core.http import ExternalHttpClient, ExternalResponse
from app.core.idempotency import IdempotencyService, get_idempotency_service
from app.core.locking import RedisLockManager, get_lock_manager
from app.core.metrics import metrics_registry
from app.core.repository import AsyncRepository
from app.core.responses import PageParams, PageResult, Result

__all__ = [
    "AccessTokenPayload",
    "Base",
    "BizException",
    "CacheInvalidationPlan",
    "CommonErrorCode",
    "ExternalHttpClient",
    "ExternalResponse",
    "AsyncRepository",
    "IdempotencyService",
    "JsonCache",
    "PageParams",
    "PageResult",
    "RedisLockManager",
    "Result",
    "Settings",
    "TimestampSoftDeleteMixin",
    "create_access_token",
    "get_cache",
    "get_current_user",
    "get_db_session",
    "get_idempotency_service",
    "get_lock_manager",
    "get_optional_current_user",
    "get_settings",
    "metrics_registry",
    "register_exception_handlers",
    "settings",
]
