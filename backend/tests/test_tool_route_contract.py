from __future__ import annotations

import httpx
import pytest

from app.auth.deps import get_current_active_user
from app.auth.model import User
from app.core.database import get_db_session
from app.main import app


@pytest.mark.asyncio
async def test_create_tool_route_exists() -> None:
    async def override_get_db_session():  # type: ignore[no-untyped-def]
        yield None

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_current_active_user] = lambda: User(
        id=1,
        username="member",
        email="member@hify.ai",
        password_hash="hash",
        role="member",
        is_active=True,
    )

    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/api/v1/tools",
            json={
                "name": "查询天气",
                "description": "按城市查询天气",
                "status": "enabled",
                "sourceType": "manual",
                "httpMethod": "GET",
                "url": "https://api.example.com/weather",
                "timeoutSeconds": 15,
                "headersTemplate": {"Accept": "application/json"},
                "queryTemplate": {"city": "{{city}}"},
                "bodyTemplate": None,
                "contentType": "application/json",
                "auth": {"authType": "none"},
                "parameters": [],
                "openapiSource": None,
                "metadata": None,
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code != 404
