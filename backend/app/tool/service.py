"""Tool module business services."""

from __future__ import annotations

import json
from dataclasses import dataclass
from ipaddress import ip_address
from time import perf_counter
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from fastapi import status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agent.model import AgentToolBinding
from app.core.database import utc_now
from app.core.errors import CommonErrorCode
from app.core.exceptions import BizException
from app.core.responses import PageResult
from app.llm.provider import (
    ProviderSecretCodec,
    ProviderSecretPayload,
    fingerprint_secret,
    mask_secret,
)
from app.tool.errors import ToolErrorCode
from app.tool.model import Tool, ToolAuthSecret, ToolExecutionLog, ToolParameter
from app.tool.schema import (
    OpenApiPreviewReq,
    OpenApiPreviewResp,
    ToolAuthInput,
    ToolAuthResp,
    ToolCreateReq,
    ToolDetailResp,
    ToolExecuteTestReq,
    ToolExecutionHttpRequestResp,
    ToolExecutionHttpResponseResp,
    ToolExecutionLogListParams,
    ToolExecutionLogSummaryResp,
    ToolExecutionPreviewResp,
    ToolExecutionResp,
    ToolListParams,
    ToolOptionResp,
    ToolParameterInput,
    ToolParameterResp,
    ToolSummaryResp,
    ToolUpdateReq,
)

PREVIEW_LIMIT = 8192
SAFE_HEADER_PREFIXES = {"accept", "content-type", "user-agent"}


@dataclass(frozen=True, slots=True)
class PreparedRequest:
    """Rendered outbound request data."""

    method: str
    url: str
    headers: dict[str, str]
    params: dict[str, Any]
    json_body: dict[str, Any] | None


