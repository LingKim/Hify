from typing import cast

import pytest
from fastapi.testclient import TestClient

from app.core.cache import CacheInvalidationPlan, JsonCache
from app.core.idempotency import IdempotencyService
from app.core.locking import RedisLockManager
from app.core.metrics import metrics_registry
from app.llm.provider import ProviderConfig, ProviderRegistry
from app.main import app


class FakeRedis:
    def __init__(self) -> None:
        self.storage: dict[str, str] = {}
        self.expirations: dict[str, int | None] = {}

    async def get(self, key: str) -> str | None:
        return self.storage.get(key)

    async def set(
        self,
        key: str,
        value: str,
        ex: int | None = None,
        nx: bool = False,
    ) -> bool:
        if nx and key in self.storage:
            return False
        self.storage[key] = value
        self.expirations[key] = ex
        return True

    async def delete(self, *keys: str) -> int:
        deleted = 0
        for key in keys:
            if key in self.storage:
                del self.storage[key]
                self.expirations.pop(key, None)
                deleted += 1
        return deleted

    async def ping(self) -> bool:
        return True


def test_provider_config_masks_secret() -> None:
    config = ProviderConfig(
        provider="openai",
        model="gpt-4.1",
        api_key="sk-super-secret-value",
    )

    assert config.masked_api_key == "sk-s...alue"


def test_provider_registry_resolves_registered_adapter() -> None:
    registry = ProviderRegistry()
    adapter = object()

    registry.register("openai", adapter)

    assert registry.resolve("openai") is adapter


@pytest.mark.asyncio
async def test_cache_invalidation_plan_deletes_multiple_keys() -> None:
    redis = FakeRedis()
    cache = JsonCache(redis, prefix="hify-test")
    await cache.set_json("agents", ("1",), {"name": "a"})
    await cache.set_json("llms", ("2",), {"name": "b"})
    plan = CacheInvalidationPlan(
        namespace="agents",
        keys=[("1",), ("missing",)],
    )

    deleted = await plan.apply(cache)

    assert deleted == 1
    assert await cache.get_json("agents", ("1",)) is None


@pytest.mark.asyncio
async def test_cache_refresh_through_loader() -> None:
    redis = FakeRedis()
    cache = JsonCache(redis, prefix="hify-test", default_ttl=120)

    async def load_agent() -> dict[str, str]:
        return {"name": "agent-a"}

    value = await cache.refresh_json("agents", ("1",), load_agent)

    assert value == {"name": "agent-a"}
    assert redis.expirations["hify-test:agents:1"] == 120


@pytest.mark.asyncio
async def test_lock_manager_blocks_duplicate_acquire() -> None:
    redis = FakeRedis()
    lock_manager = RedisLockManager(redis, prefix="hify-lock")

    first = await lock_manager.acquire("knowledge-sync", ttl=30)
    second = await lock_manager.acquire("knowledge-sync", ttl=30)

    assert first.acquired is True
    assert second.acquired is False

    await first.release()

    third = await lock_manager.acquire("knowledge-sync", ttl=30)
    assert third.acquired is True


@pytest.mark.asyncio
async def test_idempotency_service_returns_cached_response_for_duplicate(
) -> None:
    redis = FakeRedis()
    cache = JsonCache(redis, prefix="hify-test", default_ttl=300)
    lock_manager = RedisLockManager(redis, prefix="hify-lock")
    service = IdempotencyService(cache=cache, lock_manager=lock_manager)

    first = await service.begin("req-1")
    assert first.status == "started"

    await service.complete("req-1", {"ok": True})

    second = await service.begin("req-1")
    assert second.status == "replayed"
    assert second.response_data == {"ok": True}


def test_metrics_and_trace_headers_are_exposed() -> None:
    before_snapshot = cast(
        dict[str, dict[str, int]],
        metrics_registry.snapshot(),
    )
    before = before_snapshot["counters"].get(
        "http.server.requests",
        0,
    )
    client = TestClient(app)

    response = client.get("/health")
    after_snapshot = cast(
        dict[str, dict[str, int]],
        metrics_registry.snapshot(),
    )
    after = after_snapshot["counters"].get(
        "http.server.requests",
        0,
    )

    assert response.status_code == 200
    assert "X-Trace-ID" in response.headers
    assert after == before + 1


def test_metrics_endpoint_returns_snapshot() -> None:
    client = TestClient(app)

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "counters" in response.json()["data"]
