from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any

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
from app.conversation.model import (
    ConversationMessage,
    ConversationRun,
    ConversationSession,
)
from app.conversation.runtime import (
    ConversationRuntime,
    PreparedConversationRun,
    RuntimeStreamEvent,
)
from app.conversation.service import ConversationService
from app.core.database import Base
from app.llm.executor import LiteLLMExecutor, StreamChunk
from app.llm.model import ProviderAuthSecret, ProviderInstance, ProviderModel
from app.llm.provider import ProviderSecretCodec, ProviderSecretPayload
from app.tool.model import Tool, ToolAuthSecret, ToolExecutionLog, ToolParameter
from app.tool.service import ToolService

from tests._p4_echo import ToolEchoServer, start_echo_server


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
class ConversationToolHarness:
    session_factory: async_sessionmaker[AsyncSession]
    user_id: int
    agent_id: int
    echo: ToolEchoServer
    codec: ProviderSecretCodec
    tool_calls: list[dict[str, Any]]


@pytest_asyncio.fixture
async def conversation_tool_harness() -> ConversationToolHarness:
    database_url = _database_url()
    schema_name = f"test_conv_tool_{uuid.uuid4().hex}"
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
            username="conv_real",
            email="conv_real@hify.ai",
            password_hash=hash_password("ConvReal123!"),
            role="member",
            is_active=True,
        )
        session.add(user)
        await session.flush()
        provider = ProviderInstance(
            name="OpenAI-真工具测试",
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
                ProviderSecretPayload(secret_value="sk-conv-tool")
            ),
            secret_masked="sk-c...tool",
            secret_fingerprint="conv-tool",
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
            name="工具助手",
            description="调工具回答问题",
            status="active",
            orchestration_mode="agent",
            provider_instance_id=provider.id,
            provider_model_id=model.id,
            system_prompt="你可以调用工具。",
            opening_message="你好。",
            model_config_json={"temperature": 0.2, "maxTokens": 1024},
            tags_json=[],
        )
        session.add(agent)
        await session.commit()
        agent_id = agent.id
        user_id = user.id

    echo = start_echo_server(slow_delay=1.5)
    try:
        yield ConversationToolHarness(
            session_factory=session_factory,
            user_id=user_id,
            agent_id=agent_id,
            echo=echo,
            codec=codec,
            tool_calls=[],
        )
    finally:
        echo.stop()
        await _drop_schema(admin_engine, schema_name)
        await test_engine.dispose()
        await admin_engine.dispose()


async def _attach_weather_tool(
    session: AsyncSession,
    *,
    harness: ConversationToolHarness,
    tool_url: str,
    tool_name: str = "查询天气",
    binding_name: str = "weather_lookup",
    tool_status: str = "enabled",
) -> int:
    tool = Tool(
        owner_user_id=harness.user_id,
        name=tool_name,
        description="按城市查询天气",
        status=tool_status,
        tool_type="http",
        source_type="manual",
        http_method="GET",
        url=tool_url,
        timeout_seconds=5,
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
            secret_ciphertext=harness.codec.encrypt(
                ProviderSecretPayload(secret_value="sk-tool-real-conv")
            ),
            secret_masked="sk-t...conv",
            secret_fingerprint="real-conv",
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
            agent_id=harness.agent_id,
            tool_id=tool.id,
            binding_name=binding_name,
            is_enabled=True,
            sort_order=0,
        )
    )
    await session.commit()
    return int(tool.id)


async def _drain_stream(
    stream: Any,
) -> tuple[list[str], list[RuntimeStreamEvent]]:
    text_parts: list[str] = []
    events: list[RuntimeStreamEvent] = []
    async for item in stream:
        if isinstance(item, RuntimeStreamEvent):
            events.append(item)
        else:
            text_parts.append(str(item))
    return text_parts, events


