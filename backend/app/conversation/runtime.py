"""Conversation runtime orchestration helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from time import perf_counter

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
    ) -> AsyncIterator[str]:
        """Yield assistant deltas and persist final stream state."""
        content_parts: list[str] = []
        start_clock = perf_counter()
        try:
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
        await self.mark_stream_completed(prepared, output_text, latency_ms)

    async def mark_stream_completed(
        self,
        prepared: PreparedConversationRun,
        output_text: str,
        latency_ms: int,
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
        assistant.updated_at = now
        assistant.version += 1
        run.status = "completed"
        run.completed_at = now
        run.latency_ms = latency_ms
        run.response_json = {"finishReason": "stop"}
        run.version += 1
        conversation.last_message_role = "assistant"
        conversation.last_message_preview = preview_text(output_text)
        conversation.last_message_at = now
        conversation.version += 1
        await self.db.commit()

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

    async def _load_provider_model(self, provider_model_id: int) -> ProviderModel:
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
