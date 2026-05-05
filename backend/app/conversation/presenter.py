"""Conversation response and snapshot builders."""

from __future__ import annotations

from typing import Any

from app.agent.model import Agent
from app.conversation.model import ConversationMessage, ConversationSession
from app.conversation.schema import (
    ConversationAgentModelResp,
    ConversationAgentRuntimePreviewResp,
    ConversationDetailResp,
    ConversationMessageResp,
    ConversationSummaryResp,
)
from app.llm.model import ProviderInstance, ProviderModel


def preview_text(content: str) -> str:
    """Return a compact message preview for list rows."""
    return content.strip().replace("\n", " ")[:200]


def optional_float(value: Any) -> float | None:
    """Return value as float when it is a numeric config."""
    if isinstance(value, int | float):
        return float(value)
    return None


def optional_int(value: Any) -> int | None:
    """Return value as positive int when it is a numeric config."""
    if isinstance(value, int) and value > 0:
        return value
    return None


def build_agent_snapshot(
    agent: Agent,
    model: ProviderModel,
    provider: ProviderInstance,
) -> dict[str, Any]:
    """Build the immutable runtime snapshot stored on conversations."""
    model_snapshot = {
        "providerInstanceId": provider.id,
        "providerName": provider.name,
        "providerType": provider.provider_type,
        "providerModelId": model.id,
        "modelName": model.model_name,
        "displayName": model.display_name,
    }
    return {
        "agentId": agent.id,
        "name": agent.name,
        "orchestrationMode": agent.orchestration_mode,
        "openingMessage": agent.opening_message,
        "model": model_snapshot,
        **model_snapshot,
    }


def build_summary_response(
    conversation: ConversationSession,
) -> ConversationSummaryResp:
    """Build a list-friendly conversation response."""
    snapshot = conversation.agent_snapshot_json or {}
    return ConversationSummaryResp(
        id=conversation.id,
        userId=conversation.user_id,
        agentId=conversation.agent_id,
        agentName=str(snapshot.get("name") or "未知 Agent"),
        title=conversation.title,
        status=conversation.status,
        channel=conversation.channel,
        lastMessageRole=conversation.last_message_role,
        lastMessagePreview=conversation.last_message_preview,
        lastMessageAt=conversation.last_message_at,
        messageCount=conversation.message_count,
        createdAt=conversation.created_at,
        updatedAt=conversation.updated_at,
    )


def build_detail_response(
    conversation: ConversationSession,
) -> ConversationDetailResp:
    """Build a conversation detail response."""
    summary = build_summary_response(conversation)
    snapshot = conversation.agent_snapshot_json or {}
    return ConversationDetailResp(
        **summary.model_dump(by_alias=True),
        openingMessage=snapshot.get("openingMessage"),
        agentSnapshot=snapshot,
        metadata=conversation.metadata_json,
    )


def build_message_response(
    message: ConversationMessage,
) -> ConversationMessageResp:
    """Build a message history response."""
    return ConversationMessageResp(
        id=message.id,
        conversationId=message.conversation_id,
        runId=message.run_id,
        role=message.role,
        status=message.status,
        content=message.content,
        contentFormat=message.content_format,
        sequence=message.sequence,
        tokenCount=message.token_count,
        latencyMs=message.latency_ms,
        modelSnapshot=message.model_snapshot_json,
        error=message.error_json,
        createdAt=message.created_at,
        updatedAt=message.updated_at,
    )


def build_runtime_preview_response(
    *,
    agent: Agent,
    model: ProviderModel | None,
    provider: ProviderInstance | None,
    blocked_reason: str | None,
) -> ConversationAgentRuntimePreviewResp:
    """Build the Agent runtime preview response for conversation pages."""
    model_payload = None
    if model is not None:
        model_payload = ConversationAgentModelResp(
            providerInstanceId=model.provider_instance_id,
            providerName=provider.name if provider is not None else None,
            providerType=provider.provider_type if provider is not None else None,
            modelId=model.id,
            modelName=model.model_name,
            displayName=model.display_name,
            supportsStream=model.supports_stream,
        )

    return ConversationAgentRuntimePreviewResp(
        agentId=agent.id,
        name=agent.name,
        status=agent.status,
        orchestrationMode=agent.orchestration_mode,
        isRunnable=blocked_reason is None,
        blockedReason=blocked_reason,
        model=model_payload,
        openingMessage=agent.opening_message,
        enabledToolIds=[
            binding.tool_id
            for binding in agent.tool_bindings
            if binding.deleted_at is None and binding.is_enabled
        ],
        enabledKnowledgeBaseIds=[
            binding.knowledge_base_id
            for binding in agent.knowledge_bindings
            if binding.deleted_at is None and binding.is_enabled
        ],
    )
