"""Idempotency helpers for write endpoints."""

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from app.core.cache import JsonCache, NullCache, get_cache
from app.core.config import get_settings
from app.core.locking import (
    NullLockManager,
    RedisLockManager,
    get_lock_manager,
)

IDEMPOTENCY_NAMESPACE = "idempotency"


@dataclass(frozen=True, slots=True)
class IdempotencyResult:
    """Represents the state of an idempotent request."""

    status: str
    response_data: dict[str, Any] | None = None


class IdempotencyService:
    """Persist completed responses and reject in-flight duplicates."""

    def __init__(
        self,
        *,
        cache: JsonCache | NullCache,
        lock_manager: RedisLockManager | NullLockManager,
        ttl_seconds: int | None = None,
    ) -> None:
        settings = get_settings()
        self.cache = cache
        self.lock_manager = lock_manager
        self.ttl_seconds = ttl_seconds or settings.idempotency_ttl_seconds

    async def begin(self, request_key: str) -> IdempotencyResult:
        """Start an idempotent request or replay a stored response."""
        cached = await self.cache.get_json(
            IDEMPOTENCY_NAMESPACE,
            (request_key,),
        )
        if isinstance(cached, dict):
            return IdempotencyResult(
                status="replayed",
                response_data=cached,
            )

        lock = await self.lock_manager.acquire(
            f"idempotency:{request_key}",
            ttl=self.ttl_seconds,
        )
        if lock.acquired:
            return IdempotencyResult(status="started")
        return IdempotencyResult(status="conflict")

    async def complete(
        self,
        request_key: str,
        response_data: dict[str, Any],
    ) -> None:
        """Persist the successful response for replay."""
        await self.cache.set_json(
            IDEMPOTENCY_NAMESPACE,
            (request_key,),
            response_data,
            ttl=self.ttl_seconds,
        )
        lock = await self.lock_manager.acquire(
            f"idempotency:{request_key}",
            ttl=1,
        )
        await lock.release()


@lru_cache
def get_idempotency_service() -> IdempotencyService:
    """Return the configured idempotency service."""
    return IdempotencyService(
        cache=get_cache(),
        lock_manager=get_lock_manager(),
    )
