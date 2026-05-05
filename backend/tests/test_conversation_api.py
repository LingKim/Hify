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

from app.agent.model import Agent
from app.conversation.model import ConversationMessage, ConversationRun
from app.core.database import Base, get_db_session
from app.llm.executor import LiteLLMExecutor, StreamChunk
from app.llm.model import ProviderAuthSecret, ProviderInstance, ProviderModel
from app.llm.provider import ProviderSecretCodec, ProviderSecretPayload
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
class ConversationApiHarness:
    client: httpx.AsyncClient
    session_factory: async_sessionmaker[AsyncSession]
    agent_id: int
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
    )
    detail_response = await conversation_api_harness.client.get(
        f"/api/v1/conversations/{created['id']}"
    )
    archive_response = await conversation_api_harness.client.patch(
        f"/api/v1/conversations/{created['id']}",
        json={"status": "archived"},
    )
    delete_response = await conversation_api_harness.client.delete(
        f"/api/v1/conversations/{created['id']}"
    )
    missing_response = await conversation_api_harness.client.get(
        f"/api/v1/conversations/{created['id']}"
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
    )
    conversation_id = create_response.json()["data"]["id"]

    async with conversation_api_harness.client.stream(
        "POST",
        f"/api/v1/conversations/{conversation_id}/messages/stream",
        json={"content": "退货政策是什么？"},
        headers={"Accept": "text/event-stream"},
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
    assert conversation_api_harness.stream_calls[0]["messages"][0]["role"] == "system"

    messages_response = await conversation_api_harness.client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        params={"pageSize": 100},
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
