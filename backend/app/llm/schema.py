"""LLM module request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.responses import PageParams


class ModelPreviewResp(BaseModel):
    """Response schema for the LLM preview endpoint."""

    module: str
    status: str
    capabilities: list[str]


class ProviderAuthSecretInput(BaseModel):
    """Aggregated provider auth input payload."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    auth_type: str = Field(alias="authType")
    secret_value: str | None = Field(default=None, alias="secretValue")
    headers: dict[str, str] | None = None
    query_params: dict[str, str] | None = Field(
        default=None,
        alias="queryParams",
    )
    metadata: dict[str, Any] | None = None
    expires_at: datetime | None = Field(default=None, alias="expiresAt")


class ProviderModelInput(BaseModel):
    """Aggregated provider model input payload."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    model_name: str = Field(alias="modelName", min_length=1, max_length=128)
    display_name: str = Field(alias="displayName", min_length=1, max_length=128)
    description: str | None = None
    status: str = "active"
    is_default: bool = Field(default=False, alias="isDefault")
    sort_order: int = Field(default=0, alias="sortOrder", ge=0)
    supports_chat: bool = Field(default=True, alias="supportsChat")
    supports_stream: bool = Field(default=True, alias="supportsStream")
    supports_tools: bool = Field(default=False, alias="supportsTools")
    supports_structured_output: bool = Field(
        default=False,
        alias="supportsStructuredOutput",
    )
    supports_vision_input: bool = Field(
        default=False,
        alias="supportsVisionInput",
    )
    supports_audio_input: bool = Field(
        default=False,
        alias="supportsAudioInput",
    )
    supports_reasoning: bool = Field(default=False, alias="supportsReasoning")
    supports_embeddings: bool = Field(default=False, alias="supportsEmbeddings")
    context_window: int | None = Field(
        default=None,
        alias="contextWindow",
        ge=0,
    )
    max_output_tokens: int | None = Field(
        default=None,
        alias="maxOutputTokens",
        ge=0,
    )
    max_input_tokens: int | None = Field(
        default=None,
        alias="maxInputTokens",
        ge=0,
    )
    temperature_supported: bool = Field(
        default=True,
        alias="temperatureSupported",
    )
    top_p_supported: bool = Field(default=True, alias="topPSupported")
    tags: list[str] | None = None
    pricing: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class ProviderAdminCreateReq(BaseModel):
    """Create payload for the single-page provider admin view."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    name: str = Field(min_length=1, max_length=128)
    provider_type: str = Field(
        alias="providerType",
        min_length=1,
        max_length=64,
    )
    api_family: str = Field(alias="apiFamily", min_length=1, max_length=64)
    base_url: str = Field(alias="baseUrl", min_length=1, max_length=512)
    status: str = "draft"
    is_default: bool = Field(default=False, alias="isDefault")
    priority: int = Field(default=0, ge=0)
    notes: str | None = None
    metadata: dict[str, Any] | None = None
    auth: ProviderAuthSecretInput
    models: list[ProviderModelInput]

    @field_validator("models")
    @classmethod
    def validate_models(
        cls,
        models: list[ProviderModelInput],
    ) -> list[ProviderModelInput]:
        if not models:
            raise ValueError("至少需要配置一个模型")
        return models


class ProviderAdminUpdateReq(BaseModel):
    """Update payload for the single-page provider admin view."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    name: str = Field(min_length=1, max_length=128)
    provider_type: str = Field(
        alias="providerType",
        min_length=1,
        max_length=64,
    )
    api_family: str = Field(alias="apiFamily", min_length=1, max_length=64)
    base_url: str = Field(alias="baseUrl", min_length=1, max_length=512)
    status: str = "draft"
    is_default: bool = Field(default=False, alias="isDefault")
    priority: int = Field(default=0, ge=0)
    notes: str | None = None
    metadata: dict[str, Any] | None = None
    auth: ProviderAuthSecretInput
    models: list[ProviderModelInput]

    @field_validator("models")
    @classmethod
    def validate_models(
        cls,
        models: list[ProviderModelInput],
    ) -> list[ProviderModelInput]:
        if not models:
            raise ValueError("至少需要配置一个模型")
        return models


class ProviderListParams(PageParams):
    """List query params for provider summaries."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    keyword: str | None = None
    provider_type: str | None = Field(default=None, alias="providerType")
    status: str | None = None


