"""Tool module request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.responses import PageParams

ToolStatus = Literal["draft", "enabled", "disabled", "archived"]
ToolSourceType = Literal["manual", "openapi"]
ToolHttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
ToolAuthType = Literal["none", "bearer", "api_key_header", "api_key_query"]
ToolParamLocation = Literal["path", "query", "header", "body"]
ToolSchemaType = Literal[
    "string",
    "number",
    "integer",
    "boolean",
    "object",
    "array",
]
ToolExecutionSource = Literal["test", "conversation"]
ToolExecutionStatus = Literal["success", "failed", "timeout"]


class ToolExecutionPreviewResp(BaseModel):
    """Response schema for the legacy tool preview endpoint."""

    module: str
    status: str
    capabilities: list[str]


class ToolListParams(PageParams):
    """Tool list query parameters."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    keyword: str | None = None
    status: ToolStatus | None = None
    source_type: ToolSourceType | None = Field(
        default=None,
        alias="sourceType",
    )
    http_method: ToolHttpMethod | None = Field(
        default=None,
        alias="httpMethod",
    )


class ToolAuthInput(BaseModel):
    """Tool authentication input payload."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    auth_type: ToolAuthType = Field(alias="authType")
    secret_value: str | None = Field(default=None, alias="secretValue")
    header_name: str | None = Field(default=None, alias="headerName")
    query_name: str | None = Field(default=None, alias="queryName")


class ToolAuthResp(BaseModel):
    """Tool authentication response payload without plaintext secret."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    auth_type: ToolAuthType = Field(alias="authType")
    secret_masked: str | None = Field(default=None, alias="secretMasked")
    header_name: str | None = Field(default=None, alias="headerName")
    query_name: str | None = Field(default=None, alias="queryName")
    last_rotated_at: datetime | None = Field(
        default=None,
        alias="lastRotatedAt",
    )


class ToolParameterInput(BaseModel):
    """Tool parameter input definition."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    name: str = Field(min_length=1, max_length=128)
    label: str | None = Field(default=None, max_length=128)
    description: str | None = None
    param_location: ToolParamLocation = Field(alias="paramLocation")
    schema_type: ToolSchemaType = Field(alias="schemaType")
    is_required: bool = Field(default=False, alias="isRequired")
    default_value: Any | None = Field(default=None, alias="defaultValue")
    enum_values: list[Any] | None = Field(default=None, alias="enumValues")
    schema_value: dict[str, Any] | None = Field(default=None, alias="schema")
    sort_order: int = Field(default=0, alias="sortOrder", ge=0)
    metadata: dict[str, Any] | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        """Strip and validate the parameter name."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("参数名称不能为空")
        return stripped


class ToolParameterResp(ToolParameterInput):
    """Tool parameter response definition."""


class ToolBasePayload(BaseModel):
    """Shared create and update payload fields."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    status: ToolStatus = "draft"
    source_type: ToolSourceType = Field(default="manual", alias="sourceType")
    http_method: ToolHttpMethod = Field(alias="httpMethod")
    url: str = Field(min_length=1, max_length=2048)
    timeout_seconds: int = Field(
        default=15,
        alias="timeoutSeconds",
        ge=1,
        le=60,
    )
    headers_template: dict[str, Any] | None = Field(
        default=None,
        alias="headersTemplate",
    )
    query_template: dict[str, Any] | None = Field(
        default=None,
        alias="queryTemplate",
    )
    body_template: dict[str, Any] | None = Field(
        default=None,
        alias="bodyTemplate",
    )
    content_type: str = Field(
        default="application/json",
        alias="contentType",
        max_length=128,
    )
    auth: ToolAuthInput
    parameters: list[ToolParameterInput] = Field(default_factory=list)
    openapi_source: dict[str, Any] | None = Field(
        default=None,
        alias="openapiSource",
    )
    metadata: dict[str, Any] | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        """Strip and validate the tool name."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("工具名称不能为空")
        return stripped

    @field_validator("parameters")
    @classmethod
    def validate_unique_parameters(
        cls,
        parameters: list[ToolParameterInput],
    ) -> list[ToolParameterInput]:
        """Reject duplicate parameter names in the same location."""
        keys = [(item.name, item.param_location) for item in parameters]
        if len(keys) != len(set(keys)):
            raise ValueError("同一工具下参数名称和位置不能重复")
        return parameters


class ToolCreateReq(ToolBasePayload):
    """Create tool request payload."""


class ToolUpdateReq(ToolBasePayload):
    """Update tool request payload."""


