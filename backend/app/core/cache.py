"""Redis-backed JSON cache helpers."""

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from redis import asyncio as redis

from app.core.config import get_settings


class CacheKeyBuilder:
    """Build namespaced cache keys consistently."""

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix.strip(":")

    def build(self, namespace: str, *parts: object) -> str:
        """Join cache key segments into a normalized key."""
        segments = [self.prefix, namespace.strip(":")]
        segments.extend(str(part).strip(":") for part in parts)
        return ":".join(segment for segment in segments if segment)


class JsonCache:
    """JSON cache wrapper around an async Redis client."""

    def __init__(
        self,
        client: Any,
        *,
        prefix: str,
        default_ttl: int | None = None,
    ) -> None:
        self.client = client
        self.default_ttl = default_ttl
        self.key_builder = CacheKeyBuilder(prefix=prefix)

    def build_key(self, namespace: str, parts: tuple[object, ...]) -> str:
        """Build a cache key for the provided namespace and parts."""
        return self.key_builder.build(namespace, *parts)

    async def get_json(
        self,
        namespace: str,
        parts: tuple[object, ...],
    ) -> Any | None:
        """Load and deserialize a JSON cache value."""
        payload = await self.client.get(self.build_key(namespace, parts))
        if payload is None:
            return None
        return json.loads(payload)

    async def set_json(
        self,
        namespace: str,
        parts: tuple[object, ...],
        value: Any,
        *,
        ttl: int | None = None,
    ) -> bool:
        """Serialize and store a JSON cache value."""
        effective_ttl = ttl if ttl is not None else self.default_ttl
        return await self.client.set(
            self.build_key(namespace, parts),
            json.dumps(value, ensure_ascii=False),
            ex=effective_ttl,
        )

    async def delete(self, namespace: str, *parts: object) -> int:
        """Delete a cached JSON value by namespace and key parts."""
        key = self.key_builder.build(namespace, *parts)
        return await self.client.delete(key)

    async def refresh_json(
        self,
        namespace: str,
        parts: tuple[object, ...],
        loader: Callable[[], Awaitable[Any]],
        *,
        ttl: int | None = None,
    ) -> Any:
        """Rebuild a cached JSON value by calling the provided loader."""
        value = await loader()
        await self.set_json(namespace, parts, value, ttl=ttl)
        return value

    async def ping(self) -> bool:
        """Return whether the backing cache responds to ping."""
        return await self.client.ping()


class NullCache:
    """No-op cache used when Redis is disabled."""

    async def get_json(
        self,
        namespace: str,
        parts: tuple[object, ...],
    ) -> Any | None:
        del namespace, parts
        return None

    async def set_json(
        self,
        namespace: str,
        parts: tuple[object, ...],
        value: Any,
        *,
        ttl: int | None = None,
    ) -> bool:
        del namespace, parts, value, ttl
        return False

    async def delete(self, namespace: str, *parts: object) -> int:
        del namespace, parts
        return 0

    async def refresh_json(
        self,
        namespace: str,
        parts: tuple[object, ...],
        loader: Callable[[], Awaitable[Any]],
        *,
        ttl: int | None = None,
    ) -> Any:
        del namespace, parts, ttl
        return await loader()

    async def ping(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class CacheInvalidationPlan:
    """Describe cache keys that should be invalidated together."""

    namespace: str
    keys: list[tuple[object, ...]] = field(default_factory=list)

    async def apply(self, cache: JsonCache | NullCache) -> int:
        """Delete all keys described by the invalidation plan."""
        deleted = 0
        for parts in self.keys:
            deleted += await cache.delete(self.namespace, *parts)
        return deleted


@lru_cache
def get_redis_client() -> Any | None:
    """Create a cached Redis client when Redis support is enabled."""
    settings = get_settings()
    if not settings.redis_enabled or not settings.redis_url:
        return None
    return redis.from_url(settings.redis_url, decode_responses=True)


@lru_cache
def get_cache() -> JsonCache | NullCache:
    """Return the configured cache implementation."""
    settings = get_settings()
    client = get_redis_client()
    if client is None:
        return NullCache()
    return JsonCache(
        client,
        prefix=settings.redis_key_prefix,
        default_ttl=settings.redis_default_ttl_seconds,
    )
