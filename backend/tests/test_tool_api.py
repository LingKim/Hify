from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.agent.model import Agent, AgentToolBinding
from app.auth.model import User
from app.auth.password import hash_password
from app.core.auth import AccessTokenPayload, create_access_token
from app.core.database import Base, get_db_session
from app.main import app


def _database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    env_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        ".env.development",
    )
    values: dict[str, str] = {}
    with open(env_path, encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values["DATABASE_URL"]


async def _create_schema(engine: AsyncEngine, schema_name: str) -> None:
    async with engine.begin() as connection:
        await connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))


async def _create_tables(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def _drop_schema(engine: AsyncEngine, schema_name: str) -> None:
    async with engine.begin() as connection:
        await connection.execute(text(f'DROP SCHEMA "{schema_name}" CASCADE'))


@dataclass
class ToolApiHarness:
    client: httpx.AsyncClient
    session_factory: async_sessionmaker[AsyncSession]
    user_id: int
    headers: dict[str, str]


@pytest_asyncio.fixture
async def tool_api_harness() -> ToolApiHarness:
    database_url = _database_url()
    schema_name = f"test_tool_{uuid.uuid4().hex}"
    admin_engine = create_async_engine(database_url)
    test_engine = create_async_engine(
        database_url,
        connect_args={
            "server_settings": {
                "search_path": schema_name,
            }
        },
    )
    session_factory = async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False,
        autoflush=False,
    )

    try:
        await _create_schema(admin_engine, schema_name)
    except (ConnectionRefusedError, OSError, SQLAlchemyError) as exc:
        await test_engine.dispose()
        await admin_engine.dispose()
        pytest.skip(f"PostgreSQL is not available for API test: {exc}")
    await _create_tables(test_engine)

    async with session_factory() as session:
        user = User(
            username="member",
            email="member@hify.ai",
            password_hash=hash_password("Member123!"),
            role="member",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        user_id = user.id

    token = create_access_token(
        AccessTokenPayload(
            sub=str(user_id),
            username="member",
            role="member",
        )
    )
    headers = {"Authorization": f"Bearer {token}"}

    async def override_get_db_session():  # type: ignore[no-untyped-def]
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers=headers,
    ) as client:
        yield ToolApiHarness(
            client=client,
            session_factory=session_factory,
            user_id=user_id,
            headers=headers,
        )

    app.dependency_overrides.clear()
    await _drop_schema(admin_engine, schema_name)
    await test_engine.dispose()
    await admin_engine.dispose()


def _tool_payload(
    *,
    name: str = "查询天气",
    secret_value: str | None = "sk-test-tool",
) -> dict[str, Any]:
    return {
        "name": name,
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
        "auth": {
            "authType": "api_key_header",
            "secretValue": secret_value,
            "headerName": "X-API-Key",
            "queryName": None,
        },
        "parameters": [
            {
                "name": "city",
                "label": "城市",
                "description": "要查询天气的城市名称",
                "paramLocation": "query",
                "schemaType": "string",
                "isRequired": True,
                "defaultValue": None,
                "enumValues": None,
                "schema": {"type": "string"},
                "sortOrder": 0,
                "metadata": None,
            }
        ],
        "openapiSource": None,
        "metadata": None,
    }


