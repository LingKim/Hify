from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
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
from app.llm.model import ProviderInstance, ProviderModel
from app.main import app
from app.tool.model import Tool


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
class AgentApiHarness:
    client: httpx.AsyncClient
    session_factory: async_sessionmaker[AsyncSession]
    provider_instance_id: int
    provider_model_id: int
    tool_id: int
    headers: dict[str, str]


@pytest_asyncio.fixture
async def agent_api_harness() -> AgentApiHarness:
    database_url = _database_url()
    schema_name = f"test_agent_config_{uuid.uuid4().hex}"
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
            role="member",
            is_active=True,
        )
        session.add(user)
        await session.flush()
        provider = ProviderInstance(
            name="OpenAI-测试",
            provider_type="openai",
            api_family="openai_responses",
            base_url="https://api.openai.com/v1",
            status="active",
            is_default=True,
            priority=100,
        )
        session.add(provider)
        await session.flush()
        model = ProviderModel(
            provider_instance_id=provider.id,
            model_name="gpt-4.1-mini",
            display_name="GPT-4.1 Mini",
            status="active",
            is_default=True,
            sort_order=0,
        )
        session.add(model)
        await session.flush()
        tool = Tool(
            owner_user_id=user.id,
            name="查询订单",
            description="按订单号查询订单",
            status="enabled",
            tool_type="http",
            source_type="manual",
            http_method="GET",
            url="https://api.example.com/orders",
            timeout_seconds=15,
        )
        session.add(tool)
        await session.commit()
        provider_instance_id = provider.id
        provider_model_id = model.id
        tool_id = tool.id
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
        yield AgentApiHarness(
            client=client,
            session_factory=session_factory,
            provider_instance_id=provider_instance_id,
            provider_model_id=provider_model_id,
            tool_id=tool_id,
            headers=headers,
        )

    app.dependency_overrides.clear()
    await _drop_schema(admin_engine, schema_name)
    await test_engine.dispose()
    await admin_engine.dispose()


def _agent_payload(
    harness: AgentApiHarness,
    *,
    name: str = "客服助手",
    status: str = "draft",
    orchestration_mode: str = "agent",
) -> dict[str, Any]:
    return {
        "name": name,
        "description": "回答售前与售后常见问题",
        "avatarUrl": None,
        "status": status,
        "orchestrationMode": orchestration_mode,
        "providerInstanceId": harness.provider_instance_id,
        "providerModelId": harness.provider_model_id,
        "systemPrompt": None,
        "openingMessage": "你好，我可以帮你查询产品和订单问题。",
        "modelConfig": {
            "temperature": 0.7,
            "topP": 1,
            "maxTokens": 2048,
        },
        "runtimeConfig": {
            "stream": True,
            "maxIterations": 5,
            "memoryWindow": 10,
        },
        "workflowRef": (
            {"workflowDraftKey": "draft-only"}
            if orchestration_mode == "workflow"
            else None
        ),
        "tools": [
            {
                "toolId": harness.tool_id,
                "bindingName": "查询订单",
                "isEnabled": True,
                "sortOrder": 0,
                "config": {"timeoutSeconds": 20},
                "metadata": None,
            }
        ],
        "knowledgeBases": [
            {
                "knowledgeBaseId": 20,
                "isEnabled": True,
                "sortOrder": 0,
                "retrievalConfig": {
                    "topK": 5,
                    "scoreThreshold": 0.5,
                    "rerankEnabled": False,
                },
                "metadata": None,
            }
        ],
        "tags": ["客服", "FAQ"],
        "metadata": None,
    }


async def _create_agent(harness: AgentApiHarness) -> dict[str, Any]:
    response = await harness.client.post(
        "/api/v1/agents",
        json=_agent_payload(harness),
    )
    assert response.status_code == 201
    return response.json()["data"]


@pytest.mark.asyncio
async def test_create_agent_accepts_workflow_draft_without_system_prompt(
    agent_api_harness: AgentApiHarness,
) -> None:
    response = await agent_api_harness.client.post(
        "/api/v1/agents",
        json=_agent_payload(
            agent_api_harness,
            status="draft",
            orchestration_mode="workflow",
        ),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["code"] == 201
    assert payload["data"]["orchestrationMode"] == "workflow"
    assert payload["data"]["systemPrompt"] is None
    assert payload["data"]["workflowRef"] == {"workflowDraftKey": "draft-only"}
    assert payload["data"]["tools"][0]["toolId"] == agent_api_harness.tool_id
    assert payload["data"]["knowledgeBases"][0]["knowledgeBaseId"] == 20


@pytest.mark.asyncio
async def test_active_workflow_agent_is_rejected_until_workflow_exists(
    agent_api_harness: AgentApiHarness,
) -> None:
    response = await agent_api_harness.client.post(
        "/api/v1/agents",
        json=_agent_payload(
            agent_api_harness,
            status="active",
            orchestration_mode="workflow",
        ),
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == 4002
    assert "Workflow" in payload["message"]


@pytest.mark.asyncio
async def test_list_detail_and_preview_return_aggregated_agent_config(
    agent_api_harness: AgentApiHarness,
) -> None:
    created = await _create_agent(agent_api_harness)

    list_response = await agent_api_harness.client.get(
        "/api/v1/agents",
        params={"keyword": "客服", "status": "draft", "pageSize": 20},
    )
    detail_response = await agent_api_harness.client.get(
        f"/api/v1/agents/{created['id']}"
    )
    preview_response = await agent_api_harness.client.get(
        f"/api/v1/agents/{created['id']}/config-preview"
    )

    assert list_response.status_code == 200
    list_payload = list_response.json()["data"]
    assert list_payload["total"] == 1
    assert list_payload["list"][0]["toolCount"] == 1
    assert list_payload["list"][0]["knowledgeBaseCount"] == 1
    assert list_payload["list"][0]["model"]["modelName"] == "gpt-4.1-mini"

    assert detail_response.status_code == 200
    detail_payload = detail_response.json()["data"]
    assert detail_payload["id"] == created["id"]
    assert detail_payload["tools"][0]["bindingName"] == "查询订单"
    assert detail_payload["knowledgeBases"][0]["retrievalConfig"]["topK"] == 5

    assert preview_response.status_code == 200
    preview_payload = preview_response.json()["data"]
    assert preview_payload["agentId"] == created["id"]
    assert preview_payload["isRunnable"] is False
    assert preview_payload["enabledToolIds"] == [agent_api_harness.tool_id]
    assert preview_payload["enabledKnowledgeBaseIds"] == [20]


@pytest.mark.asyncio
async def test_update_replaces_bindings_and_delete_soft_deletes_agent(
    agent_api_harness: AgentApiHarness,
) -> None:
    created = await _create_agent(agent_api_harness)
    update_payload = _agent_payload(agent_api_harness, name="客服助手升级版")
    update_payload["tools"] = []
    update_payload["knowledgeBases"] = []

    update_response = await agent_api_harness.client.put(
        f"/api/v1/agents/{created['id']}",
        json=update_payload,
    )
    delete_response = await agent_api_harness.client.delete(
        f"/api/v1/agents/{created['id']}"
    )
    detail_response = await agent_api_harness.client.get(
        f"/api/v1/agents/{created['id']}"
    )

    assert update_response.status_code == 200
    update_data = update_response.json()["data"]
    assert update_data["name"] == "客服助手升级版"
    assert update_data["tools"] == []
    assert update_data["knowledgeBases"] == []

    assert delete_response.status_code == 204
    assert detail_response.status_code == 404
