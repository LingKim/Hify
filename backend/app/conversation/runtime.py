"""Conversation runtime orchestration helpers."""

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agent.errors import AgentErrorCode
from app.agent.model import Agent
from app.conversation.errors import ConversationErrorCode
from app.conversation.model import (
    ConversationMessage,
    ConversationRun,
    ConversationSession,
)
from app.conversation.presenter import preview_text
from app.core.database import utc_now
from app.core.exceptions import BizException
from app.llm.executor import LiteLLMExecutor
from app.llm.model import ProviderAuthSecret, ProviderInstance, ProviderModel
from app.llm.provider import (
    LiteLLMRuntimeConfig,
    ProviderSecretCodec,
    resolve_litellm_model,
)
from app.tool.service import ToolService


@dataclass(frozen=True, slots=True)
class RuntimeTool:
    """A tool exposed to the model during one conversation run."""

    tool_id: int
    tool_name: str
    runtime_tool_name: str
    description: str | None
    http_method: str
    parameter_count: int
    schema: dict[str, Any]


@dataclass(frozen=True, slots=True)
class RuntimeStreamEvent:
    """Non-token event emitted while streaming a conversation run."""

    event: str
    data: dict[str, Any]


@dataclass(frozen=True, slots=True)
class PreparedConversationRun:
    """Persisted state needed before starting an SSE stream."""

    conversation: ConversationSession
    run: ConversationRun
    user_message: ConversationMessage
    assistant_message: ConversationMessage
    runtime_config: LiteLLMRuntimeConfig
    messages: list[dict[str, str]]
    temperature: float | None
    max_tokens: int | None
    user_id: int
    tools: list[RuntimeTool]


