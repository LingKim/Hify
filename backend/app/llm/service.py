"""LLM module business services."""

from __future__ import annotations

from time import perf_counter

from fastapi import status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import utc_now
from app.core.errors import CommonErrorCode
from app.core.exceptions import BizException
from app.core.http import ExternalHttpClient
from app.core.responses import PageResult
from app.llm.executor import LiteLLMExecutor
from app.llm.model import (
    ProviderAuthSecret,
    ProviderHealthStatus,
    ProviderInstance,
    ProviderModel,
)
from app.llm.provider import (
    LiteLLMRuntimeConfig,
    ProviderSecretCodec,
    ProviderSecretPayload,
    fingerprint_secret,
    mask_secret,
    resolve_litellm_model,
)
from app.llm.schema import (
    ModelPreviewResp,
    ProviderAdminCreateReq,
    ProviderAdminUpdateReq,
    ProviderAuthSecretInput,
    ProviderAuthSecretResp,
    ProviderConnectionTestResp,
    ProviderDetailResp,
    ProviderHealthStatusResp,
    ProviderInvokeTestReq,
    ProviderInvokeTestResp,
    ProviderListParams,
    ProviderModelInput,
    ProviderModelResp,
    ProviderRuntimeConfigResp,
    ProviderSummaryResp,
)