class ToolSummaryResp(BaseModel):
    """Tool list item response."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int
    name: str
    description: str | None = None
    status: ToolStatus
    tool_type: str = Field(alias="toolType")
    source_type: ToolSourceType = Field(alias="sourceType")
    http_method: ToolHttpMethod = Field(alias="httpMethod")
    url: str
    auth_type: ToolAuthType = Field(alias="authType")
    parameter_count: int = Field(alias="parameterCount")
    bound_agent_count: int = Field(alias="boundAgentCount")
    last_test_status: str | None = Field(default=None, alias="lastTestStatus")
    last_test_at: datetime | None = Field(default=None, alias="lastTestAt")
    last_test_latency_ms: int | None = Field(
        default=None,
        alias="lastTestLatencyMs",
    )
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class ToolOptionResp(BaseModel):
    """Tool option for Agent forms."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int
    name: str
    description: str | None = None
    status: ToolStatus
    http_method: ToolHttpMethod = Field(alias="httpMethod")
    url: str
    parameter_count: int = Field(alias="parameterCount")


class ToolDetailResp(BaseModel):
    """Aggregated tool detail response."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int
    name: str
    description: str | None = None
    status: ToolStatus
    tool_type: str = Field(alias="toolType")
    source_type: ToolSourceType = Field(alias="sourceType")
    http_method: ToolHttpMethod = Field(alias="httpMethod")
    url: str
    timeout_seconds: int = Field(alias="timeoutSeconds")
    headers_template: dict[str, Any] | None = Field(alias="headersTemplate")
    query_template: dict[str, Any] | None = Field(alias="queryTemplate")
    body_template: dict[str, Any] | None = Field(alias="bodyTemplate")
    content_type: str = Field(alias="contentType")
    auth: ToolAuthResp
    parameters: list[ToolParameterResp]
    openapi_source: dict[str, Any] | None = Field(alias="openapiSource")
    last_test_status: str | None = Field(default=None, alias="lastTestStatus")
    last_test_at: datetime | None = Field(default=None, alias="lastTestAt")
    last_test_latency_ms: int | None = Field(
        default=None,
        alias="lastTestLatencyMs",
    )
    last_error_message: str | None = Field(
        default=None,
        alias="lastErrorMessage",
    )
    metadata: dict[str, Any] | None = None
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class ToolExecuteTestReq(BaseModel):
    """Execute-test request payload."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    parameters: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int | None = Field(
        default=None,
        alias="timeoutSeconds",
        ge=1,
        le=60,
    )


class ToolExecutionHttpRequestResp(BaseModel):
    """UI-safe executed request summary."""

    method: str
    url: str
    headers: dict[str, Any]
    body_preview: str | None = Field(default=None, alias="bodyPreview")


class ToolExecutionHttpResponseResp(BaseModel):
    """UI-safe upstream response summary."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    status_code: int | None = Field(default=None, alias="statusCode")
    headers: dict[str, Any]
    body_preview: str | None = Field(default=None, alias="bodyPreview")


class ToolExecutionResp(BaseModel):
    """Execute-test response payload."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    log_id: int = Field(alias="logId")
    tool_id: int = Field(alias="toolId")
    status: ToolExecutionStatus
    request: ToolExecutionHttpRequestResp
    response: ToolExecutionHttpResponseResp
    latency_ms: int = Field(alias="latencyMs")
    error_code: str | None = Field(default=None, alias="errorCode")
    error_message: str | None = Field(default=None, alias="errorMessage")
    created_at: datetime = Field(alias="createdAt")


class ToolExecutionLogListParams(PageParams):
    """Tool execution log list query parameters."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    source: ToolExecutionSource | None = None
    status: ToolExecutionStatus | None = None


class ToolExecutionLogSummaryResp(BaseModel):
    """Tool execution log list item response."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int
    tool_id: int = Field(alias="toolId")
    source: ToolExecutionSource
    status: ToolExecutionStatus
    request_method: str = Field(alias="requestMethod")
    request_url: str = Field(alias="requestUrl")
    response_status_code: int | None = Field(
        default=None,
        alias="responseStatusCode",
    )
    latency_ms: int = Field(alias="latencyMs")
    error_code: str | None = Field(default=None, alias="errorCode")
    error_message: str | None = Field(default=None, alias="errorMessage")
    created_at: datetime = Field(alias="createdAt")


class OpenApiOperationReq(BaseModel):
    """OpenAPI operation selector."""

    method: ToolHttpMethod
    path: str = Field(min_length=1)


class OpenApiPreviewReq(BaseModel):
    """OpenAPI operation preview request."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    document: dict[str, Any]
    operation: OpenApiOperationReq
    server_url: str | None = Field(default=None, alias="serverUrl")


class OpenApiPreviewResp(BaseModel):
    """OpenAPI operation preview response."""

    draft: ToolCreateReq
    warnings: list[str]
