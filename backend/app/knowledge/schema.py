"""Knowledge module request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.responses import PageParams

KnowledgeBaseStatus = Literal["draft", "enabled", "archived"]
KnowledgeVisibility = Literal["private", "workspace"]
DocumentStatus = Literal[
    "uploaded",
    "processing",
    "completed",
    "failed",
    "disabled",
]


class KnowledgeRetrievalPreviewResp(BaseModel):
    """Response schema for the knowledge preview endpoint."""

    module: str
    status: str
    capabilities: list[str]


class KnowledgeBaseListParams(PageParams):
    """Knowledge-base list query parameters."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    keyword: str | None = None
    status: KnowledgeBaseStatus | None = None
    visibility: KnowledgeVisibility | None = None


class KnowledgeBaseCreateReq(BaseModel):
    """Create payload for a knowledge base."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    status: KnowledgeBaseStatus = "draft"
    visibility: KnowledgeVisibility = "private"
    chunk_size: int = Field(default=800, alias="chunkSize", gt=0)
    chunk_overlap: int = Field(default=120, alias="chunkOverlap", ge=0)
    default_top_k: int = Field(default=5, alias="defaultTopK", gt=0)
    default_score_threshold: float = Field(
        default=0.65,
        alias="defaultScoreThreshold",
        ge=0,
        le=1,
    )
    metadata: dict[str, Any] | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("知识库名称不能为空")
        return stripped

    @field_validator("chunk_overlap")
    @classmethod
    def validate_overlap(cls, value: int, info) -> int:  # type: ignore[no-untyped-def]
        chunk_size = info.data.get("chunk_size")
        if isinstance(chunk_size, int) and value >= chunk_size:
            raise ValueError("切片重叠长度必须小于切片长度")
        return value


class KnowledgeBaseUpdateReq(KnowledgeBaseCreateReq):
    """Update payload for a knowledge base."""


class KnowledgeBaseSummaryResp(BaseModel):
    """List card response for a knowledge base."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int
    name: str
    description: str | None = None
    status: KnowledgeBaseStatus
    visibility: KnowledgeVisibility
    document_count: int = Field(alias="documentCount")
    chunk_count: int = Field(alias="chunkCount")
    last_indexed_at: datetime | None = Field(
        default=None,
        alias="lastIndexedAt",
    )
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class KnowledgeHealthResp(BaseModel):
    """UI health summary for the knowledge workbench."""

    score: int
    label: str
    suggestion: str | None = None


class KnowledgeBoundAgentResp(BaseModel):
    """Agent binding summary shown on knowledge detail pages."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    agent_id: int = Field(alias="agentId")
    agent_name: str = Field(alias="agentName")
    is_enabled: bool = Field(alias="isEnabled")
    top_k: int | None = Field(default=None, alias="topK")
    score_threshold: float | None = Field(
        default=None,
        alias="scoreThreshold",
    )


class KnowledgeBaseDetailResp(KnowledgeBaseSummaryResp):
    """Aggregated workbench detail response."""

    embedding_model: str = Field(alias="embeddingModel")
    embedding_dimensions: int = Field(alias="embeddingDimensions")
    chunk_size: int = Field(alias="chunkSize")
    chunk_overlap: int = Field(alias="chunkOverlap")
    default_top_k: int = Field(alias="defaultTopK")
    default_score_threshold: float = Field(alias="defaultScoreThreshold")
    processing_document_count: int = Field(alias="processingDocumentCount")
    failed_document_count: int = Field(alias="failedDocumentCount")
    health: KnowledgeHealthResp
    bound_agents: list[KnowledgeBoundAgentResp] = Field(alias="boundAgents")
    metadata: dict[str, Any] | None = None


class KnowledgeBaseOptionResp(BaseModel):
    """Knowledge-base option for reference fields."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int
    name: str
    status: KnowledgeBaseStatus
    document_count: int = Field(alias="documentCount")
    chunk_count: int = Field(alias="chunkCount")


class KnowledgeDocumentListParams(PageParams):
    """Document list query parameters."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    keyword: str | None = None
    status: DocumentStatus | None = None


class KnowledgeDocumentResp(BaseModel):
    """Document response payload."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int
    knowledge_base_id: int = Field(alias="knowledgeBaseId")
    filename: str
    file_ext: str = Field(alias="fileExt")
    mime_type: str | None = Field(default=None, alias="mimeType")
    file_size_bytes: int = Field(alias="fileSizeBytes")
    status: DocumentStatus
    process_stage: str = Field(alias="processStage")
    chunk_count: int = Field(alias="chunkCount")
    token_count: int = Field(alias="tokenCount")
    error_code: str | None = Field(default=None, alias="errorCode")
    error_message: str | None = Field(default=None, alias="errorMessage")
    started_at: datetime | None = Field(default=None, alias="startedAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    metadata: dict[str, Any] | None = None


class RetrievalTestReq(BaseModel):
    """Retrieval test request payload."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    query: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, alias="topK", gt=0, le=20)
    score_threshold: float | None = Field(
        default=None,
        alias="scoreThreshold",
        ge=0,
        le=1,
    )

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("检索问题不能为空")
        return stripped


class RetrievalHitResp(BaseModel):
    """One retrieval hit shown in test or conversation previews."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    chunk_id: int = Field(alias="chunkId")
    document_id: int = Field(alias="documentId")
    document_name: str = Field(alias="documentName")
    content: str
    score: float
    page_number: int | None = Field(default=None, alias="pageNumber")
    section_title: str | None = Field(default=None, alias="sectionTitle")


class RetrievalTestResp(BaseModel):
    """Retrieval test response payload."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    query: str
    top_k: int = Field(alias="topK")
    score_threshold: float = Field(alias="scoreThreshold")
    latency_ms: int = Field(alias="latencyMs")
    hits: list[RetrievalHitResp]


class ConversationRetrievalResp(BaseModel):
    """Internal retrieval response used by conversation orchestration."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    hits: list[RetrievalHitResp]
    context_text: str = Field(alias="contextText")