class ToolService:
    """Tool service with aggregated CRUD and test execution."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        secret_codec: ProviderSecretCodec | None = None,
    ) -> None:
        """Initialize the tool service."""
        self.db = db
        self.secret_codec = secret_codec or ProviderSecretCodec()

    async def preview(self) -> ToolExecutionPreviewResp:
        """Return the legacy tool module preview payload."""
        return ToolExecutionPreviewResp(
            module="tool",
            status="skeleton_ready",
            capabilities=[
                "OpenAPI 工具注册",
                "HTTP 工具调用",
                "工具执行结果透传",
            ],
        )

    async def list_tools(
        self,
        params: ToolListParams,
    ) -> PageResult[ToolSummaryResp]:
        """Return paginated tool summaries."""
        filters = [Tool.deleted_at.is_(None)]
        if params.keyword:
            keyword = f"%{params.keyword.strip()}%"
            filters.append(
                or_(
                    Tool.name.ilike(keyword),
                    Tool.description.ilike(keyword),
                    Tool.url.ilike(keyword),
                )
            )
        if params.status:
            filters.append(Tool.status == params.status)
        else:
            filters.append(Tool.status != "archived")
        if params.source_type:
            filters.append(Tool.source_type == params.source_type)
        if params.http_method:
            filters.append(Tool.http_method == params.http_method)

        total = int(
            (
                await self.db.execute(
                    select(func.count()).select_from(Tool).where(*filters)
                )
            ).scalar_one()
        )
        statement = (
            select(Tool)
            .where(*filters)
            .options(
                selectinload(Tool.auth_secret),
                selectinload(Tool.parameters),
            )
            .order_by(Tool.updated_at.desc(), Tool.id.desc())
            .offset(params.offset)
            .limit(params.page_size)
        )
        tools = list((await self.db.scalars(statement)).all())
        bound_counts = await self._load_bound_agent_counts(
            [tool.id for tool in tools]
        )
        return PageResult.create(
            items=[
                self._build_summary(tool, bound_counts=bound_counts)
                for tool in tools
            ],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    async def list_options(
        self,
        *,
        keyword: str | None = None,
        status_value: str | None = "enabled",
    ) -> list[ToolOptionResp]:
        """Return tool options for Agent forms."""
        filters = [Tool.deleted_at.is_(None)]
        if status_value:
            filters.append(Tool.status == status_value)
        if keyword:
            pattern = f"%{keyword.strip()}%"
            filters.append(
                or_(Tool.name.ilike(pattern), Tool.url.ilike(pattern))
            )
        statement = (
            select(Tool)
            .where(*filters)
            .options(selectinload(Tool.parameters))
            .order_by(Tool.updated_at.desc(), Tool.id.desc())
            .limit(100)
        )
        return [
            self._build_option(tool)
            for tool in await self.db.scalars(statement)
        ]

    async def get_tool(self, tool_id: int) -> ToolDetailResp:
        """Return one tool detail."""
        tool = await self._get_tool_or_raise(tool_id)
        return self._build_detail(tool)

    async def create_tool(
        self,
        payload: ToolCreateReq,
        *,
        user_id: int,
    ) -> ToolDetailResp:
        """Create one aggregated tool."""
        self._validate_tool_payload(payload)
        await self._ensure_name_unique(payload.name, user_id=user_id)
        tool = Tool(
            owner_user_id=user_id,
            name=payload.name,
            description=payload.description,
            status=payload.status,
            tool_type="http",
            source_type=payload.source_type,
            http_method=payload.http_method,
            url=payload.url,
            timeout_seconds=payload.timeout_seconds,
            headers_template_json=payload.headers_template,
            query_template_json=payload.query_template,
            body_template_json=payload.body_template,
            content_type=payload.content_type,
            openapi_source_json=payload.openapi_source,
            metadata_json=payload.metadata,
        )
        self.db.add(tool)
        await self.db.flush()
        self.db.add(self._build_auth(tool.id, payload.auth))
        self.db.add_all(
            [
                self._build_parameter(tool.id, item)
                for item in payload.parameters
            ]
        )
        await self.db.commit()
        return await self.get_tool(tool.id)

    async def update_tool(
        self,
        tool_id: int,
        payload: ToolUpdateReq,
        *,
        user_id: int,
    ) -> ToolDetailResp:
        """Update one aggregated tool."""
        tool = await self._get_tool_or_raise(tool_id)
        self._validate_tool_payload(payload)
        await self._ensure_name_unique(
            payload.name,
            user_id=user_id,
            exclude_id=tool_id,
        )
        tool.name = payload.name
        tool.description = payload.description
        tool.status = payload.status
        tool.source_type = payload.source_type
        tool.http_method = payload.http_method
        tool.url = payload.url
        tool.timeout_seconds = payload.timeout_seconds
        tool.headers_template_json = payload.headers_template
        tool.query_template_json = payload.query_template
        tool.body_template_json = payload.body_template
        tool.content_type = payload.content_type
        tool.openapi_source_json = payload.openapi_source
        tool.metadata_json = payload.metadata
        tool.version += 1
        await self._replace_auth(tool, payload.auth)
        await self._replace_parameters(tool, payload.parameters)
        await self.db.commit()
        self.db.expire_all()
        return await self.get_tool(tool_id)

    async def delete_tool(self, tool_id: int) -> None:
        """Soft-delete one tool if it is not bound by active Agents."""
        tool = await self._get_tool_or_raise(tool_id)
        bound_count = await self._bound_agent_count(tool_id)
        if bound_count > 0:
            raise BizException(
                code=ToolErrorCode.TOOL_IN_USE,
                message="工具已被 Agent 绑定，请先解绑后再删除",
                http_status=status.HTTP_400_BAD_REQUEST,
            )
        for auth in [tool.auth_secret] if tool.auth_secret else []:
            auth.soft_delete()
            auth.version += 1
        for parameter in self._active_parameters(tool):
            parameter.soft_delete()
            parameter.version += 1
        tool.soft_delete()
        tool.version += 1
        await self.db.commit()

    async def execute_test(
        self,
        tool_id: int,
        payload: ToolExecuteTestReq,
        *,
        user_id: int,
    ) -> ToolExecutionResp:
        """Execute one tool against its configured HTTP target."""
        tool = await self._get_tool_or_raise(tool_id)
        if tool.status not in {"draft", "enabled"}:
            raise BizException(
                code=ToolErrorCode.INVALID_TOOL_CONFIGURATION,
                message="当前工具状态不允许测试执行",
                http_status=status.HTTP_400_BAD_REQUEST,
            )
        prepared = self._prepare_request(tool, payload.parameters)
        start = perf_counter()
        try:
            async with httpx.AsyncClient(
                timeout=payload.timeout_seconds or tool.timeout_seconds,
                trust_env=False,
            ) as client:
                request = client.build_request(
                    prepared.method,
                    prepared.url,
                    headers=prepared.headers,
                    params=prepared.params,
                    json=prepared.json_body,
                )
                response = await client.send(request)
        except httpx.TimeoutException as exc:
            latency_ms = int((perf_counter() - start) * 1000)
            return await self._save_execution(
                tool,
                prepared,
                user_id=user_id,
                status_value="timeout",
                latency_ms=latency_ms,
                error_code="timeout",
                error_message=str(exc),
            )
        except httpx.TransportError as exc:
            latency_ms = int((perf_counter() - start) * 1000)
            return await self._save_execution(
                tool,
                prepared,
                user_id=user_id,
                status_value="failed",
                latency_ms=latency_ms,
                error_code="transport_error",
                error_message=str(exc),
            )

        latency_ms = int((perf_counter() - start) * 1000)
        status_value = "success" if response.is_success else "failed"
        return await self._save_execution(
            tool,
            prepared,
            user_id=user_id,
            status_value=status_value,
            latency_ms=latency_ms,
            response=response,
        )

    async def execute_conversation(
        self,
        tool_id: int,
        parameters: dict[str, Any],
        *,
        user_id: int,
        conversation_id: int,
        run_id: int,
        tool_call_id: str,
        runtime_tool_name: str,
    ) -> ToolExecutionResp:
        """Execute one enabled tool from a conversation run."""
        tool = await self._get_tool_or_raise(tool_id)
        if tool.status != "enabled":
            raise BizException(
                code=ToolErrorCode.INVALID_TOOL_CONFIGURATION,
                message="当前工具状态不允许会话调用",
                http_status=status.HTTP_400_BAD_REQUEST,
            )
        prepared = self._prepare_request(tool, parameters)
        metadata = {
            "toolCallId": tool_call_id,
            "runtimeToolName": runtime_tool_name,
            "argumentsPreview": self._mask_mapping(parameters),
        }
        start = perf_counter()
        try:
            async with httpx.AsyncClient(
                timeout=tool.timeout_seconds,
                trust_env=False,
            ) as client:
                request = client.build_request(
                    prepared.method,
                    prepared.url,
                    headers=prepared.headers,
                    params=prepared.params,
                    json=prepared.json_body,
                )
                response = await client.send(request)
        except httpx.TimeoutException as exc:
            latency_ms = int((perf_counter() - start) * 1000)
            return await self._save_execution(
                tool,
                prepared,
                user_id=user_id,
                status_value="timeout",
                latency_ms=latency_ms,
                source="conversation",
                conversation_id=conversation_id,
                run_id=run_id,
                metadata=metadata,
                update_tool_health=False,
                error_code="timeout",
                error_message=str(exc),
            )
        except httpx.TransportError as exc:
            latency_ms = int((perf_counter() - start) * 1000)
            return await self._save_execution(
                tool,
                prepared,
                user_id=user_id,
                status_value="failed",
                latency_ms=latency_ms,
                source="conversation",
                conversation_id=conversation_id,
                run_id=run_id,
                metadata=metadata,
                update_tool_health=False,
                error_code="transport_error",
                error_message=str(exc),
            )

        latency_ms = int((perf_counter() - start) * 1000)
        status_value = "success" if response.is_success else "failed"
        return await self._save_execution(
            tool,
            prepared,
            user_id=user_id,
            status_value=status_value,
            latency_ms=latency_ms,
            source="conversation",
            conversation_id=conversation_id,
            run_id=run_id,
            metadata=metadata,
            update_tool_health=False,
            response=response,
            error_code=None if response.is_success else "http_error",
            error_message=None
            if response.is_success
            else f"上游接口返回 {response.status_code}",
        )

    async def list_execution_logs(
        self,
        tool_id: int,
        params: ToolExecutionLogListParams,
    ) -> PageResult[ToolExecutionLogSummaryResp]:
        """Return execution logs for one tool."""
        await self._get_tool_or_raise(tool_id)
        filters = [
            ToolExecutionLog.tool_id == tool_id,
            ToolExecutionLog.deleted_at.is_(None),
        ]
        if params.source:
            filters.append(ToolExecutionLog.source == params.source)
        if params.status:
            filters.append(ToolExecutionLog.status == params.status)
        total = int(
            (
                await self.db.execute(
                    select(func.count())
                    .select_from(ToolExecutionLog)
                    .where(*filters)
                )
            ).scalar_one()
        )
        statement = (
            select(ToolExecutionLog)
            .where(*filters)
            .order_by(ToolExecutionLog.created_at.desc())
            .offset(params.offset)
            .limit(params.page_size)
        )
        return PageResult.create(
            items=[
                self._build_log_summary(log)
                for log in await self.db.scalars(statement)
            ],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    async def preview_openapi(
        self,
        payload: OpenApiPreviewReq,
    ) -> OpenApiPreviewResp:
        """Parse one OpenAPI operation into an editable tool draft."""
        document = payload.document
        if not str(document.get("openapi", "")).startswith("3."):
            raise BizException(
                code=ToolErrorCode.INVALID_OPENAPI_SCHEMA,
                message="仅支持 OpenAPI 3.x 文档",
                http_status=status.HTTP_400_BAD_REQUEST,
            )
        path_item = (document.get("paths") or {}).get(payload.operation.path)
        operation = (
            path_item or {}
        ).get(payload.operation.method.lower())
        if not isinstance(operation, dict):
            raise BizException(
                code=ToolErrorCode.INVALID_OPENAPI_SCHEMA,
                message="OpenAPI operation 不存在",
                http_status=status.HTTP_400_BAD_REQUEST,
            )
        server_url = payload.server_url or self._first_server_url(document)
        url = urljoin(
            server_url.rstrip("/") + "/",
            payload.operation.path.lstrip("/"),
        )
        parameters = self._parameters_from_openapi(operation)
        query_template = {
            item.name: f"{{{{{item.name}}}}}"
            for item in parameters
            if item.param_location == "query"
        }
        draft = ToolCreateReq(
            name=(
                operation.get("summary")
                or operation.get("operationId")
                or "未命名工具"
            ),
            description=(
                operation.get("description") or operation.get("summary")
            ),
            status="draft",
            sourceType="openapi",
            httpMethod=payload.operation.method,
            url=url,
            timeoutSeconds=15,
            headersTemplate={"Accept": "application/json"},
            queryTemplate=query_template or None,
            bodyTemplate=None,
            contentType="application/json",
            auth=ToolAuthInput(authType="none"),
            parameters=parameters,
            openapiSource={
                "title": (document.get("info") or {}).get("title"),
                "version": (document.get("info") or {}).get("version"),
                "operationId": operation.get("operationId"),
                "path": payload.operation.path,
                "method": payload.operation.method,
                "serverUrl": server_url,
            },
            metadata=None,
        )
        return OpenApiPreviewResp(draft=draft, warnings=[])

    async def _get_tool_or_raise(self, tool_id: int) -> Tool:
        statement = (
            select(Tool)
            .where(Tool.id == tool_id, Tool.deleted_at.is_(None))
            .options(
                selectinload(Tool.auth_secret),
                selectinload(Tool.parameters),
            )
        )
        tool = await self.db.scalar(statement)
        if tool is None:
            raise BizException(
                code=ToolErrorCode.TOOL_NOT_FOUND,
                message="工具不存在",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        return tool

    async def _ensure_name_unique(
        self,
        name: str,
        *,
        user_id: int,
        exclude_id: int | None = None,
    ) -> None:
        filters = [
            Tool.owner_user_id == user_id,
            Tool.name == name,
            Tool.deleted_at.is_(None),
        ]
        if exclude_id is not None:
            filters.append(Tool.id != exclude_id)
        exists = await self.db.scalar(select(Tool.id).where(*filters).limit(1))
        if exists is not None:
            raise BizException(
                code=CommonErrorCode.RESOURCE_ALREADY_EXISTS,
                message="工具名称已存在",
                http_status=status.HTTP_409_CONFLICT,
            )

    def _validate_tool_payload(
        self,
        payload: ToolCreateReq | ToolUpdateReq,
    ) -> None:
        parsed = urlparse(payload.url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise BizException(
                code=ToolErrorCode.INVALID_TOOL_CONFIGURATION,
                message="工具 URL 必须是合法 http/https 地址",
                http_status=status.HTTP_400_BAD_REQUEST,
            )
        self._validate_safe_url(payload.url)
        if (
            payload.auth.auth_type == "api_key_header"
            and not payload.auth.header_name
        ):
            raise BizException(
                code=ToolErrorCode.INVALID_TOOL_CONFIGURATION,
                message="Header API Key 必须填写 Header 名称",
                http_status=status.HTTP_400_BAD_REQUEST,
            )
        if (
            payload.auth.auth_type == "api_key_query"
            and not payload.auth.query_name
        ):
            raise BizException(
                code=ToolErrorCode.INVALID_TOOL_CONFIGURATION,
                message="Query API Key 必须填写 Query 名称",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

    def _build_auth(
        self,
        tool_id: int,
        payload: ToolAuthInput,
    ) -> ToolAuthSecret:
        metadata = {
            "headerName": payload.header_name,
            "queryName": payload.query_name,
        }
        if payload.auth_type == "none" or not payload.secret_value:
            return ToolAuthSecret(
                tool_id=tool_id,
                auth_type=payload.auth_type,
                metadata_json=metadata,
            )
        ciphertext = self.secret_codec.encrypt(
            ProviderSecretPayload(
                secret_value=payload.secret_value,
                metadata=metadata,
            )
        )
        return ToolAuthSecret(
            tool_id=tool_id,
            auth_type=payload.auth_type,
            secret_ciphertext=ciphertext,
            secret_masked=mask_secret(payload.secret_value),
            secret_fingerprint=fingerprint_secret(payload.secret_value),
            encryption_key_version="v1",
            last_rotated_at=utc_now(),
            metadata_json=metadata,
        )

    async def _replace_auth(self, tool: Tool, payload: ToolAuthInput) -> None:
        current = tool.auth_secret
        if payload.secret_value is None and current is not None:
            current.auth_type = payload.auth_type
            current.metadata_json = {
                "headerName": payload.header_name,
                "queryName": payload.query_name,
            }
            current.version += 1
            return
        if current is not None:
            current.soft_delete()
            current.version += 1
            await self.db.flush()
        self.db.add(self._build_auth(tool.id, payload))

    def _build_parameter(
        self,
        tool_id: int,
        payload: ToolParameterInput,
    ) -> ToolParameter:
        return ToolParameter(
            tool_id=tool_id,
            name=payload.name,
            label=payload.label,
            description=payload.description,
            param_location=payload.param_location,
            schema_type=payload.schema_type,
            is_required=payload.is_required,
            default_value_json=payload.default_value,
            enum_values_json=payload.enum_values,
            schema_json=payload.schema_value,
            sort_order=payload.sort_order,
            metadata_json=payload.metadata,
        )

    async def _replace_parameters(
        self,
        tool: Tool,
        parameters: list[ToolParameterInput],
    ) -> None:
        for parameter in self._active_parameters(tool):
            parameter.soft_delete()
            parameter.version += 1
        self.db.add_all(
            [self._build_parameter(tool.id, item) for item in parameters]
        )

    def _prepare_request(
        self,
        tool: Tool,
        values: dict[str, Any],
    ) -> PreparedRequest:
        for parameter in self._active_parameters(tool):
            if parameter.is_required and parameter.name not in values:
                raise BizException(
                    code=CommonErrorCode.VALIDATION_ERROR,
                    message=f"缺少必填参数: {parameter.name}",
                    http_status=status.HTTP_400_BAD_REQUEST,
                )
        url = self._render_template(tool.url, values)
        self._validate_safe_url(url)
        headers = {
            str(key): str(self._render_value(value, values))
            for key, value in (tool.headers_template_json or {}).items()
        }
        params = {
            str(key): self._render_value(value, values)
            for key, value in (tool.query_template_json or {}).items()
        }
        body = (
            self._render_json_template(tool.body_template_json, values)
            if tool.body_template_json is not None
            else None
        )
        self._apply_auth(tool, headers, params)
        return PreparedRequest(
            method=tool.http_method,
            url=url,
            headers=headers,
            params=params,
            json_body=body,
        )

    def _apply_auth(
        self,
        tool: Tool,
        headers: dict[str, str],
        params: dict[str, Any],
    ) -> None:
        auth = tool.auth_secret
        if (
            auth is None
            or auth.auth_type == "none"
            or not auth.secret_ciphertext
        ):
            return
        payload = self.secret_codec.decrypt(auth.secret_ciphertext)
        secret = payload.secret_value
        metadata = auth.metadata_json or {}
        if auth.auth_type == "bearer":
            headers["Authorization"] = f"Bearer {secret}"
        elif auth.auth_type == "api_key_header":
            headers[str(metadata.get("headerName") or "X-API-Key")] = secret
        elif auth.auth_type == "api_key_query":
            params[str(metadata.get("queryName") or "api_key")] = secret

    def _validate_safe_url(self, url: str) -> None:
        parsed = urlparse(url)
        host = parsed.hostname
        if host is None:
            raise BizException(
                code=ToolErrorCode.INVALID_TOOL_CONFIGURATION,
                message="工具 URL 必须包含合法域名或 IP",
                http_status=status.HTTP_400_BAD_REQUEST,
            )
        normalized_host = host.strip().lower()
        if normalized_host in {"localhost", "metadata.google.internal"}:
            raise BizException(
                code=ToolErrorCode.TOOL_SECURITY_BLOCKED,
                message="目标 URL 被安全策略拦截",
                http_status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            address = ip_address(normalized_host)
        except ValueError:
            return
        if (
            address.is_loopback
            or address.is_link_local
            or address.is_private
            or address.is_unspecified
            or address.is_reserved
        ):
            raise BizException(
                code=ToolErrorCode.TOOL_SECURITY_BLOCKED,
                message="目标 URL 被安全策略拦截",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

    async def _save_execution(
        self,
        tool: Tool,
        prepared: PreparedRequest,
        *,
        user_id: int,
        status_value: str,
        latency_ms: int,
        source: str = "test",
        conversation_id: int | None = None,
        run_id: int | None = None,
        metadata: dict[str, Any] | None = None,
        update_tool_health: bool = True,
        response: httpx.Response | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> ToolExecutionResp:
        response_headers = (
            dict(response.headers) if response is not None else {}
        )
        response_text = response.text if response is not None else None
        log = ToolExecutionLog(
            tool_id=tool.id,
            executor_user_id=user_id,
            conversation_id=conversation_id,
            run_id=run_id,
            source=source,
            status=status_value,
            request_method=prepared.method,
            request_url=str(httpx.URL(prepared.url, params=prepared.params)),
            request_headers_json=self._mask_headers(prepared.headers),
            request_body_preview=self._preview(prepared.json_body),
            response_status_code=(
                response.status_code if response is not None else None
            ),
            response_headers_json=self._safe_headers(response_headers),
            response_body_preview=self._preview(response_text),
            latency_ms=latency_ms,
            error_code=error_code,
            error_message=error_message,
            metadata_json=metadata,
        )
        self.db.add(log)
        if update_tool_health:
            tool.last_test_status = status_value
            tool.last_test_at = utc_now()
            tool.last_test_latency_ms = latency_ms
            tool.last_error_message = error_message
            tool.version += 1
        await self.db.commit()
        await self.db.refresh(log)
        return ToolExecutionResp(
            logId=log.id,
            toolId=tool.id,
            status=status_value,  # type: ignore[arg-type]
            request=ToolExecutionHttpRequestResp(
                method=prepared.method,
                url=log.request_url,
                headers=log.request_headers_json or {},
                bodyPreview=log.request_body_preview,
            ),
            response=ToolExecutionHttpResponseResp(
                statusCode=log.response_status_code,
                headers=log.response_headers_json or {},
                bodyPreview=log.response_body_preview,
            ),
            latencyMs=latency_ms,
            errorCode=error_code,
            errorMessage=error_message,
            createdAt=log.created_at,
        )

    def _build_detail(self, tool: Tool) -> ToolDetailResp:
        return ToolDetailResp(
            id=tool.id,
            name=tool.name,
            description=tool.description,
            status=tool.status,  # type: ignore[arg-type]
            toolType=tool.tool_type,
            sourceType=tool.source_type,
            httpMethod=tool.http_method,
            url=tool.url,
            timeoutSeconds=tool.timeout_seconds,
            headersTemplate=tool.headers_template_json,
            queryTemplate=tool.query_template_json,
            bodyTemplate=tool.body_template_json,
            contentType=tool.content_type,
            auth=self._build_auth_response(tool.auth_secret),
            parameters=[
                self._build_parameter_response(item)
                for item in self._active_parameters(tool)
            ],
            openapiSource=tool.openapi_source_json,
            lastTestStatus=tool.last_test_status,
            lastTestAt=tool.last_test_at,
            lastTestLatencyMs=tool.last_test_latency_ms,
            lastErrorMessage=tool.last_error_message,
            metadata=tool.metadata_json,
            createdAt=tool.created_at,
            updatedAt=tool.updated_at,
        )

    def _build_summary(
        self,
        tool: Tool,
        *,
        bound_counts: dict[int, int],
    ) -> ToolSummaryResp:
        return ToolSummaryResp(
            id=tool.id,
            name=tool.name,
            description=tool.description,
            status=tool.status,  # type: ignore[arg-type]
            toolType=tool.tool_type,
            sourceType=tool.source_type,
            httpMethod=tool.http_method,
            url=tool.url,
            authType=(
                tool.auth_secret.auth_type if tool.auth_secret else "none"
            ),
            parameterCount=len(self._active_parameters(tool)),
            boundAgentCount=bound_counts.get(tool.id, 0),
            lastTestStatus=tool.last_test_status,
            lastTestAt=tool.last_test_at,
            lastTestLatencyMs=tool.last_test_latency_ms,
            createdAt=tool.created_at,
            updatedAt=tool.updated_at,
        )

    def _build_option(self, tool: Tool) -> ToolOptionResp:
        return ToolOptionResp(
            id=tool.id,
            name=tool.name,
            description=tool.description,
            status=tool.status,  # type: ignore[arg-type]
            httpMethod=tool.http_method,
            url=tool.url,
            parameterCount=len(self._active_parameters(tool)),
        )

    def _build_auth_response(
        self,
        auth: ToolAuthSecret | None,
    ) -> ToolAuthResp:
        metadata = auth.metadata_json if auth is not None else {}
        return ToolAuthResp(
            authType=(auth.auth_type if auth is not None else "none"),
            secretMasked=(auth.secret_masked if auth is not None else None),
            headerName=(metadata or {}).get("headerName"),
            queryName=(metadata or {}).get("queryName"),
            lastRotatedAt=(auth.last_rotated_at if auth is not None else None),
        )

    def _build_parameter_response(
        self,
        parameter: ToolParameter,
    ) -> ToolParameterResp:
        return ToolParameterResp(
            name=parameter.name,
            label=parameter.label,
            description=parameter.description,
            paramLocation=parameter.param_location,
            schemaType=parameter.schema_type,
            isRequired=parameter.is_required,
            defaultValue=parameter.default_value_json,
            enumValues=parameter.enum_values_json,
            schema=parameter.schema_json,
            sortOrder=parameter.sort_order,
            metadata=parameter.metadata_json,
        )

    def _build_log_summary(
        self,
        log: ToolExecutionLog,
    ) -> ToolExecutionLogSummaryResp:
        return ToolExecutionLogSummaryResp(
            id=log.id,
            toolId=log.tool_id,
            source=log.source,  # type: ignore[arg-type]
            status=log.status,  # type: ignore[arg-type]
            requestMethod=log.request_method,
            requestUrl=log.request_url,
            responseStatusCode=log.response_status_code,
            latencyMs=log.latency_ms,
            errorCode=log.error_code,
            errorMessage=log.error_message,
            createdAt=log.created_at,
        )

    async def _load_bound_agent_counts(
        self,
        tool_ids: list[int],
    ) -> dict[int, int]:
        if not tool_ids:
            return {}
        rows = (
            await self.db.execute(
                select(AgentToolBinding.tool_id, func.count())
                .where(
                    AgentToolBinding.tool_id.in_(tool_ids),
                    AgentToolBinding.deleted_at.is_(None),
                )
                .group_by(AgentToolBinding.tool_id)
            )
        ).all()
        return {int(tool_id): int(count) for tool_id, count in rows}

    async def _bound_agent_count(self, tool_id: int) -> int:
        return int(
            (
                await self.db.execute(
                    select(func.count())
                    .select_from(AgentToolBinding)
                    .where(
                        AgentToolBinding.tool_id == tool_id,
                        AgentToolBinding.deleted_at.is_(None),
                    )
                )
            ).scalar_one()
        )

    def _active_parameters(self, tool: Tool) -> list[ToolParameter]:
        return [
            parameter
            for parameter in tool.parameters
            if parameter.deleted_at is None
        ]

    def _parameters_from_openapi(
        self,
        operation: dict[str, Any],
    ) -> list[ToolParameterInput]:
        result: list[ToolParameterInput] = []
        for index, raw in enumerate(operation.get("parameters") or []):
            schema = raw.get("schema") or {"type": "string"}
            result.append(
                ToolParameterInput(
                    name=raw["name"],
                    label=raw.get("name"),
                    description=raw.get("description") or "",
                    paramLocation=raw.get("in", "query"),
                    schemaType=schema.get("type", "string"),
                    isRequired=bool(raw.get("required", False)),
                    defaultValue=schema.get("default"),
                    enumValues=schema.get("enum"),
                    schema=schema,
                    sortOrder=index,
                    metadata=None,
                )
            )
        return result

    def _first_server_url(self, document: dict[str, Any]) -> str:
        servers = document.get("servers") or []
        if servers and isinstance(servers[0], dict) and servers[0].get("url"):
            return str(servers[0]["url"])
        return ""

    def _render_json_template(
        self,
        template: dict[str, Any],
        values: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            str(key): self._render_value(value, values)
            for key, value in template.items()
        }

    def _render_value(self, value: Any, values: dict[str, Any]) -> Any:
        if isinstance(value, str):
            return self._render_template(value, values)
        if isinstance(value, dict):
            return self._render_json_template(value, values)
        if isinstance(value, list):
            return [self._render_value(item, values) for item in value]
        return value

    def _render_template(self, template: str, values: dict[str, Any]) -> str:
        result = template
        for key, value in values.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result

    def _safe_headers(self, headers: dict[str, str]) -> dict[str, str]:
        return {
            key: value
            for key, value in headers.items()
            if key.lower() in SAFE_HEADER_PREFIXES
        }

    def _mask_headers(self, headers: dict[str, str]) -> dict[str, str]:
        masked: dict[str, str] = {}
        for key, value in headers.items():
            if key.lower() in SAFE_HEADER_PREFIXES:
                masked[key] = value
            else:
                masked[key] = mask_secret(value)
        return masked

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

    def _preview(self, value: Any | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            text = value
        else:
            text = json.dumps(value, ensure_ascii=False)
        return text[:PREVIEW_LIMIT]