class ProviderAuthSecretResp(BaseModel):
    """Provider auth response payload without plaintext secrets."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    auth_type: str = Field(alias="authType")
    secret_masked: str = Field(alias="secretMasked")
    has_secret: bool = Field(alias="hasSecret")
    headers: dict[str, str] | None = None
    query_params: dict[str, str] | None = Field(
        default=None,
        alias="queryParams",
    )
    metadata: dict[str, Any] | None = None
    expires_at: datetime | None = Field(default=None, alias="expiresAt")
    last_rotated_at: datetime | None = Field(
        default=None,
        alias="lastRotatedAt",
    )


class ProviderModelResp(BaseModel):
    """Provider model response payload."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int
    model_name: str = Field(alias="modelName")
    display_name: str = Field(alias="displayName")
    description: str | None = None
    status: str
    is_default: bool = Field(alias="isDefault")
    sort_order: int = Field(alias="sortOrder")
    supports_chat: bool = Field(alias="supportsChat")
    supports_stream: bool = Field(alias="supportsStream")
    supports_tools: bool = Field(alias="supportsTools")
    supports_structured_output: bool = Field(alias="supportsStructuredOutput")
    supports_vision_input: bool = Field(alias="supportsVisionInput")
    supports_audio_input: bool = Field(alias="supportsAudioInput")
    supports_reasoning: bool = Field(alias="supportsReasoning")
    supports_embeddings: bool = Field(alias="supportsEmbeddings")
    context_window: int | None = Field(default=None, alias="contextWindow")
    max_output_tokens: int | None = Field(default=None, alias="maxOutputTokens")
    max_input_tokens: int | None = Field(default=None, alias="maxInputTokens")
    temperature_supported: bool = Field(alias="temperatureSupported")
    top_p_supported: bool = Field(alias="topPSupported")
    tags: list[str] | None = None
    pricing: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class ProviderHealthStatusResp(BaseModel):
    """Provider health response payload."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    health_state: str = Field(alias="healthState")
    auth_state: str = Field(alias="authState")
    connectivity_state: str = Field(alias="connectivityState")
    inference_state: str = Field(alias="inferenceState")
    last_check_at: datetime | None = Field(default=None, alias="lastCheckAt")
    last_success_at: datetime | None = Field(
        default=None,
        alias="lastSuccessAt",
    )
    last_failure_at: datetime | None = Field(
        default=None,
        alias="lastFailureAt",
    )
    consecutive_failures: int = Field(alias="consecutiveFailures")
    latency_ms_p50: int | None = Field(default=None, alias="latencyMsP50")
    latency_ms_p95: int | None = Field(default=None, alias="latencyMsP95")
    last_error_code: str | None = Field(default=None, alias="lastErrorCode")
    last_error_message: str | None = Field(
        default=None,
        alias="lastErrorMessage",
    )
    last_error_at: datetime | None = Field(default=None, alias="lastErrorAt")


class ProviderSummaryResp(BaseModel):
    """Summary response used by the provider list page."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int
    name: str
    provider_type: str = Field(alias="providerType")
    api_family: str = Field(alias="apiFamily")
    base_url: str = Field(alias="baseUrl")
    status: str
    is_default: bool = Field(alias="isDefault")
    priority: int
    notes: str | None = None
    metadata: dict[str, Any] | None = None
    model_count: int = Field(alias="modelCount")
    auth: ProviderAuthSecretResp | None = None
    default_model: ProviderModelResp | None = Field(
        default=None,
        alias="defaultModel",
    )
    health: ProviderHealthStatusResp | None = None
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class ProviderDetailResp(ProviderSummaryResp):
    """Detailed provider response with nested models."""

    models: list[ProviderModelResp]


class ProviderConnectionTestResp(BaseModel):
    """Connection test response payload."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    provider_id: int = Field(alias="providerId")
    health_state: str = Field(alias="healthState")
    auth_state: str = Field(alias="authState")
    connectivity_state: str = Field(alias="connectivityState")
    inference_state: str = Field(alias="inferenceState")
    http_status_code: int = Field(alias="httpStatusCode")
    latency_ms: int | None = Field(default=None, alias="latencyMs")
    message: str
    checked_at: datetime = Field(alias="checkedAt")


class ProviderRuntimeConfigResp(BaseModel):
    """UI-safe runtime config preview for one provider model."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    provider_id: int = Field(alias="providerId")
    provider_type: str = Field(alias="providerType")
    api_family: str = Field(alias="apiFamily")
    model_name: str = Field(alias="modelName")
    litellm_model: str = Field(alias="litellmModel")
    api_base: str = Field(alias="apiBase")
    api_key_masked: str = Field(alias="apiKeyMasked")
    extra_headers: dict[str, str] = Field(alias="extraHeaders")
    query_params: dict[str, str] = Field(alias="queryParams")


class ProviderInvokeTestReq(BaseModel):
    """Prompt payload for a real LiteLLM invocation test."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    prompt: str = Field(min_length=1, max_length=8000)
    model_name: str | None = Field(default=None, alias="modelName")
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(
        default=None,
        alias="maxTokens",
        ge=1,
        le=32768,
    )


class ProviderInvokeTestResp(BaseModel):
    """Response payload for a real LiteLLM invocation test."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    provider_id: int = Field(alias="providerId")
    model_name: str = Field(alias="modelName")
    litellm_model: str = Field(alias="litellmModel")
    output_text: str = Field(alias="outputText")
    latency_ms: int = Field(alias="latencyMs")
