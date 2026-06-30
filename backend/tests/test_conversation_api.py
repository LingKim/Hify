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

from app.agent.model import Agent, AgentToolBinding
from app.auth.model import User
from app.auth.password import hash_password
from app.conversation.model import ConversationMessage, ConversationRun
from app.core.auth import AccessTokenPayload, create_access_token
from app.core.database import Base, get_db_session
from app.llm.executor import LiteLLMExecutor, StreamChunk
from app.llm.model import ProviderAuthSecret, ProviderInstance, ProviderModel
from app.llm.provider import ProviderSecretCodec, ProviderSecretPayload
from app.main import app
from app.tool.model import Tool, ToolAuthSecret, ToolExecutionLog, ToolParameter


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
class ConversationApiHarness:
    client: httpx.AsyncClient
    session_factory: async_sessionmaker[AsyncSession]
    agent_id: int
    user_id: int
    headers: dict[str, str]
    stream_calls: list[dict[str, Any]]


@pytest_asyncio.fixture
async def conversation_api_harness(
    monkeypatch: pytest.MonkeyPatch,
) -> ConversationApiHarness:
    database_url = _database_url()
    schema_name = f"test_conversation_{uuid.uuid4().hex}"
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

    codec = ProviderSecretCodec()
    async with session_factory() as session:
        user = User(
            username="member",
            email="member@hify.ai",
            password_hash=hash_password("Member123!"),
            is_active=True,
        )
        session.add(user)
        await session.flush()
        provider = ProviderInstance(
            name="OpenAI-会话测试",
            provider_type="openai",
            api_family="openai_chat",
            base_url="https://api.openai.com/v1",
            status="active",
            is_default=True,
            priority=100,
        )
        session.add(provider)
        await session.flush()
        secret = ProviderAuthSecret(
            provider_instance_id=provider.id,
            auth_type="api_key",
            secret_ciphertext=codec.encrypt(
                ProviderSecretPayload(secret_value="sk-test-conversation")
            ),
            secret_masked="sk-t...tion",
            secret_fingerprint="test",
            encryption_key_version="v1",
        )
        session.add(secret)
        model = ProviderModel(
            provider_instance_id=provider.id,
            model_name="gpt-4.1-mini",
            display_name="GPT-4.1 Mini",
            status="active",
            is_default=True,
            supports_chat=True,
            supports_stream=True,
            supports_tools=True,
            sort_order=0,
        )
        session.add(model)
        await session.flush()
        agent = Agent(
            name="客服助手",
            description="回答售后问题",
            status="active",
            orchestration_mode="agent",
            provider_instance_id=provider.id,
            provider_model_id=model.id,
            system_prompt="你是客服助手。",
            opening_message="你好，我可以帮你查询售后政策。",
            model_config_json={"temperature": 0.2, "maxTokens": 1024},
            runtime_config_json={"memoryWindow": 10},
            tags_json=["客服"],
        )
        session.add(agent)
        await session.commit()
        agent_id = agent.id
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

    stream_calls: list[dict[str, Any]] = []

    async def fake_stream_text(
        self,  # noqa: ARG001
        runtime_config,  # type: ignore[no-untyped-def]
        *,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        stream_calls.append(
            {
                "runtime_config": runtime_config,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )
        yield StreamChunk(delta="根据当前")
        yield StreamChunk(delta="售后政策，可以 7 天内退换。")

    app.dependency_overrides[get_db_session] = override_get_db_session
    monkeypatch.setattr(LiteLLMExecutor, "stream_text", fake_stream_text)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        yield ConversationApiHarness(
            client=client,
            session_factory=session_factory,
            agent_id=agent_id,
            user_id=user_id,
            headers=headers,
            stream_calls=stream_calls,
        )

    app.dependency_overrides.clear()
    await _drop_schema(admin_engine, schema_name)
    await test_engine.dispose()
    await admin_engine.dispose()


@pytest.mark.asyncio
async def test_create_list_update_and_delete_conversation(
    conversation_api_harness: ConversationApiHarness,
) -> None:
    create_response = await conversation_api_harness.client.post(
        "/api/v1/conversations",
        json={
            "agentId": conversation_api_harness.agent_id,
            "title": "售后政策咨询",
        },
        headers=conversation_api_harness.headers,
    )

    assert create_response.status_code == 201
    created = create_response.json()["data"]
    assert created["agentName"] == "客服助手"
    assert created["openingMessage"] == "你好，我可以帮你查询售后政策。"
    assert created["agentSnapshot"]["modelName"] == "gpt-4.1-mini"
    assert created["messageCount"] == 0

    list_response = await conversation_api_harness.client.get(
        "/api/v1/conversations",
        params={"keyword": "售后", "pageSize": 20},
        headers=conversation_api_harness.headers,
    )
    detail_response = await conversation_api_harness.client.get(
        f"/api/v1/conversations/{created['id']}",
        headers=conversation_api_harness.headers,
    )
    archive_response = await conversation_api_harness.client.patch(
        f"/api/v1/conversations/{created['id']}",
        json={"status": "archived"},
        headers=conversation_api_harness.headers,
    )
    delete_response = await conversation_api_harness.client.delete(
        f"/api/v1/conversations/{created['id']}",
        headers=conversation_api_harness.headers,
    )
    missing_response = await conversation_api_harness.client.get(
        f"/api/v1/conversations/{created['id']}",
        headers=conversation_api_harness.headers,
    )

    assert list_response.status_code == 200
    assert list_response.json()["data"]["total"] == 1
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["id"] == created["id"]
    assert archive_response.status_code == 200
    assert archive_response.json()["data"]["status"] == "archived"
    assert delete_response.status_code == 204
    assert missing_response.status_code == 404
    assert missing_response.json()["code"] == 7001


@pytest.mark.asyncio
async def test_stream_message_persists_messages_and_run(
    conversation_api_harness: ConversationApiHarness,
) -> None:
    create_response = await conversation_api_harness.client.post(
        "/api/v1/conversations",
        json={"agentId": conversation_api_harness.agent_id},
        headers=conversation_api_harness.headers,
    )
    conversation_id = create_response.json()["data"]["id"]

    async with conversation_api_harness.client.stream(
        "POST",
        f"/api/v1/conversations/{conversation_id}/messages/stream",
        json={"content": "退货政策是什么？"},
        headers={
            **conversation_api_harness.headers,
            "Accept": "text/event-stream",
        },
    ) as response:
        body = await response.aread()

    text_body = body.decode("utf-8")
    assert response.status_code == 200
    assert "event: run.started" in text_body
    assert "event: message.created" in text_body
    assert "event: message.delta" in text_body
    assert "event: message.completed" in text_body
    assert "event: run.completed" in text_body
    assert "event: done" in text_body
    assert "根据当前" in text_body
    assert (
        conversation_api_harness.stream_calls[0]["messages"][0]["role"]
        == "system"
    )

    messages_response = await conversation_api_harness.client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        params={"pageSize": 100},
        headers=conversation_api_harness.headers,
    )

    assert messages_response.status_code == 200
    messages = messages_response.json()["data"]["list"]
    assert [item["role"] for item in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "退货政策是什么？"
    assert messages[1]["status"] == "completed"
    assert messages[1]["content"] == "根据当前售后政策，可以 7 天内退换。"

    async with conversation_api_harness.session_factory() as session:
        run = await session.scalar(select(ConversationRun))
        assistant = await session.scalar(
            select(ConversationMessage).where(
                ConversationMessage.role == "assistant"
            )
        )

    assert run is not None
    assert run.status == "completed"
    assert run.assistant_message_id == assistant.id


@pytest.mark.asyncio
async def test_stream_message_executes_bound_tool_and_exposes_tool_calls(
    conversation_api_harness: ConversationApiHarness,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_send = httpx.AsyncClient.send
    codec = ProviderSecretCodec()
    async with conversation_api_harness.session_factory() as session:
        tool = Tool(
            owner_user_id=conversation_api_harness.user_id,
            name="查询天气",
            description="按城市查询天气",
            status="enabled",
            tool_type="http",
            source_type="manual",
            http_method="GET",
            url="https://api.example.com/weather",
            timeout_seconds=15,
            headers_template_json={"Accept": "application/json"},
            query_template_json={"city": "{{city}}"},
            content_type="application/json",
        )
        session.add(tool)
        await session.flush()
        session.add(
            ToolAuthSecret(
                tool_id=tool.id,
                auth_type="api_key_header",
                secret_ciphertext=codec.encrypt(
                    ProviderSecretPayload(secret_value="sk-weather-tool")
                ),
                secret_masked="sk-w...tool",
                secret_fingerprint="weather",
                encryption_key_version="v1",
                metadata_json={"headerName": "X-API-Key"},
            )
        )
        session.add(
            ToolParameter(
                tool_id=tool.id,
                name="city",
                label="城市",
                description="要查询天气的城市名称",
                param_location="query",
                schema_type="string",
                is_required=True,
                schema_json={"type": "string"},
                sort_order=0,
            )
        )
        session.add(
            AgentToolBinding(
                agent_id=conversation_api_harness.agent_id,
                tool_id=tool.id,
                binding_name="weather_lookup",
                is_enabled=True,
                sort_order=0,
            )
        )
        await session.commit()
        tool_id = tool.id

    async def fake_send(self, request, **kwargs):  # type: ignore[no-untyped-def]
        if request.url.host == "testserver":
            return await original_send(self, request, **kwargs)
        del kwargs
        assert request.url == httpx.URL(
            "https://api.example.com/weather?city=%E6%9D%AD%E5%B7%9E"
        )
        assert request.headers["X-API-Key"] == "sk-weather-tool"
        return httpx.Response(
            200,
            json={"city": "杭州", "weather": "晴", "temperature": 26},
            request=request,
        )

    async def fake_invoke_with_tools(
        self,  # noqa: ARG001
        runtime_config,  # type: ignore[no-untyped-def]
        *,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        del runtime_config, messages, temperature, max_tokens
        assert tools[0]["function"]["name"] == "weather_lookup"
        return {
            "assistantMessage": {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_weather_1",
                        "type": "function",
                        "function": {
                            "name": "weather_lookup",
                            "arguments": '{"city":"杭州"}',
                        },
                    }
                ],
            },
            "toolCalls": [
                {
                    "id": "call_weather_1",
                    "name": "weather_lookup",
                    "arguments": {"city": "杭州"},
                }
            ],
        }

    async def fake_stream_text(
        self,  # noqa: ARG001
        runtime_config,  # type: ignore[no-untyped-def]
        *,
        messages: list[dict[str, Any]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        del runtime_config, temperature, max_tokens
        tool_messages = [
            message for message in messages if message["role"] == "tool"
        ]
        assert tool_messages
        assert "temperature" in tool_messages[0]["content"]
        yield StreamChunk(delta="杭州今天晴，")
        yield StreamChunk(delta="气温 26 度，适合露营。")

    monkeypatch.setattr(httpx.AsyncClient, "send", fake_send)
    monkeypatch.setattr(
        LiteLLMExecutor,
        "invoke_with_tools",
        fake_invoke_with_tools,
        raising=False,
    )
    monkeypatch.setattr(LiteLLMExecutor, "stream_text", fake_stream_text)

    create_response = await conversation_api_harness.client.post(
        "/api/v1/conversations",
        json={"agentId": conversation_api_harness.agent_id},
        headers=conversation_api_harness.headers,
    )
    conversation_id = create_response.json()["data"]["id"]

    async with conversation_api_harness.client.stream(
        "POST",
        f"/api/v1/conversations/{conversation_id}/messages/stream",
        json={"content": "杭州今天适合露营吗？"},
        headers={
            **conversation_api_harness.headers,
            "Accept": "text/event-stream",
        },
    ) as response:
        body = await response.aread()

    text_body = body.decode("utf-8")
    assert response.status_code == 200
    assert "event: tool.started" in text_body
    assert "event: tool.completed" in text_body
    assert "weather_lookup" in text_body
    assert "sk-weather-tool" not in text_body
    assert "杭州今天晴" in text_body

    messages_response = await conversation_api_harness.client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        params={"pageSize": 100},
        headers=conversation_api_harness.headers,
    )
    messages = messages_response.json()["data"]["list"]
    assistant = messages[1]
    assert assistant["content"] == "杭州今天晴，气温 26 度，适合露营。"
    assert assistant["toolCalls"][0]["toolId"] == tool_id
    assert assistant["toolCalls"][0]["status"] == "success"
    assert assistant["toolCalls"][0]["executionLogId"] is not None

    logs_response = await conversation_api_harness.client.get(
        f"/api/v1/tools/{tool_id}/execution-logs",
        params={"source": "conversation"},
        headers=conversation_api_harness.headers,
    )
    logs = logs_response.json()["data"]
    assert logs["total"] == 1
    assert logs["list"][0]["status"] == "success"

    async with conversation_api_harness.session_factory() as session:
        log = await session.scalar(select(ToolExecutionLog))
        run = await session.scalar(select(ConversationRun))

    assert log is not None
    assert log.source == "conversation"
    assert log.conversation_id == conversation_id
    assert log.run_id == run.id
    assert log.request_headers_json["X-API-Key"] != "sk-weather-tool"