class ConversationRuntime:
    """Runtime operations for Agent validation and streaming execution."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        secret_codec: ProviderSecretCodec,
        executor: LiteLLMExecutor,
    ) -> None:
        """Initialize runtime helpers."""
        self.db = db
        self.secret_codec = secret_codec
        self.executor = executor

    async def load_runnable_agent(
        self,
        agent_id: int,
    ) -> tuple[Agent, ProviderModel, ProviderInstance, ProviderAuthSecret]:
        """Load an Agent and ensure it can run a streaming chat."""
        agent = await self.get_agent_or_raise(agent_id)
        if agent.status != "active":
            raise BizException(
                code=ConversationErrorCode.AGENT_MODEL_NOT_CONFIGURED,
                message="Agent 当前不是启用状态",
                http_status=status.HTTP_400_BAD_REQUEST,
            )
        if agent.orchestration_mode == "workflow":
            raise BizException(
                code=AgentErrorCode.INVALID_CONFIGURATION,
                message="Workflow Agent 暂不能运行",
                http_status=status.HTTP_400_BAD_REQUEST,
            )
        if agent.provider_model_id is None:
            raise BizException(
                code=ConversationErrorCode.AGENT_MODEL_NOT_CONFIGURED,
                message="Agent 尚未绑定模型",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        model = await self._load_provider_model(agent.provider_model_id)
        provider = model.provider_instance
        if provider is None or provider.deleted_at is not None:
            raise BizException(
                code=ConversationErrorCode.AGENT_MODEL_NOT_CONFIGURED,
                message="Agent 绑定 Provider 不存在",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        secret = await self._load_provider_secret(provider.id)
        return agent, model, provider, secret

    async def get_agent_or_raise(self, agent_id: int) -> Agent:
        """Return an Agent or raise a module error."""
        statement = (
            select(Agent)
            .where(Agent.id == agent_id, Agent.deleted_at.is_(None))
            .options(
                selectinload(Agent.tool_bindings),
                selectinload(Agent.knowledge_bindings),
            )
        )
        agent = await self.db.scalar(statement)
        if agent is None:
            raise BizException(
                code=AgentErrorCode.AGENT_NOT_FOUND,
                message="Agent 不存在",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        return agent

    async def next_message_sequence(self, conversation_id: int) -> int:
        """Return the next sequence number for one conversation."""
        statement = select(func.max(ConversationMessage.sequence)).where(
            ConversationMessage.conversation_id == conversation_id,
            ConversationMessage.deleted_at.is_(None),
        )
        max_sequence = await self.db.scalar(statement)
        return int(max_sequence or 0) + 1

    async def build_llm_messages(
        self,
        conversation_id: int,
        agent: Agent,
        current_content: str,
    ) -> list[dict[str, str]]:
        """Build the LLM message list from prompt and history."""
        messages: list[dict[str, str]] = []
        if agent.system_prompt:
            messages.append({"role": "system", "content": agent.system_prompt})

        statement = (
            select(ConversationMessage)
            .where(
                ConversationMessage.conversation_id == conversation_id,
                ConversationMessage.deleted_at.is_(None),
                ConversationMessage.status == "completed",
            )
            .order_by(ConversationMessage.sequence.asc())
        )
        for message in list((await self.db.scalars(statement)).all()):
            if message.role in {"user", "assistant"}:
                messages.append(
                    {"role": message.role, "content": message.content}
                )

        if not messages or messages[-1]["content"] != current_content:
            messages.append({"role": "user", "content": current_content})
        return messages

    def build_runtime_config(
        self,
        provider: ProviderInstance,
        model: ProviderModel,
        secret: ProviderAuthSecret,
    ) -> LiteLLMRuntimeConfig:
        """Resolve the LiteLLM runtime config for one provider/model."""
        payload = self.secret_codec.decrypt(secret.secret_ciphertext)
        headers = {"Authorization": f"Bearer {payload.secret_value}"}
        return LiteLLMRuntimeConfig(
            provider_type=provider.provider_type,
            api_family=provider.api_family,
            model_name=model.model_name,
            litellm_model=resolve_litellm_model(
                provider.provider_type,
                model.model_name,
            ),
            api_base=provider.base_url,
            api_key=payload.secret_value,
            extra_headers=headers,
            query_params=payload.query_params or {},
        )

    async def stream_assistant_response(
        self,
        prepared: PreparedConversationRun,
    ) -> AsyncIterator[str | RuntimeStreamEvent]:
        """Yield assistant deltas and persist final stream state."""
        content_parts: list[str] = []
        start_clock = perf_counter()
        try:
            if prepared.tools:
                async for event in self._stream_with_tools(
                    prepared,
                    content_parts,
                ):
                    yield event
            else:
                async for chunk in self.executor.stream_text(
                    prepared.runtime_config,
                    messages=prepared.messages,
                    temperature=prepared.temperature,
                    max_tokens=prepared.max_tokens,
                ):
                    content_parts.append(chunk.delta)
                    yield chunk.delta
        except BizException as exc:
            await self.mark_stream_failed(prepared, exc)
            raise

        output_text = "".join(content_parts)
        latency_ms = int((perf_counter() - start_clock) * 1000)
        tool_calls = self._collect_tool_calls(prepared)
        await self.mark_stream_completed(
            prepared,
            output_text,
            latency_ms,
            tool_calls=tool_calls,
        )

    async def _stream_with_tools(
        self,
        prepared: PreparedConversationRun,
        content_parts: list[str],
    ) -> AsyncIterator[str | RuntimeStreamEvent]:
        tool_definitions = [tool.schema for tool in prepared.tools]
        decision = await self.executor.invoke_with_tools(
            prepared.runtime_config,
            messages=prepared.messages,
            tools=tool_definitions,
            temperature=prepared.temperature,
            max_tokens=prepared.max_tokens,
        )
        assistant_message, tool_calls = self._normalize_tool_decision(decision)
        if not tool_calls:
            content = str(assistant_message.get("content") or "")
            if content:
                content_parts.append(content)
                yield content
            return

        followup_messages: list[dict[str, Any]] = list(prepared.messages)
        followup_messages.append(assistant_message)
        tool_lookup = {tool.runtime_tool_name: tool for tool in prepared.tools}
        tool_summaries: list[dict[str, Any]] = []
        tool_service = ToolService(self.db)
        for call in tool_calls:
            runtime_tool = tool_lookup.get(call["name"])
            if runtime_tool is None:
                summary = self._unknown_tool_summary(prepared, call)
                tool_summaries.append(summary)
                yield RuntimeStreamEvent("tool.failed", summary)
                followup_messages.append(self._tool_message(call, summary))
                continue

            started = {
                "runId": prepared.run.id,
                "conversationId": prepared.conversation.id,
                "messageId": prepared.assistant_message.id,
                "toolCallId": call["id"],
                "toolId": runtime_tool.tool_id,
                "toolName": runtime_tool.tool_name,
                "runtimeToolName": runtime_tool.runtime_tool_name,
                "argumentsPreview": self._mask_mapping(call["arguments"]),
                "startedAt": utc_now().isoformat(),
            }
            yield RuntimeStreamEvent("tool.started", started)
            result = await tool_service.execute_conversation(
                runtime_tool.tool_id,
                call["arguments"],
                user_id=prepared.user_id,
                conversation_id=prepared.conversation.id,
                run_id=prepared.run.id,
                tool_call_id=call["id"],
                runtime_tool_name=runtime_tool.runtime_tool_name,
            )
            summary = self._tool_result_summary(
                prepared,
                call,
                runtime_tool,
                result,
            )
            tool_summaries.append(summary)
            event_name = (
                "tool.completed"
                if summary["status"] == "success"
                else "tool.failed"
            )
            yield RuntimeStreamEvent(event_name, summary)
            followup_messages.append(self._tool_message(call, summary))

        prepared.assistant_message.tool_call_json = {"calls": tool_summaries}
        await self.db.commit()
        async for chunk in self.executor.stream_text(
            prepared.runtime_config,
            messages=followup_messages,
            temperature=prepared.temperature,
            max_tokens=prepared.max_tokens,
        ):
            content_parts.append(chunk.delta)
            yield chunk.delta

    async def mark_stream_completed(
        self,
        prepared: PreparedConversationRun,
        output_text: str,
        latency_ms: int,
        *,
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> None:
        """Persist a completed stream."""
        assistant = await self.db.get(
            ConversationMessage,
            prepared.assistant_message.id,
        )
        run = await self.db.get(ConversationRun, prepared.run.id)
        conversation = await self.db.get(
            ConversationSession,
            prepared.conversation.id,
        )
        if assistant is None or run is None or conversation is None:
            return

        now = utc_now()
        assistant.content = output_text
        assistant.status = "completed"
        assistant.latency_ms = latency_ms
        if tool_calls:
            assistant.tool_call_json = {"calls": tool_calls}
        assistant.updated_at = now
        assistant.version += 1
        run.status = "completed"
        run.completed_at = now
        run.latency_ms = latency_ms
        run.response_json = {
            "finishReason": "stop",
            "toolCalls": tool_calls or [],
        }
        run.version += 1
        conversation.last_message_role = "assistant"
        conversation.last_message_preview = preview_text(output_text)
        conversation.last_message_at = now
        conversation.version += 1
        await self.db.commit()

    def _collect_tool_calls(
        self,
        prepared: PreparedConversationRun,
    ) -> list[dict[str, Any]]:
        payload = prepared.assistant_message.tool_call_json or {}
        calls = payload.get("calls") if isinstance(payload, dict) else None
        return calls if isinstance(calls, list) else []

    def _normalize_tool_decision(
        self,
        decision: Any,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        if isinstance(decision, dict):
            assistant = decision.get("assistantMessage") or {
                "role": "assistant",
                "content": "",
            }
            calls = decision.get("toolCalls") or []
            return dict(assistant), [
                self._normalize_tool_call(call) for call in calls
            ]

        assistant = getattr(decision, "assistant_message", None) or {
            "role": "assistant",
            "content": "",
        }
        calls = getattr(decision, "tool_calls", None) or []
        return dict(assistant), [
            self._normalize_tool_call(call) for call in calls
        ]

    def _normalize_tool_call(self, call: Any) -> dict[str, Any]:
        call_id = self._read_value(call, "id") or "tool_call"
        name = self._read_value(call, "name") or ""
        arguments = self._read_value(call, "arguments") or {}
        return {
            "id": str(call_id),
            "name": str(name),
            "arguments": arguments if isinstance(arguments, dict) else {},
        }

    def _read_value(self, value: Any, key: str) -> Any:
        if isinstance(value, dict):
            return value.get(key)
        return getattr(value, key, None)

    def _unknown_tool_summary(
        self,
        prepared: PreparedConversationRun,
        call: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "runId": prepared.run.id,
            "conversationId": prepared.conversation.id,
            "messageId": prepared.assistant_message.id,
            "toolCallId": call["id"],
            "toolId": 0,
            "toolName": call["name"],
            "runtimeToolName": call["name"],
            "status": "failed",
            "executionLogId": None,
            "argumentsPreview": self._mask_mapping(call["arguments"]),
            "responsePreview": None,
            "latencyMs": None,
            "errorCode": "unknown_tool",
            "errorMessage": "模型请求调用未知工具",
            "retryable": False,
            "completedAt": utc_now().isoformat(),
        }

    def _tool_result_summary(
        self,
        prepared: PreparedConversationRun,
        call: dict[str, Any],
        runtime_tool: RuntimeTool,
        result: Any,
    ) -> dict[str, Any]:
        return {
            "runId": prepared.run.id,
            "conversationId": prepared.conversation.id,
            "messageId": prepared.assistant_message.id,
            "toolCallId": call["id"],
            "toolId": runtime_tool.tool_id,
            "toolName": runtime_tool.tool_name,
            "runtimeToolName": runtime_tool.runtime_tool_name,
            "status": result.status,
            "executionLogId": result.log_id,
            "argumentsPreview": self._mask_mapping(call["arguments"]),
            "responseStatusCode": result.response.status_code,
            "responsePreview": result.response.body_preview,
            "latencyMs": result.latency_ms,
            "errorCode": result.error_code,
            "errorMessage": result.error_message,
            "retryable": result.status in {"timeout", "failed"},
            "completedAt": result.created_at.isoformat(),
        }

    def _tool_message(
        self,
        call: dict[str, Any],
        summary: dict[str, Any],
    ) -> dict[str, Any]:
        content = {
            "status": summary["status"],
            "responsePreview": summary.get("responsePreview"),
            "errorCode": summary.get("errorCode"),
            "errorMessage": summary.get("errorMessage"),
        }
        return {
            "role": "tool",
            "tool_call_id": call["id"],
            "name": call["name"],
            "content": json.dumps(content, ensure_ascii=False),
        }

    def _mask_mapping(self, values: dict[str, Any]) -> dict[str, Any]:
        masked: dict[str, Any] = {}
        for key, value in values.items():
            lowered = key.lower()
            if any(
                marker in lowered
                for marker in ("token", "password", "secret", "key")
            ):
                masked[key] = "***"
            else:
                masked[key] = value
        return masked

    async def mark_stream_failed(
        self,
        prepared: PreparedConversationRun,
        exc: BizException,
    ) -> None:
        """Persist a failed stream."""
        assistant = await self.db.get(
            ConversationMessage,
            prepared.assistant_message.id,
        )
        run = await self.db.get(ConversationRun, prepared.run.id)
        error_payload = {"code": int(exc.code), "message": exc.message}
        if assistant is not None:
            assistant.status = "failed"
            assistant.error_json = error_payload
            assistant.version += 1
        if run is not None:
            run.status = "failed"
            run.completed_at = utc_now()
            run.error_json = error_payload
            run.version += 1
        await self.db.commit()

    async def _load_provider_model(
        self,
        provider_model_id: int,
    ) -> ProviderModel:
        statement = (
            select(ProviderModel)
            .where(
                ProviderModel.id == provider_model_id,
                ProviderModel.deleted_at.is_(None),
            )
            .options(selectinload(ProviderModel.provider_instance))
        )
        model = await self.db.scalar(statement)
        if model is None:
            raise BizException(
                code=ConversationErrorCode.AGENT_MODEL_NOT_CONFIGURED,
                message="Agent 绑定模型不存在",
                http_status=status.HTTP_400_BAD_REQUEST,
            )
        if not model.supports_chat or not model.supports_stream:
            raise BizException(
                code=ConversationErrorCode.AGENT_MODEL_NOT_CONFIGURED,
                message="Agent 绑定模型不支持流式对话",
                http_status=status.HTTP_400_BAD_REQUEST,
            )
        return model

    async def _load_provider_secret(
        self,
        provider_instance_id: int,
    ) -> ProviderAuthSecret:
        statement = select(ProviderAuthSecret).where(
            ProviderAuthSecret.provider_instance_id == provider_instance_id,
            ProviderAuthSecret.deleted_at.is_(None),
        )
        secret = await self.db.scalar(statement)
        if secret is None:
            raise BizException(
                code=ConversationErrorCode.AGENT_MODEL_NOT_CONFIGURED,
                message="Agent 绑定 Provider 未配置密钥",
                http_status=status.HTTP_400_BAD_REQUEST,
            )
        return secret
