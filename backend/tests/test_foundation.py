import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, MockTransport, Request, Response

from app.auth.deps import get_current_active_user
from app.auth.model import User
from app.core.auth import (
    AccessTokenPayload,
    create_access_token,
    decode_access_token,
)
from app.core.cache import CacheKeyBuilder, JsonCache
from app.core.config import get_settings
from app.core.http import ExternalHttpClient
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
    ) -> bool:
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


def test_settings_reads_foundation_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_POOL_SIZE", "11")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/9")
    monkeypatch.setenv("JWT_SECRET_KEY", "secret-key")
    monkeypatch.setenv("HTTP_CLIENT_TIMEOUT_SECONDS", "12.5")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.database_pool_size == 11
    assert settings.redis_url == "redis://localhost:6379/9"
    assert settings.jwt_secret_key == "secret-key"
    assert settings.http_client_timeout_seconds == 12.5

    get_settings.cache_clear()


def test_health_response_includes_request_id_header() -> None:
    client = TestClient(app)

    response = client.get("/health", headers={"X-Request-ID": "req-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-123"


def test_auth_me_requires_bearer_token() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["message"] == "未登录或登录已过期"


def test_auth_me_returns_current_user_from_token() -> None:
    client = TestClient(app)
    token = create_access_token(
        AccessTokenPayload(
            sub="1",
            username="demo",
            role="admin",
        )
    )

    async def override_current_user() -> User:
        return User(
            id=1,
            username="demo",
            email="demo@hify.ai",
            password_hash="hashed",
            role="admin",
            is_active=True,
        )

    app.dependency_overrides[get_current_active_user] = override_current_user
    try:
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"] == {
        "id": 1,
        "username": "demo",
        "email": "demo@hify.ai",
        "role": "admin",
        "roleLabel": "管理员",
    }


def test_access_token_round_trip() -> None:
    token = create_access_token(
        AccessTokenPayload(
            sub="user-7",
            username="alice",
            role="member",
        )
    )

    payload = decode_access_token(token)

    assert payload.sub == "user-7"
    assert payload.username == "alice"
    assert payload.role == "member"


@pytest.mark.asyncio
async def test_http_client_retries_retryable_statuses() -> None:
    attempts = 0

    async def handler(request: Request) -> Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return Response(status_code=503, json={"error": "busy"})
        return Response(status_code=200, json={"ok": True})

    transport = MockTransport(handler)
    async with AsyncClient(transport=transport) as client:
        http_client = ExternalHttpClient(client=client, max_retries=2)

        response = await http_client.request_json(
            "GET",
            "https://example.com/health",
        )

    assert attempts == 2
    assert response.ok is True
    assert response.status_code == 200
    assert response.data == {"ok": True}


@pytest.mark.asyncio
async def test_json_cache_applies_namespace_and_ttl() -> None:
    fake_redis = FakeRedis()
    cache = JsonCache(fake_redis, prefix="hify-test")

    await cache.set_json("agents", ("agent", "1"), {"name": "demo"}, ttl=60)
    cached = await cache.get_json("agents", ("agent", "1"))

    assert cached == {"name": "demo"}
    assert fake_redis.expirations["hify-test:agents:agent:1"] == 60


def test_cache_key_builder_joins_segments() -> None:
    builder = CacheKeyBuilder(prefix="hify")

    key = builder.build("llm", "provider", 1)

    assert key == "hify:llm:provider:1"


def test_ready_returns_dependency_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_snapshot() -> dict[str, object]:
        return {
            "status": "ok",
            "checks": {
                "database": {"status": "ok"},
                "cache": {"status": "disabled"},
            },
        }

    monkeypatch.setattr("app.api.router.get_readiness_snapshot", fake_snapshot)
    client = TestClient(app)

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["data"] == {
        "status": "ok",
        "checks": {
            "database": {"status": "ok"},
            "cache": {"status": "disabled"},
        },
    }
