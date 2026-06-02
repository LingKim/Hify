"""Conversation module request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.responses import PageParams

ConversationStatus = Literal["active", "archived"]
MessageRole = Literal["user", "assistant", "system", "tool"]
MessageStatus = Literal[
    "pending",
    "streaming",
    "completed",
    "failed",
    "cancelled",
]


class ConversationChatPreviewResp(BaseModel):
    """Response schema for the conversation preview endpoint."""

    module: str
    status: str
    capabilities: list[str]


class ConversationListParams(PageParams):
    """Conversation list query parameters."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    keyword: str | None = None
    agent_id: int | None = Field(default=None, alias="agentId", gt=0)
    status: ConversationStatus | None = None
    include_archived: bool = Field(default=False, alias="includeArchived")


class ConversationCreateReq(BaseModel):
    """Create conversation payload."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    agent_id: int = Field(alias="agentId", gt=0)
    title: str | None = Field(default=None, max_length=255)
    channel: str = Field(default="web", min_length=1, max_length=32)
    metadata: dict[str, Any] | None = None

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class ConversationUpdateReq(BaseModel):
    """Update conversation payload."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    title: str | None = Field(default=None, min_length=1, max_length=255)
    status: ConversationStatus | None = None


class ConversationMessageListParams(PageParams):
    """Message list query parameters."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    page_size: int = Field(default=100, alias="pageSize", ge=1, le=100)
    role: MessageRole | None = None


class ConversationStreamMessageReq(BaseModel):
    """Payload for streaming one user message."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    content: str = Field(min_length=1, max_length=20000)
    metadata: dict[str, Any] | None = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("消息内容不能为空")
        return stripped


class ConversationAgentModelResp(BaseModel):
    """Runtime model summary used by conversation."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    provider_instance_id: int = Field(alias="providerInstanceId")
    provider_name: str | None = Field(default=None, alias="providerName")
    provider_type: str | None = Field(default=None, alias="providerType")
    model_id: int = Field(alias="modelId")
    model_name: str = Field(alias="modelName")
    display_name: str = Field(alias="displayName")
    supports_stream: bool = Field(alias="supportsStream")


class ConversationRuntimeToolResp(BaseModel):
    """Runtime tool summary exposed by one Agent."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    tool_id: int = Field(alias="toolId")
    tool_name: str = Field(alias="toolName")
    runtime_tool_name: str = Field(alias="runtimeToolName")
    description: str | None = None
    status: str
    http_method: str = Field(alias="httpMethod")
    parameter_count: int = Field(alias="parameterCount")


class ConversationAgentRuntimePreviewResp(BaseModel):
    """Runnable preview for one agent in conversation context."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    agent_id: int = Field(alias="agentId")
    name: str
    status: str
    orchestration_mode: str = Field(alias="orchestrationMode")
    is_runnable: bool = Field(alias="isRunnable")
    blocked_reason: str | None = Field(default=None, alias="blockedReason")
    model: ConversationAgentModelResp | None = None
    opening_message: str | None = Field(default=None, alias="openingMessage")
    enabled_tool_ids: list[int] = Field(alias="enabledToolIds")
    enabled_knowledge_base_ids: list[int] = Field(
        alias="enabledKnowledgeBaseIds",
    )
    tools: list[ConversationRuntimeToolResp] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ConversationSummaryResp(BaseModel):
    """Conversation summary payload."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int
    user_id: int = Field(alias="userId")
    agent_id: int = Field(alias="agentId")
    agent_name: str = Field(alias="agentName")
    title: str
    status: ConversationStatus
    channel: str
    last_message_role: str | None = Field(default=None, alias="lastMessageRole")
    last_message_preview: str | None = Field(
        default=None,
        alias="lastMessagePreview",
    )
    last_message_at: datetime | None = Field(
        default=None,
        alias="lastMessageAt",
    )
    message_count: int = Field(alias="messageCount")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class ConversationDetailResp(ConversationSummaryResp):
    """Conversation detail payload."""

    opening_message: str | None = Field(default=None, alias="openingMessage")
    agent_snapshot: dict[str, Any] = Field(alias="agentSnapshot")
    metadata: dict[str, Any] | None = None


class ConversationKnowledgeSourceResp(BaseModel):
    """Knowledge source used by one assistant message."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    chunk_id: int = Field(alias="chunkId")
    document_id: int = Field(alias="documentId")
    document_name: str = Field(alias="documentName")
    score: float
    page_number: int | None = Field(default=None, alias="pageNumber")
    section_title: str | None = Field(default=None, alias="sectionTitle")
    snippet: str | None = None


class ConversationToolCallResp(BaseModel):
    """UI-safe tool call summary stored on an assistant message."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    tool_call_id: str = Field(alias="toolCallId")
    tool_id: int = Field(alias="toolId")
    tool_name: str = Field(alias="toolName")
    runtime_tool_name: str = Field(alias="runtimeToolName")
    status: str
    execution_log_id: int | None = Field(default=None, alias="executionLogId")
    arguments_preview: dict[str, Any] = Field(
        default_factory=dict,
        alias="argumentsPreview",
    )
    response_preview: str | None = Field(default=None, alias="responsePreview")
    latency_ms: int | None = Field(default=None, alias="latencyMs")
    error_code: str | None = Field(default=None, alias="errorCode")
    error_message: str | None = Field(default=None, alias="errorMessage")


class ConversationMessageResp(BaseModel):
    """Conversation message payload."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int
    conversation_id: int = Field(alias="conversationId")
    run_id: int | None = Field(default=None, alias="runId")
    role: MessageRole
    status: MessageStatus
    content: str
    content_format: str = Field(alias="contentFormat")
    sequence: int
    token_count: int | None = Field(default=None, alias="tokenCount")
    latency_ms: int | None = Field(default=None, alias="latencyMs")
    model_snapshot: dict[str, Any] | None = Field(
        default=None,
        alias="modelSnapshot",
    )
    error: dict[str, Any] | None = None
    knowledge_sources: list[ConversationKnowledgeSourceResp] = Field(
        default_factory=list,
        alias="knowledgeSources",
    )
    tool_calls: list[ConversationToolCallResp] = Field(
        default_factory=list,
        alias="toolCalls",
    )
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
