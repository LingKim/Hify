"""Agent module request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.responses import PageParams

AgentStatus = Literal["draft", "active", "disabled", "archived"]
AgentOrchestrationMode = Literal["agent", "chatbot", "workflow"]


class AgentConfigPreviewResp(BaseModel):
    """Response schema for the legacy agent preview endpoint."""

    module: str
    status: str
    capabilities: list[str]


class AgentModelSummaryResp(BaseModel):
    """Selected provider model summary shown by admin pages."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    provider_instance_id: int = Field(alias="providerInstanceId")
    provider_name: str | None = Field(default=None, alias="providerName")
    provider_type: str | None = Field(default=None, alias="providerType")
    model_id: int = Field(alias="modelId")
    model_name: str = Field(alias="modelName")
    display_name: str = Field(alias="displayName")


class AgentToolBindingInput(BaseModel):
    """Tool binding input payload."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    tool_id: int = Field(alias="toolId", gt=0)
    binding_name: str | None = Field(default=None, alias="bindingName")
    is_enabled: bool = Field(default=True, alias="isEnabled")
    sort_order: int = Field(default=0, alias="sortOrder", ge=0)
    config: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class AgentKnowledgeBindingInput(BaseModel):
    """Knowledge-base binding input payload."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    knowledge_base_id: int = Field(alias="knowledgeBaseId", gt=0)
    is_enabled: bool = Field(default=True, alias="isEnabled")
    sort_order: int = Field(default=0, alias="sortOrder", ge=0)
    retrieval_config: dict[str, Any] | None = Field(
        default=None,
        alias="retrievalConfig",
    )
    metadata: dict[str, Any] | None = None


class AgentAdminCreateReq(BaseModel):
    """Create payload for aggregated agent configuration."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    avatar_url: str | None = Field(
        default=None,
        alias="avatarUrl",
        max_length=512,
    )
    status: AgentStatus = "draft"
    orchestration_mode: AgentOrchestrationMode = Field(
        default="agent",
        alias="orchestrationMode",
    )
    provider_instance_id: int | None = Field(
        default=None,
        alias="providerInstanceId",
        gt=0,
    )
    provider_model_id: int | None = Field(
        default=None,
        alias="providerModelId",
        gt=0,
    )
    system_prompt: str | None = Field(default=None, alias="systemPrompt")
    opening_message: str | None = Field(default=None, alias="openingMessage")
    model_settings: dict[str, Any] | None = Field(
        default=None,
        alias="modelConfig",
    )
    runtime_config: dict[str, Any] | None = Field(
        default=None,
        alias="runtimeConfig",
    )
    workflow_ref: dict[str, Any] | None = Field(
        default=None,
        alias="workflowRef",
    )
    tools: list[AgentToolBindingInput] = Field(default_factory=list)
    knowledge_bases: list[AgentKnowledgeBindingInput] = Field(
        default_factory=list,
        alias="knowledgeBases",
    )
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] | None = None

    @field_validator("tools")
    @classmethod
    def validate_unique_tools(
        cls,
        tools: list[AgentToolBindingInput],
    ) -> list[AgentToolBindingInput]:
        tool_ids = [item.tool_id for item in tools]
        if len(tool_ids) != len(set(tool_ids)):
            raise ValueError("同一个 Agent 下工具不能重复")
        return tools

    @field_validator("knowledge_bases")
    @classmethod
    def validate_unique_knowledge_bases(
        cls,
        knowledge_bases: list[AgentKnowledgeBindingInput],
    ) -> list[AgentKnowledgeBindingInput]:
        knowledge_base_ids = [
            item.knowledge_base_id for item in knowledge_bases
        ]
        if len(knowledge_base_ids) != len(set(knowledge_base_ids)):
            raise ValueError("同一个 Agent 下知识库不能重复")
        return knowledge_bases


class AgentAdminUpdateReq(AgentAdminCreateReq):
    """Update payload for aggregated agent configuration."""


class AgentListParams(PageParams):
    """List query params for agent summaries."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    keyword: str | None = None
    status: AgentStatus | None = None
    orchestration_mode: AgentOrchestrationMode | None = Field(
        default=None,
        alias="orchestrationMode",
    )
    provider_model_id: int | None = Field(
        default=None,
        alias="providerModelId",
        gt=0,
    )


class AgentToolBindingResp(BaseModel):
    """Tool binding response payload."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    tool_id: int = Field(alias="toolId")
    binding_name: str | None = Field(default=None, alias="bindingName")
    is_enabled: bool = Field(alias="isEnabled")
    sort_order: int = Field(alias="sortOrder")
    config: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class AgentKnowledgeBindingResp(BaseModel):
    """Knowledge-base binding response payload."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    knowledge_base_id: int = Field(alias="knowledgeBaseId")
    is_enabled: bool = Field(alias="isEnabled")
    sort_order: int = Field(alias="sortOrder")
    retrieval_config: dict[str, Any] | None = Field(
        default=None,
        alias="retrievalConfig",
    )
    metadata: dict[str, Any] | None = None


class AgentSummaryResp(BaseModel):
    """Agent summary response used by list pages."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int
    name: str
    description: str | None = None
    avatar_url: str | None = Field(default=None, alias="avatarUrl")
    status: AgentStatus
    orchestration_mode: AgentOrchestrationMode = Field(
        alias="orchestrationMode",
    )
    provider_instance_id: int | None = Field(
        default=None,
        alias="providerInstanceId",
    )
    provider_model_id: int | None = Field(
        default=None,
        alias="providerModelId",
    )
    model: AgentModelSummaryResp | None = None
    tool_count: int = Field(alias="toolCount")
    knowledge_base_count: int = Field(alias="knowledgeBaseCount")
    tags: list[str]
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class AgentDetailResp(AgentSummaryResp):
    """Agent detail response with full nested configuration."""

    system_prompt: str | None = Field(default=None, alias="systemPrompt")
    opening_message: str | None = Field(default=None, alias="openingMessage")
    model_settings: dict[str, Any] | None = Field(
        default=None,
        alias="modelConfig",
    )
    runtime_config: dict[str, Any] | None = Field(
        default=None,
        alias="runtimeConfig",
    )
    workflow_ref: dict[str, Any] | None = Field(
        default=None,
        alias="workflowRef",
    )
    tools: list[AgentToolBindingResp]
    knowledge_bases: list[AgentKnowledgeBindingResp] = Field(
        alias="knowledgeBases",
    )
    metadata: dict[str, Any] | None = None


class AgentRuntimePreviewResp(BaseModel):
    """UI-safe preview of how conversation will load one agent."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    agent_id: int = Field(alias="agentId")
    name: str
    status: AgentStatus
    orchestration_mode: AgentOrchestrationMode = Field(
        alias="orchestrationMode",
    )
    is_runnable: bool = Field(alias="isRunnable")
    model: AgentModelSummaryResp | None = None
    enabled_tool_ids: list[int] = Field(alias="enabledToolIds")
    enabled_knowledge_base_ids: list[int] = Field(
        alias="enabledKnowledgeBaseIds",
    )
    runtime_config: dict[str, Any] | None = Field(
        default=None,
        alias="runtimeConfig",
    )
    workflow_ref: dict[str, Any] | None = Field(
        default=None,
        alias="workflowRef",
    )
    warnings: list[str]