@pytest.mark.asyncio
async def test_runtime_executes_bound_tool_over_real_http(
    conversation_tool_harness: ConversationToolHarness,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ToolService,
        "_validate_safe_url",
        lambda self, url: None,
    )
    base = conversation_tool_harness.echo.base_url

    tool_calls: list[dict[str, Any]] = []

    async def fake_invoke_with_tools(
        self,  # noqa: ARG001
        runtime_config,  # type: ignore[no-untyped-def]
        *,
        messages,  # type: ignore[no-untyped-def]
        tools,  # type: ignore[no-untyped-def]
        temperature=None,  # type: ignore[no-untyped-def]
        max_tokens=None,  # type: ignore[no-untyped-def]
    ) -> dict[str, Any]:
        del runtime_config, messages, temperature, max_tokens
        tool_calls.append({"tools": tools, "arguments": {"city": "杭州"}})
        return {
            "assistantMessage": {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_weather_real_1",
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
                    "id": "call_weather_real_1",
                    "name": "weather_lookup",
                    "arguments": {"city": "杭州"},
                }
            ],
        }

    async def fake_stream_text(
        self,  # noqa: ARG001
        runtime_config,  # type: ignore[no-untyped-def]
        *,
        messages,  # type: ignore[no-untyped-def]
        temperature=None,  # type: ignore[no-untyped-def]
        max_tokens=None,  # type: ignore[no-untyped-def]
    ):
        del runtime_config, temperature, max_tokens
        tool_messages = [m for m in messages if m["role"] == "tool"]
        assert tool_messages, "工具结果未回喂给 LLM"
        payload = tool_messages[0]["content"]
        assert "杭州" in payload or "temperature" in payload
        yield StreamChunk(delta="杭州今天晴，")
        yield StreamChunk(delta="气温 26 度。")

    monkeypatch.setattr(
        LiteLLMExecutor,
        "invoke_with_tools",
        fake_invoke_with_tools,
        raising=False,
    )
    monkeypatch.setattr(LiteLLMExecutor, "stream_text", fake_stream_text)

    async with conversation_tool_harness.session_factory() as session:
        tool_id = await _attach_weather_tool(
            session,
            harness=conversation_tool_harness,
            tool_url=f"{base}/ok",
        )
        service = ConversationService(session)
        conversation = ConversationSession(
            user_id=conversation_tool_harness.user_id,
            agent_id=conversation_tool_harness.agent_id,
            title="真工具测试",
            status="active",
            channel="api",
            agent_snapshot_json={"model": {"id": 1}},
            message_count=0,
        )
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
        prepared = await service.prepare_stream_message(
            conversation.id,
            _StreamRequest(content="杭州今天适合露营吗？"),  # type: ignore[arg-type]
            user_id=conversation_tool_harness.user_id,
        )
        prepared_run_id = prepared.run.id
        prepared_assistant_id = prepared.assistant_message.id
        conversation_id = conversation.id

        runtime = ConversationRuntime(
            db=session,
            secret_codec=conversation_tool_harness.codec,
            executor=LiteLLMExecutor(),
        )
        text_parts, events = await _drain_stream(
            runtime.stream_assistant_response(prepared)
        )

    full_text = "".join(text_parts)
    assert full_text == "杭州今天晴，气温 26 度。"
    event_names = [event.event for event in events]
    assert "tool.started" in event_names
    assert "tool.completed" in event_names

    completed = next(
        event
        for event in events
        if event.event == "tool.completed"
    )
    assert completed.data["toolId"] == tool_id
    assert completed.data["status"] == "success"
    assert completed.data["executionLogId"] is not None
    assert completed.data["responseStatusCode"] == 200

    inbound = conversation_tool_harness.echo.requests[-1]
    assert inbound.path == "/ok"
    assert inbound.query == {"city": "杭州"}
    inbound_header_map = {k.lower(): v for k, v in inbound.headers.items()}
    assert inbound_header_map.get("x-api-key") == "sk-tool-real-conv"

    assert tool_calls
    assert tool_calls[0]["tools"][0]["function"]["name"] == "weather_lookup"

    async with conversation_tool_harness.session_factory() as session:
        assistant = await session.scalar(
            select(ConversationMessage).where(
                ConversationMessage.id == prepared_assistant_id
            )
        )
        run = await session.scalar(
            select(ConversationRun).where(ConversationRun.id == prepared_run_id)
        )
        log = await session.scalar(
            select(ToolExecutionLog).where(ToolExecutionLog.tool_id == tool_id)
        )

    assert assistant is not None
    assert assistant.status == "completed"
    assert assistant.content == full_text
    assert assistant.tool_call_json is not None
    assert len(assistant.tool_call_json["calls"]) == 1
    assert assistant.tool_call_json["calls"][0]["status"] == "success"

    assert run is not None
    assert run.status == "completed"

    assert log is not None
    assert log.source == "conversation"
    assert log.conversation_id == conversation_id
    assert log.run_id == prepared_run_id
    assert log.status == "success"
    log_header_map = {
        k.lower(): v for k, v in (log.request_headers_json or {}).items()
    }
    assert log_header_map.get("x-api-key") != "sk-tool-real-conv"
    assert run.latency_ms is not None
    assert run.latency_ms >= 0