class LlmService:
    """LLM service with aggregated provider CRUD operations."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        http_client: ExternalHttpClient | None = None,
        executor: LiteLLMExecutor | None = None,
    ) -> None:
        """Initialize the LLM service."""
        self.db = db
        self.secret_codec = ProviderSecretCodec()
        self.http_client = http_client or ExternalHttpClient()
        self.executor = executor or LiteLLMExecutor()

    async def preview(self) -> ModelPreviewResp:
        """Return the llm module preview payload."""
        return ModelPreviewResp(
            module="llm",
            status="skeleton_ready",
            capabilities=[
                "多模型配置管理",
                "Provider 适配",
                "调用参数统一封装",
            ],
        )

    async def list_providers(
        self,
        params: ProviderListParams,
    ) -> PageResult[ProviderSummaryResp]:
        """Return paginated provider summaries for the admin page."""
        filters = [ProviderInstance.deleted_at.is_(None)]
        if params.keyword:
            keyword = f"%{params.keyword.strip()}%"
            filters.append(
                or_(
                    ProviderInstance.name.ilike(keyword),
                    ProviderInstance.base_url.ilike(keyword),
                )
            )
        if params.provider_type:
            filters.append(
                ProviderInstance.provider_type == params.provider_type
            )
        if params.status:
            filters.append(ProviderInstance.status == params.status)

        total_statement = (
            select(func.count())
            .select_from(ProviderInstance)
            .where(*filters)
        )
        total = int((await self.db.execute(total_statement)).scalar_one())

        statement = (
            select(ProviderInstance)
            .where(*filters)
            .options(
                selectinload(ProviderInstance.auth_secret),
                selectinload(ProviderInstance.models),
                selectinload(ProviderInstance.health_status),
            )
            .order_by(
                ProviderInstance.priority.desc(),
                ProviderInstance.id.desc(),
            )
            .offset(params.offset)
            .limit(params.page_size)
        )
        instances = list((await self.db.scalars(statement)).all())
        items = [
            self._build_summary_response(instance)
            for instance in instances
        ]
        return PageResult.create(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    async def get_provider(self, provider_id: int) -> ProviderDetailResp:
        """Return one provider detail payload."""
        instance = await self._get_provider_instance_or_raise(provider_id)
        return self._build_detail_response(instance)

    async def create_provider(
        self,
        payload: ProviderAdminCreateReq,
    ) -> ProviderDetailResp:
        """Create an aggregated provider record."""
        await self._ensure_instance_name_unique(payload.name)
        instance = ProviderInstance(
            name=payload.name,
            provider_type=payload.provider_type,
            api_family=payload.api_family,
            base_url=payload.base_url,
            status=payload.status,
            is_default=payload.is_default,
            priority=payload.priority,
            notes=payload.notes,
            metadata_json=payload.metadata,
        )
        self.db.add(instance)
        await self.db.flush()

        if payload.is_default:
            await self._clear_other_default_instances(instance.id)

        auth_secret = self._build_auth_secret(
            provider_instance_id=instance.id,
            auth=payload.auth,
            existing=None,
        )
        self.db.add(auth_secret)
        await self.db.flush()

        models = self._build_models(
            provider_instance_id=instance.id,
            models=payload.models,
        )
        self.db.add_all(models)

        health_status = ProviderHealthStatus(provider_instance_id=instance.id)
        self.db.add(health_status)

        await self.db.commit()
        return await self.get_provider(instance.id)

    async def update_provider(
        self,
        provider_id: int,
        payload: ProviderAdminUpdateReq,
    ) -> ProviderDetailResp:
        """Update an aggregated provider record."""
        instance = await self._get_provider_instance_or_raise(provider_id)
        await self._ensure_instance_name_unique(
            payload.name,
            exclude_id=provider_id,
        )

        instance.name = payload.name
        instance.provider_type = payload.provider_type
        instance.api_family = payload.api_family
        instance.base_url = payload.base_url
        instance.status = payload.status
        instance.is_default = payload.is_default
        instance.priority = payload.priority
        instance.notes = payload.notes
        instance.metadata_json = payload.metadata
        instance.version += 1

        if payload.is_default:
            await self._clear_other_default_instances(provider_id)

        current_auth = instance.auth_secret
        if current_auth is None:
            current_auth = self._build_auth_secret(
                provider_instance_id=provider_id,
                auth=payload.auth,
                existing=None,
            )
            self.db.add(current_auth)
        else:
            self._update_auth_secret(current_auth, payload.auth)

        await self._replace_models(instance, payload.models)

        await self.db.commit()
        return await self.get_provider(provider_id)

    async def delete_provider(self, provider_id: int) -> None:
        """Soft-delete one provider and its child records."""
        instance = await self._get_provider_instance_or_raise(provider_id)

        for model in instance.models:
            if not model.is_deleted:
                model.soft_delete()
                model.version += 1

        if (
            instance.auth_secret is not None
            and not instance.auth_secret.is_deleted
        ):
            instance.auth_secret.soft_delete()
            instance.auth_secret.version += 1

        if (
            instance.health_status is not None
            and not instance.health_status.is_deleted
        ):
            instance.health_status.soft_delete()
            instance.health_status.version += 1

        instance.soft_delete()
        instance.version += 1

        await self.db.commit()

    async def get_provider_runtime_config(
        self,
        provider_id: int,
        *,
        model_name: str | None = None,
    ) -> ProviderRuntimeConfigResp:
        """Return a UI-safe LiteLLM runtime config preview."""
        instance = await self._get_provider_instance_or_raise(provider_id)
        runtime_config = self._build_runtime_config(
            instance,
            model_name=model_name,
        )
        return ProviderRuntimeConfigResp(
            providerId=instance.id,
            providerType=runtime_config.provider_type,
            apiFamily=runtime_config.api_family,
            modelName=runtime_config.model_name,
            litellmModel=runtime_config.litellm_model,
            apiBase=runtime_config.api_base,
            apiKeyMasked=runtime_config.masked_api_key,
            extraHeaders=runtime_config.extra_headers,
            queryParams=runtime_config.query_params,
        )

    async def test_provider_connection(
        self,
        provider_id: int,
    ) -> ProviderConnectionTestResp:
        """Test one provider connection and update the health snapshot."""
        instance = await self._get_provider_instance_or_raise(provider_id)
        runtime_config = self._build_runtime_config(instance)
        connection_test_url = self._build_connection_test_url(instance)
        start_clock = perf_counter()
        response = await self.http_client.request_json(
            "GET",
            connection_test_url,
            headers=runtime_config.extra_headers,
            params=runtime_config.query_params,
        )
        latency_ms = int((perf_counter() - start_clock) * 1000)
        checked_at = utc_now()

        health_status = instance.health_status
        if health_status is None:
            health_status = ProviderHealthStatus(
                provider_instance_id=instance.id
            )
            self.db.add(health_status)
            await self.db.flush()

        if response.status_code == 0:
            health_state = "unhealthy"
            auth_state = "unknown"
            connectivity_state = "unreachable"
            inference_state = "failed"
            message = response.error or "连接失败"
        elif response.status_code in {401, 403}:
            health_state = "unhealthy"
            auth_state = "invalid"
            connectivity_state = "reachable"
            inference_state = "failed"
            message = "鉴权失败，请检查密钥配置"
        elif response.ok:
            health_state = "healthy"
            auth_state = "valid"
            connectivity_state = "reachable"
            inference_state = "ok"
            message = "连接成功"
        else:
            health_state = "degraded"
            auth_state = "unknown"
            connectivity_state = "reachable"
            inference_state = "failed"
            message = f"已连通，但返回 HTTP {response.status_code}"

        health_status.health_state = health_state
        health_status.auth_state = auth_state
        health_status.connectivity_state = connectivity_state
        health_status.inference_state = inference_state
        health_status.last_check_at = checked_at
        health_status.latency_ms_p50 = latency_ms
        health_status.latency_ms_p95 = latency_ms
        health_status.last_error_code = (
            None if response.ok else str(response.status_code)
        )
        health_status.last_error_message = None if response.ok else message
        if response.ok:
            health_status.last_success_at = checked_at
            health_status.consecutive_failures = 0
        else:
            health_status.last_failure_at = checked_at
            health_status.last_error_at = checked_at
            health_status.consecutive_failures += 1
        health_status.version += 1

        await self.db.commit()

        return ProviderConnectionTestResp(
            providerId=instance.id,
            healthState=health_state,
            authState=auth_state,
            connectivityState=connectivity_state,
            inferenceState=inference_state,
            httpStatusCode=response.status_code,
            latencyMs=latency_ms,
            message=message,
            checkedAt=checked_at,
        )

    async def invoke_provider_test(
        self,
        provider_id: int,
        payload: ProviderInvokeTestReq,
    ) -> ProviderInvokeTestResp:
        """Run one real LiteLLM test invocation for the provider."""
        instance = await self._get_provider_instance_or_raise(provider_id)
        runtime_config = self._build_runtime_config(
            instance,
            model_name=payload.model_name,
        )
        checked_at = utc_now()

        health_status = instance.health_status
        if health_status is None:
            health_status = ProviderHealthStatus(
                provider_instance_id=instance.id
            )
            self.db.add(health_status)
            await self.db.flush()

        try:
            result = await self.executor.invoke_text(
                runtime_config,
                prompt=payload.prompt,
                temperature=payload.temperature,
                max_tokens=payload.max_tokens,
            )
        except BizException as exc:
            health_status.health_state = "unhealthy"
            health_status.inference_state = "failed"
            health_status.last_check_at = checked_at
            health_status.last_failure_at = checked_at
            health_status.last_error_at = checked_at
            health_status.last_error_code = str(exc.code)
            health_status.last_error_message = exc.message
            health_status.consecutive_failures += 1
            health_status.version += 1
            await self.db.commit()
            raise

        health_status.health_state = "healthy"
        health_status.auth_state = "valid"
        health_status.connectivity_state = "reachable"
        health_status.inference_state = "ok"
        health_status.last_check_at = checked_at
        health_status.last_success_at = checked_at
        health_status.latency_ms_p50 = result.latency_ms
        health_status.latency_ms_p95 = result.latency_ms
        health_status.last_error_code = None
        health_status.last_error_message = None
        health_status.consecutive_failures = 0
        health_status.version += 1
        await self.db.commit()

        return ProviderInvokeTestResp(
            providerId=instance.id,
            modelName=result.model_name,
            litellmModel=result.litellm_model,
            outputText=result.output_text,
            latencyMs=result.latency_ms,
        )

    async def _get_provider_instance_or_raise(
        self,
        provider_id: int,
    ) -> ProviderInstance:
        statement = (
            select(ProviderInstance)
            .where(
                ProviderInstance.id == provider_id,
                ProviderInstance.deleted_at.is_(None),
            )
            .options(
                selectinload(ProviderInstance.auth_secret),
                selectinload(ProviderInstance.models),
                selectinload(ProviderInstance.health_status),
            )
        )
        instance = await self.db.scalar(statement)
        if instance is None:
            raise BizException(
                code=CommonErrorCode.RESOURCE_NOT_FOUND,
                message="模型提供商不存在",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        return instance

    async def _ensure_instance_name_unique(
        self,
        name: str,
        *,
        exclude_id: int | None = None,
    ) -> None:
        statement = select(ProviderInstance).where(
            ProviderInstance.name == name,
            ProviderInstance.deleted_at.is_(None),
        )
        if exclude_id is not None:
            statement = statement.where(ProviderInstance.id != exclude_id)
        existed = await self.db.scalar(statement)
        if existed is not None:
            raise BizException(
                code=CommonErrorCode.RESOURCE_ALREADY_EXISTS,
                message="模型提供商名称已存在",
                http_status=status.HTTP_409_CONFLICT,
            )

    async def _clear_other_default_instances(self, instance_id: int) -> None:
        statement = select(ProviderInstance).where(
            ProviderInstance.deleted_at.is_(None),
            ProviderInstance.is_default.is_(True),
            ProviderInstance.id != instance_id,
        )
        for instance in list((await self.db.scalars(statement)).all()):
            instance.is_default = False
            instance.version += 1

    def _build_auth_secret(
        self,
        *,
        provider_instance_id: int,
        auth: ProviderAuthSecretInput,
        existing: ProviderAuthSecret | None,
    ) -> ProviderAuthSecret:
        secret_value = auth.secret_value
        if auth.auth_type != "none" and not secret_value:
            raise BizException(
                code=CommonErrorCode.VALIDATION_ERROR,
                message="新增提供商时必须填写密钥",
                http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )

        effective_secret_value = secret_value or ""
        payload = ProviderSecretPayload(
            secret_value=effective_secret_value,
            headers=auth.headers,
            query_params=auth.query_params,
            metadata=auth.metadata,
        )
        ciphertext = self.secret_codec.encrypt(payload)
        now = utc_now()
        return ProviderAuthSecret(
            provider_instance_id=provider_instance_id,
            auth_type=auth.auth_type,
            secret_ciphertext=ciphertext,
            secret_masked=mask_secret(effective_secret_value),
            secret_fingerprint=fingerprint_secret(effective_secret_value),
            encryption_key_version="v1",
            last_rotated_at=now,
            expires_at=auth.expires_at,
            metadata_json={
                "headers": auth.headers or {},
                "query_params": auth.query_params or {},
                "metadata": auth.metadata or {},
            },
            version=existing.version + 1 if existing is not None else 1,
        )

    def _update_auth_secret(
        self,
        auth_secret: ProviderAuthSecret,
        auth: ProviderAuthSecretInput,
    ) -> None:
        auth_secret.auth_type = auth.auth_type
        auth_secret.expires_at = auth.expires_at
        auth_secret.metadata_json = {
            "headers": auth.headers or {},
            "query_params": auth.query_params or {},
            "metadata": auth.metadata or {},
        }

        if auth.secret_value or auth.auth_type == "none":
            effective_secret_value = auth.secret_value or ""
            payload = ProviderSecretPayload(
                secret_value=effective_secret_value,
                headers=auth.headers,
                query_params=auth.query_params,
                metadata=auth.metadata,
            )
            auth_secret.secret_ciphertext = self.secret_codec.encrypt(payload)
            auth_secret.secret_masked = mask_secret(effective_secret_value)
            auth_secret.secret_fingerprint = fingerprint_secret(
                effective_secret_value
            )
            auth_secret.last_rotated_at = utc_now()

        auth_secret.version += 1

    def _build_connection_auth(
        self,
        auth_secret: ProviderAuthSecret,
    ) -> tuple[dict[str, str], dict[str, str]]:
        metadata = auth_secret.metadata_json or {}
        headers = {
            key: str(value)
            for key, value in (metadata.get("headers") or {}).items()
        }
        query_params = {
            key: str(value)
            for key, value in (metadata.get("query_params") or {}).items()
        }

        payload = self.secret_codec.decrypt(auth_secret.secret_ciphertext)
        secret_value = payload.secret_value
        if (
            auth_secret.auth_type in {"api_key", "bearer_token"}
            and secret_value
        ):
            headers.setdefault("Authorization", f"Bearer {secret_value}")

        return headers, query_params

    def _build_connection_test_url(
        self,
        instance: ProviderInstance,
    ) -> str:
        """Resolve the best-effort health-check endpoint for one provider."""
        base_url = instance.base_url.rstrip("/")
        if instance.provider_type in {
            "openai",
            "openai_compatible",
            "anthropic",
        }:
            return f"{base_url}/models"
        if instance.provider_type == "ollama":
            return f"{base_url}/api/tags"
        return base_url

    def _build_runtime_config(
        self,
        instance: ProviderInstance,
        *,
        model_name: str | None = None,
    ) -> LiteLLMRuntimeConfig:
        auth_secret = instance.auth_secret
        if auth_secret is None or auth_secret.deleted_at is not None:
            raise BizException(
                code=CommonErrorCode.VALIDATION_ERROR,
                message="该提供商尚未配置鉴权信息",
                http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )

        active_models = self._active_models(instance.models)
        selected_model = (
            next(
                (
                    model
                    for model in active_models
                    if model.model_name == model_name
                ),
                None,
            )
            if model_name
            else next(
                (model for model in active_models if model.is_default),
                active_models[0] if active_models else None,
            )
        )
        if selected_model is None:
            raise BizException(
                code=CommonErrorCode.RESOURCE_NOT_FOUND,
                message="目标模型不存在",
                http_status=status.HTTP_404_NOT_FOUND,
            )

        headers, query_params = self._build_connection_auth(auth_secret)
        payload = self.secret_codec.decrypt(auth_secret.secret_ciphertext)
        return LiteLLMRuntimeConfig(
            provider_type=instance.provider_type,
            api_family=instance.api_family,
            model_name=selected_model.model_name,
            litellm_model=resolve_litellm_model(
                instance.provider_type,
                selected_model.model_name,
            ),
            api_base=instance.base_url,
            api_key=payload.secret_value,
            extra_headers=headers,
            query_params=query_params,
        )

    def _build_models(
        self,
        *,
        provider_instance_id: int,
        models: list[ProviderModelInput],
    ) -> list[ProviderModel]:
        if not models:
            raise BizException(
                code=CommonErrorCode.VALIDATION_ERROR,
                message="至少需要配置一个模型",
                http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )

        normalized_models = list(models)
        if not any(model.is_default for model in normalized_models):
            normalized_models[0] = normalized_models[0].model_copy(
                update={"is_default": True}
            )

        default_count = sum(
            1 for model in normalized_models if model.is_default
        )
        if default_count > 1:
            raise BizException(
                code=CommonErrorCode.VALIDATION_ERROR,
                message="同一个提供商只能设置一个默认模型",
                http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )

        seen_names: set[str] = set()
        entities: list[ProviderModel] = []
        for item in normalized_models:
            if item.model_name in seen_names:
                raise BizException(
                    code=CommonErrorCode.VALIDATION_ERROR,
                    message="同一个提供商下模型名称不能重复",
                    http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
                )
            seen_names.add(item.model_name)
            entities.append(
                ProviderModel(
                    provider_instance_id=provider_instance_id,
                    model_name=item.model_name,
                    display_name=item.display_name,
                    description=item.description,
                    status=item.status,
                    is_default=item.is_default,
                    sort_order=item.sort_order,
                    supports_chat=item.supports_chat,
                    supports_stream=item.supports_stream,
                    supports_tools=item.supports_tools,
                    supports_structured_output=item.supports_structured_output,
                    supports_vision_input=item.supports_vision_input,
                    supports_audio_input=item.supports_audio_input,
                    supports_reasoning=item.supports_reasoning,
                    supports_embeddings=item.supports_embeddings,
                    context_window=item.context_window,
                    max_output_tokens=item.max_output_tokens,
                    max_input_tokens=item.max_input_tokens,
                    temperature_supported=item.temperature_supported,
                    top_p_supported=item.top_p_supported,
                    tags_json=item.tags,
                    pricing_json=item.pricing,
                    metadata_json=item.metadata,
                )
            )
        return entities

    async def _replace_models(
        self,
        instance: ProviderInstance,
        models: list[ProviderModelInput],
    ) -> None:
        for model in instance.models:
            if not model.is_deleted:
                model.soft_delete()
                model.version += 1
        await self.db.flush()

        new_models = self._build_models(
            provider_instance_id=instance.id,
            models=models,
        )
        self.db.add_all(new_models)

    def _build_summary_response(
        self,
        instance: ProviderInstance,
    ) -> ProviderSummaryResp:
        active_models = self._active_models(instance.models)
        default_model = next(
            (model for model in active_models if model.is_default),
            active_models[0] if active_models else None,
        )
        return ProviderSummaryResp(
            id=instance.id,
            name=instance.name,
            providerType=instance.provider_type,
            apiFamily=instance.api_family,
            baseUrl=instance.base_url,
            status=instance.status,
            isDefault=instance.is_default,
            priority=instance.priority,
            notes=instance.notes,
            metadata=instance.metadata_json,
            modelCount=len(active_models),
            auth=self._build_auth_response(instance.auth_secret),
            defaultModel=(
                self._build_model_response(default_model)
                if default_model is not None
                else None
            ),
            health=self._build_health_response(instance.health_status),
            createdAt=instance.created_at,
            updatedAt=instance.updated_at,
        )

    def _build_detail_response(
        self,
        instance: ProviderInstance,
    ) -> ProviderDetailResp:
        active_models = self._active_models(instance.models)
        summary = self._build_summary_response(instance)
        return ProviderDetailResp(
            **summary.model_dump(by_alias=True),
            models=[
                self._build_model_response(model)
                for model in active_models
            ],
        )

    def _build_auth_response(
        self,
        auth_secret: ProviderAuthSecret | None,
    ) -> ProviderAuthSecretResp | None:
        if auth_secret is None or auth_secret.is_deleted:
            return None
        metadata = auth_secret.metadata_json or {}
        return ProviderAuthSecretResp(
            authType=auth_secret.auth_type,
            secretMasked=auth_secret.secret_masked,
            hasSecret=bool(auth_secret.secret_ciphertext),
            headers=metadata.get("headers"),
            queryParams=metadata.get("query_params"),
            metadata=metadata.get("metadata"),
            expiresAt=auth_secret.expires_at,
            lastRotatedAt=auth_secret.last_rotated_at,
        )

    def _build_model_response(self, model: ProviderModel) -> ProviderModelResp:
        return ProviderModelResp(
            id=model.id,
            modelName=model.model_name,
            displayName=model.display_name,
            description=model.description,
            status=model.status,
            isDefault=model.is_default,
            sortOrder=model.sort_order,
            supportsChat=model.supports_chat,
            supportsStream=model.supports_stream,
            supportsTools=model.supports_tools,
            supportsStructuredOutput=model.supports_structured_output,
            supportsVisionInput=model.supports_vision_input,
            supportsAudioInput=model.supports_audio_input,
            supportsReasoning=model.supports_reasoning,
            supportsEmbeddings=model.supports_embeddings,
            contextWindow=model.context_window,
            maxOutputTokens=model.max_output_tokens,
            maxInputTokens=model.max_input_tokens,
            temperatureSupported=model.temperature_supported,
            topPSupported=model.top_p_supported,
            tags=model.tags_json,
            pricing=model.pricing_json,
            metadata=model.metadata_json,
            createdAt=model.created_at,
            updatedAt=model.updated_at,
        )

    def _build_health_response(
        self,
        health_status: ProviderHealthStatus | None,
    ) -> ProviderHealthStatusResp | None:
        if health_status is None or health_status.is_deleted:
            return None
        return ProviderHealthStatusResp(
            healthState=health_status.health_state,
            authState=health_status.auth_state,
            connectivityState=health_status.connectivity_state,
            inferenceState=health_status.inference_state,
            lastCheckAt=health_status.last_check_at,
            lastSuccessAt=health_status.last_success_at,
            lastFailureAt=health_status.last_failure_at,
            consecutiveFailures=health_status.consecutive_failures,
            latencyMsP50=health_status.latency_ms_p50,
            latencyMsP95=health_status.latency_ms_p95,
            lastErrorCode=health_status.last_error_code,
            lastErrorMessage=health_status.last_error_message,
            lastErrorAt=health_status.last_error_at,
        )

    def _active_models(
        self,
        models: list[ProviderModel],
    ) -> list[ProviderModel]:
        return [model for model in models if model.deleted_at is None]
