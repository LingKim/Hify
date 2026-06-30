from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.auth.model import User
from app.auth.password import hash_password
from app.core.auth import AccessTokenPayload, create_access_token
from app.core.database import Base, get_db_session
from app.core.http import ExternalResponse
from app.llm.executor import InvokeResult, LiteLLMExecutor
from app.llm.model import ProviderHealthStatus, ProviderInstance
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
class ProviderApiHarness:
    client: httpx.AsyncClient
    session_factory: async_sessionmaker[AsyncSession]
    http_state: dict[str, Any]
    invoke_state: dict[str, Any]
    headers: dict[str, str]


@pytest_asyncio.fixture
async def provider_api_harness(
    monkeypatch: pytest.MonkeyPatch,
) -> ProviderApiHarness:
    database_url = _database_url()
    schema_name = f"test_llm_provider_{uuid.uuid4().hex}"
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

    await _create_schema(admin_engine, schema_name)
    await _create_tables(test_engine)

    async with session_factory() as session:
        user = User(
            username="member",
            email="member@hify.ai",
            password_hash=hash_password("Member123!"),
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

    http_state: dict[str, Any] = {
        "response": ExternalResponse(
            ok=True,
            status_code=200,
            data={"data": []},
            error=None,
            headers={},
            attempt_count=1,
        ),
        "calls": [],
    }
    invoke_state: dict[str, Any] = {
        "result": InvokeResult(
            model_name="deepseek-chat",
            litellm_model="openai/deepseek-chat",
            output_text="pong",
            latency_ms=321,
        ),
        "error": None,
        "calls": [],
    }

    async def fake_request_json(
        self,  # noqa: ARG001
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> ExternalResponse:
        http_state["calls"].append(
            {
                "method": method,
                "url": url,
                "headers": headers,
                "params": params,
                "json_body": json_body,
            }
        )
        return http_state["response"]

    async def fake_invoke_text(
        self,  # noqa: ARG001
        runtime_config,  # type: ignore[no-untyped-def]
        *,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> InvokeResult:
        invoke_state["calls"].append(
            {
                "runtime_config": runtime_config,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )
        if invoke_state["error"] is not None:
            raise invoke_state["error"]
        return invoke_state["result"]

    monkeypatch.setattr(
        "app.core.http.ExternalHttpClient.request_json",
        fake_request_json,
    )
    monkeypatch.setattr(
        LiteLLMExecutor,
        "invoke_text",
        fake_invoke_text,
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers=headers,
    ) as client:
        yield ProviderApiHarness(
            client=client,
            session_factory=session_factory,
            http_state=http_state,
            invoke_state=invoke_state,
            headers=headers,
        )

    app.dependency_overrides.clear()
    await _drop_schema(admin_engine, schema_name)
    await test_engine.dispose()
    await admin_engine.dispose()


def _deepseek_payload(
    *,
    name: str = "DeepSeek 主实例",
    secret_value: str | None = "sk-deepseek-test-12345678",
) -> dict[str, Any]:
    return {
        "name": name,
        "providerType": "openai_compatible",
        "apiFamily": "openai_chat",
        "baseUrl": "https://api.deepseek.com/v1",
        "status": "active",
        "isDefault": True,
        "priority": 100,
        "notes": "DeepSeek production",
        "metadata": None,
        "auth": {
            "authType": "api_key",
            "secretValue": secret_value,
            "headers": None,
            "queryParams": None,
            "metadata": None,
            "expiresAt": None,
        },
        "models": [
            {
                "modelName": "deepseek-chat",
                "displayName": "DeepSeek Chat",
                "description": "Primary chat model",
                "status": "active",
                "isDefault": True,
                "sortOrder": 0,
                "supportsChat": True,
                "supportsStream": True,
                "supportsTools": False,
                "supportsStructuredOutput": False,
                "supportsVisionInput": False,
                "supportsAudioInput": False,
                "supportsReasoning": False,
                "supportsEmbeddings": False,
                "contextWindow": 64000,
                "maxOutputTokens": 8000,
                "maxInputTokens": 64000,
                "temperatureSupported": True,
                "topPSupported": True,
                "tags": None,
                "pricing": None,
                "metadata": None,
            },
            {
                "modelName": "deepseek-reasoner",
                "displayName": "DeepSeek Reasoner",
                "description": "Reasoning model",
                "status": "active",
                "isDefault": False,
                "sortOrder": 1,
                "supportsChat": True,
                "supportsStream": True,
                "supportsTools": False,
                "supportsStructuredOutput": False,
                "supportsVisionInput": False,
                "supportsAudioInput": False,
                "supportsReasoning": True,
                "supportsEmbeddings": False,
                "contextWindow": 64000,
                "maxOutputTokens": 8000,
                "maxInputTokens": 64000,
                "temperatureSupported": True,
                "topPSupported": True,
                "tags": None,
                "pricing": None,
                "metadata": None,
            },
        ],
    }


async def _create_provider(
    harness: ProviderApiHarness,
    *,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = await harness.client.post(
        "/api/v1/llms/providers",
        json=payload or _deepseek_payload(),
    )
    assert response.status_code == 201
    return response.json()["data"]


@pytest.mark.asyncio
async def test_create_provider_returns_deepseek_detail_payload(
    provider_api_harness: ProviderApiHarness,
) -> None:
    response = await provider_api_harness.client.post(
        "/api/v1/llms/providers",
        json=_deepseek_payload(),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["code"] == 201
    assert payload["data"]["providerType"] == "openai_compatible"
    assert payload["data"]["apiFamily"] == "openai_chat"
    assert payload["data"]["auth"]["secretMasked"] == "sk-d...5678"
    assert payload["data"]["defaultModel"]["modelName"] == "deepseek-chat"
    assert len(payload["data"]["models"]) == 2


@pytest.mark.asyncio
async def test_list_providers_matches_frontend_query_contract(
    provider_api_harness: ProviderApiHarness,
) -> None:
    await _create_provider(provider_api_harness)

    response = await provider_api_harness.client.get(
        "/api/v1/llms/providers",
        params={
            "page": 1,
            "pageSize": 20,
            "providerType": "openai_compatible",
            "status": "active",
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["total"] == 1
    assert payload["page"] == 1
    assert payload["pageSize"] == 20
    assert payload["list"][0]["name"] == "DeepSeek 主实例"
    assert payload["list"][0]["health"]["healthState"] == "unknown"


@pytest.mark.asyncio
async def test_get_provider_detail_returns_nested_models(
    provider_api_harness: ProviderApiHarness,
) -> None:
    created = await _create_provider(provider_api_harness)

    response = await provider_api_harness.client.get(
        f"/api/v1/llms/providers/{created['id']}"
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["id"] == created["id"]
    assert [item["modelName"] for item in payload["models"]] == [
        "deepseek-chat",
        "deepseek-reasoner",
    ]


@pytest.mark.asyncio
async def test_update_provider_preserves_secret_when_frontend_omits_it(
    provider_api_harness: ProviderApiHarness,
) -> None:
    created = await _create_provider(provider_api_harness)
    updated_payload = _deepseek_payload(
        name="DeepSeek 生产实例",
        secret_value=None,
    )
    updated_payload["priority"] = 120

    response = await provider_api_harness.client.put(
        f"/api/v1/llms/providers/{created['id']}",
        json=updated_payload,
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["name"] == "DeepSeek 生产实例"
    assert payload["priority"] == 120
    assert payload["auth"]["secretMasked"] == "sk-d...5678"


@pytest.mark.asyncio
async def test_get_runtime_config_resolves_openai_compatible_model(
    provider_api_harness: ProviderApiHarness,
) -> None:
    created = await _create_provider(provider_api_harness)

    response = await provider_api_harness.client.get(
        f"/api/v1/llms/providers/{created['id']}/runtime-config",
        params={"model_name": "deepseek-reasoner"},
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload == {
        "providerId": created["id"],
        "providerType": "openai_compatible",
        "apiFamily": "openai_chat",
        "modelName": "deepseek-reasoner",
        "litellmModel": "openai/deepseek-reasoner",
        "apiBase": "https://api.deepseek.com/v1",
        "apiKeyMasked": "sk-d...5678",
        "extraHeaders": {
            "Authorization": "Bearer sk-deepseek-test-12345678",
        },
        "queryParams": {},
    }


@pytest.mark.asyncio
async def test_test_connection_uses_models_endpoint_for_deepseek(
    provider_api_harness: ProviderApiHarness,
) -> None:
    created = await _create_provider(provider_api_harness)

    response = await provider_api_harness.client.post(
        f"/api/v1/llms/providers/{created['id']}/test-connection"
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["healthState"] == "healthy"
    assert payload["authState"] == "valid"
    assert provider_api_harness.http_state["calls"] == [
        {
            "method": "GET",
            "url": "https://api.deepseek.com/v1/models",
            "headers": {
                "Authorization": "Bearer sk-deepseek-test-12345678",
            },
            "params": {},
            "json_body": None,
        }
    ]


@pytest.mark.asyncio
async def test_invoke_provider_test_returns_executor_output(
    provider_api_harness: ProviderApiHarness,
) -> None:
    created = await _create_provider(provider_api_harness)

    response = await provider_api_harness.client.post(
        f"/api/v1/llms/providers/{created['id']}/invoke-test",
        json={
            "prompt": "Reply with pong",
            "modelName": "deepseek-reasoner",
            "temperature": 0.2,
            "maxTokens": 128,
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload == {
        "providerId": created["id"],
        "modelName": "deepseek-chat",
        "litellmModel": "openai/deepseek-chat",
        "outputText": "pong",
        "latencyMs": 321,
    }
    runtime_config = provider_api_harness.invoke_state["calls"][0][
        "runtime_config"
    ]
    assert runtime_config.model_name == "deepseek-reasoner"
    assert runtime_config.litellm_model == "openai/deepseek-reasoner"


@pytest.mark.asyncio
async def test_delete_provider_soft_deletes_record(
    provider_api_harness: ProviderApiHarness,
) -> None:
    created = await _create_provider(provider_api_harness)

    delete_response = await provider_api_harness.client.delete(
        f"/api/v1/llms/providers/{created['id']}"
    )
    detail_response = await provider_api_harness.client.get(
        f"/api/v1/llms/providers/{created['id']}"
    )
    list_response = await provider_api_harness.client.get(
        "/api/v1/llms/providers"
    )

    assert delete_response.status_code == 204
    assert detail_response.status_code == 404
    assert detail_response.json()["message"] == "模型提供商不存在"
    assert list_response.json()["data"]["total"] == 0


@pytest.mark.asyncio
async def test_connection_test_persists_health_snapshot(
    provider_api_harness: ProviderApiHarness,
) -> None:
    created = await _create_provider(provider_api_harness)

    await provider_api_harness.client.post(
        f"/api/v1/llms/providers/{created['id']}/test-connection"
    )

    async with provider_api_harness.session_factory() as session:
        provider = await session.get(ProviderInstance, created["id"])
        assert provider is not None
        status_row = await session.scalar(
            select(ProviderHealthStatus).where(
                ProviderHealthStatus.provider_instance_id == created["id"]
            )
        )
        assert status_row is not None
        assert status_row.health_state == "healthy"
        assert status_row.auth_state == "valid"