@pytest.mark.asyncio
async def test_runtime_survives_tool_5xx_without_dropping_conversation(
    conversation_tool_harness: ConversationToolHarness,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ToolService,
        "_validate_safe_url",
        lambda self, url: None,
    )
    base = conversation_tool_harness.echo.base_url

    async def fake_invoke_with_tools(
        self,  # noqa: ARG001
        runtime_config,  # type: ignore[no-untyped-def]
        *,
        messages,  # type: ignore[no-untyped-def]
        tools,  # type: ignore[no-untyped-def]
        temperature=None,  # type: ignore[no-untyped-def]
        max_tokens=None,  # type: ignore[no-untyped-def]
    ):
        del runtime_config, messages, tools, temperature, max_tokens
        return {
            "assistantMessage": {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_fail_1",
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
                    "id": "call_fail_1",
                    "name": "weather_lookup",
                    "arguments": {"city": "杭州"},
                }
            ],
        }

    async def fake_stream_text(
        self,  # noqa: ARG001
        runtime_config,  # type: ignore[no-untyped-def]
        *,
        messages,  # type: ignore[no-untyped-def]
        temperature=None,  # type: ignore[no-untyped-def]
        max_tokens=None,  # type: ignore[no-untyped-def]
    ):
        del runtime_config, temperature, max_tokens
        yield StreamChunk(delta="天气服务暂时不可用，请稍后再试。")

    monkeypatch.setattr(
        LiteLLMExecutor,
        "invoke_with_tools",
        fake_invoke_with_tools,
        raising=False,
    )
    monkeypatch.setattr(LiteLLMExecutor, "stream_text", fake_stream_text)

    async with conversation_tool_harness.session_factory() as session:
        tool_id = await _attach_weather_tool(
            session,
            harness=conversation_tool_harness,
            tool_url=f"{base}/fail",
        )
        service = ConversationService(session)
        conversation = ConversationSession(
            user_id=conversation_tool_harness.user_id,
            agent_id=conversation_tool_harness.agent_id,
            title="5xx 容错",
            status="active",
            channel="api",
            agent_snapshot_json={"model": {"id": 1}},
            message_count=0,
        )
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
        prepared = await service.prepare_stream_message(
            conversation.id,
            _StreamRequest(content="查天气"),  # type: ignore[arg-type]
            user_id=conversation_tool_harness.user_id,
        )
        prepared_run_id = prepared.run.id
        prepared_assistant_id = prepared.assistant_message.id

        runtime = ConversationRuntime(
            db=session,
            secret_codec=conversation_tool_harness.codec,
            executor=LiteLLMExecutor(),
        )
        text_parts, events = await _drain_stream(
            runtime.stream_assistant_response(prepared)
        )

    full_text = "".join(text_parts)
    assert full_text == "天气服务暂时不可用，请稍后再试。"
    event_names = [event.event for event in events]
    assert "tool.failed" in event_names

    failed = next(event for event in events if event.event == "tool.failed")
    assert failed.data["toolId"] == tool_id
    assert failed.data["status"] == "failed"
    assert failed.data["responseStatusCode"] == 500
    assert failed.data["errorCode"] == "http_error"

    async with conversation_tool_harness.session_factory() as session:
        assistant = await session.scalar(
            select(ConversationMessage).where(
                ConversationMessage.id == prepared_assistant_id
            )
        )
        run = await session.scalar(
            select(ConversationRun).where(ConversationRun.id == prepared_run_id)
        )
        log = await session.scalar(select(ToolExecutionLog))

    assert assistant is not None
    assert assistant.status == "completed"
    assert assistant.tool_call_json is not None
    assert assistant.tool_call_json["calls"][0]["status"] == "failed"

    assert run is not None
    assert run.status == "completed"

    assert log is not None
    assert log.source == "conversation"
    assert log.status == "failed"
    assert log.response_status_code == 500
    assert log.error_code == "http_error"


class _StreamRequest:
    """Stand-in matching ConversationStreamMessageReq shape."""

    def __init__(self, *, content: str) -> None:
        self.content = content
        self.metadata: dict[str, Any] | None = None
