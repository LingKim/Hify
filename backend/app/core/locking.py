"""Distributed lock helpers backed by Redis-style primitives."""

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from app.core.cache import get_redis_client
from app.core.config import get_settings


@dataclass(slots=True)
class LockHandle:
    """Represents the result of a lock acquisition attempt."""

    key: str
    client: Any | None
    token: str | None
    acquired: bool

    async def release(self) -> bool:
        """Release the lock if it was acquired."""
        if not self.acquired or self.client is None:
            return False
        deleted = await self.client.delete(self.key)
        return deleted > 0


class RedisLockManager:
    """Acquire best-effort distributed locks using Redis SET NX."""

    def __init__(self, client: Any, *, prefix: str) -> None:
        self.client = client
        self.prefix = prefix.strip(":")

    def build_key(self, resource: str) -> str:
        """Build a distributed lock key."""
        return f"{self.prefix}:{resource}"

    async def acquire(self, resource: str, *, ttl: int) -> LockHandle:
        """Attempt to acquire a lock for the given resource."""
        key = self.build_key(resource)
        acquired = await self.client.set(
            key,
            "locked",
            ex=ttl,
            nx=True,
        )
        return LockHandle(
            key=key,
            client=self.client,
            token="locked" if acquired else None,
            acquired=bool(acquired),
        )


class NullLockManager:
    """No-op lock manager for environments without Redis."""

    async def acquire(self, resource: str, *, ttl: int) -> LockHandle:
        del resource, ttl
        return LockHandle(
            key="",
            client=None,
            token=None,
            acquired=True,
        )


@lru_cache
def get_lock_manager() -> RedisLockManager | NullLockManager:
    """Return the configured lock manager implementation."""
    settings = get_settings()
    client = get_redis_client()
    if client is None:
        return NullLockManager()
    return RedisLockManager(
        client,
        prefix=settings.distributed_lock_prefix,
    )