@pytest.mark.asyncio
async def test_tool_crud_execute_and_logs(
    tool_api_harness: ToolApiHarness,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_send = httpx.AsyncClient.send

    async def fake_send(self, request, **kwargs):  # type: ignore[no-untyped-def]
        if request.url.host == "testserver":
            return await original_send(self, request, **kwargs)
        del kwargs
        assert request.url == httpx.URL(
            "https://api.example.com/weather?city=%E6%9D%AD%E5%B7%9E"
        )
        assert request.headers["X-API-Key"] == "sk-test-tool"
        return httpx.Response(
            200,
            json={"city": "杭州", "weather": "晴"},
            request=request,
        )

    monkeypatch.setattr(httpx.AsyncClient, "send", fake_send)

    create_response = await tool_api_harness.client.post(
        "/api/v1/tools",
        json=_tool_payload(),
    )
    assert create_response.status_code == 201
    created = create_response.json()["data"]
    assert created["name"] == "查询天气"
    assert created["auth"]["secretMasked"] != "sk-test-tool"
    assert created["parameters"][0]["name"] == "city"

    tool_id = created["id"]
    list_response = await tool_api_harness.client.get("/api/v1/tools")
    options_response = await tool_api_harness.client.get(
        "/api/v1/tools/options"
    )
    detail_response = await tool_api_harness.client.get(
        f"/api/v1/tools/{tool_id}"
    )

    assert list_response.status_code == 200
    assert list_response.json()["data"]["total"] == 1
    assert list_response.json()["data"]["list"][0]["parameterCount"] == 1
    assert options_response.status_code == 200
    assert options_response.json()["data"][0]["id"] == tool_id
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["auth"]["secretMasked"] != (
        "sk-test-tool"
    )

    update_payload = _tool_payload(name="查询城市天气", secret_value=None)
    update_response = await tool_api_harness.client.put(
        f"/api/v1/tools/{tool_id}",
        json=update_payload,
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["name"] == "查询城市天气"

    execute_response = await tool_api_harness.client.post(
        f"/api/v1/tools/{tool_id}/execute-test",
        json={"parameters": {"city": "杭州"}, "timeoutSeconds": 10},
    )
    assert execute_response.status_code == 200
    executed = execute_response.json()["data"]
    assert executed["status"] == "success"
    assert executed["response"]["statusCode"] == 200
    assert "sk-test-tool" not in executed["request"]["headers"].values()

    logs_response = await tool_api_harness.client.get(
        f"/api/v1/tools/{tool_id}/execution-logs"
    )
    assert logs_response.status_code == 200
    assert logs_response.json()["data"]["total"] == 1

    delete_response = await tool_api_harness.client.delete(
        f"/api/v1/tools/{tool_id}"
    )
    missing_response = await tool_api_harness.client.get(
        f"/api/v1/tools/{tool_id}"
    )
    assert delete_response.status_code == 204
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_tool_auth_can_change_from_none_to_secret(
    tool_api_harness: ToolApiHarness,
) -> None:
    create_payload = _tool_payload(name="无鉴权工具", secret_value=None)
    create_payload["auth"] = {
        "authType": "none",
        "secretValue": None,
        "headerName": None,
        "queryName": None,
    }
    create_response = await tool_api_harness.client.post(
        "/api/v1/tools",
        json=create_payload,
    )
    assert create_response.status_code == 201

    update_payload = _tool_payload(name="无鉴权工具", secret_value="sk-new")
    update_response = await tool_api_harness.client.put(
        f"/api/v1/tools/{create_response.json()['data']['id']}",
        json=update_payload,
    )

    assert update_response.status_code == 200
    auth = update_response.json()["data"]["auth"]
    assert auth["authType"] == "api_key_header"
    assert auth["secretMasked"] != "sk-new"


@pytest.mark.asyncio
async def test_openapi_preview_returns_editable_tool_draft(
    tool_api_harness: ToolApiHarness,
) -> None:
    response = await tool_api_harness.client.post(
        "/api/v1/tools/import-openapi/preview",
        json={
            "document": {
                "openapi": "3.0.3",
                "info": {"title": "Weather API", "version": "1.0.0"},
                "servers": [{"url": "https://api.example.com"}],
                "paths": {
                    "/weather": {
                        "get": {
                            "operationId": "getWeather",
                            "summary": "查询天气",
                            "parameters": [
                                {
                                    "name": "city",
                                    "in": "query",
                                    "required": True,
                                    "schema": {"type": "string"},
                                }
                            ],
                        }
                    }
                },
            },
            "operation": {"path": "/weather", "method": "GET"},
            "serverUrl": "https://api.example.com",
        },
    )

    assert response.status_code == 200
    draft = response.json()["data"]["draft"]
    assert draft["sourceType"] == "openapi"
    assert draft["httpMethod"] == "GET"
    assert draft["url"] == "https://api.example.com/weather"
    assert draft["queryTemplate"] == {"city": "{{city}}"}
    assert draft["parameters"][0]["name"] == "city"


@pytest.mark.asyncio
async def test_delete_bound_tool_is_blocked(
    tool_api_harness: ToolApiHarness,
) -> None:
    create_response = await tool_api_harness.client.post(
        "/api/v1/tools",
        json=_tool_payload(name="查询订单"),
    )
    assert create_response.status_code == 201
    tool_id = create_response.json()["data"]["id"]

    async with tool_api_harness.session_factory() as session:
        agent = Agent(
            name="客服助手",
            status="draft",
            orchestration_mode="agent",
        )
        session.add(agent)
        await session.flush()
        session.add(
            AgentToolBinding(
                agent_id=agent.id,
                tool_id=tool_id,
                binding_name="查询订单",
                is_enabled=True,
                sort_order=0,
            )
        )
        await session.commit()

    delete_response = await tool_api_harness.client.delete(
        f"/api/v1/tools/{tool_id}"
    )

    assert delete_response.status_code == 400
    assert delete_response.json()["code"] == 6005
