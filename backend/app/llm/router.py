"""LLM module routes."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.responses import PageResult, Result
from app.llm.schema import (
    ModelPreviewResp,
    ProviderAdminCreateReq,
    ProviderAdminUpdateReq,
    ProviderConnectionTestResp,
    ProviderDetailResp,
    ProviderInvokeTestReq,
    ProviderInvokeTestResp,
    ProviderListParams,
    ProviderRuntimeConfigResp,
    ProviderSummaryResp,
)
from app.llm.service import LlmService

router = APIRouter(prefix="/api/v1/llms", tags=["llm"])


@router.get("/model-preview", response_model=Result[ModelPreviewResp])
async def model_preview(
    db: AsyncSession = Depends(get_db_session),
) -> Result[ModelPreviewResp]:
    """Return the llm module preview payload."""
    service = LlmService(db)
    return Result.success(data=await service.preview())


@router.get(
    "/providers",
    response_model=Result[PageResult[ProviderSummaryResp]],
)
async def list_providers(
    params: ProviderListParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
) -> Result[PageResult[ProviderSummaryResp]]:
    """Return paginated provider records for the single admin page."""
    service = LlmService(db)
    return Result.success(data=await service.list_providers(params))


@router.get(
    "/providers/{provider_id}",
    response_model=Result[ProviderDetailResp],
)
async def get_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> Result[ProviderDetailResp]:
    """Return one provider detail record."""
    service = LlmService(db)
    return Result.success(data=await service.get_provider(provider_id))


@router.get(
    "/providers/{provider_id}/runtime-config",
    response_model=Result[ProviderRuntimeConfigResp],
)
async def get_provider_runtime_config(
    provider_id: int,
    model_name: str | None = None,
    db: AsyncSession = Depends(get_db_session),
) -> Result[ProviderRuntimeConfigResp]:
    """Return a UI-safe LiteLLM runtime config preview."""
    service = LlmService(db)
    return Result.success(
        data=await service.get_provider_runtime_config(
            provider_id,
            model_name=model_name,
        )
    )


@router.post(
    "/providers",
    response_model=Result[ProviderDetailResp],
    status_code=status.HTTP_201_CREATED,
)
async def create_provider(
    payload: ProviderAdminCreateReq,
    db: AsyncSession = Depends(get_db_session),
) -> Result[ProviderDetailResp]:
    """Create one aggregated provider record."""
    service = LlmService(db)
    return Result.success(
        data=await service.create_provider(payload),
        code=status.HTTP_201_CREATED,
    )


@router.put(
    "/providers/{provider_id}",
    response_model=Result[ProviderDetailResp],
)
async def update_provider(
    provider_id: int,
    payload: ProviderAdminUpdateReq,
    db: AsyncSession = Depends(get_db_session),
) -> Result[ProviderDetailResp]:
    """Update one aggregated provider record."""
    service = LlmService(db)
    return Result.success(
        data=await service.update_provider(provider_id, payload)
    )


@router.delete(
    "/providers/{provider_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    """Soft-delete one provider record."""
    service = LlmService(db)
    await service.delete_provider(provider_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/providers/{provider_id}/test-connection",
    response_model=Result[ProviderConnectionTestResp],
)
async def test_provider_connection(
    provider_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> Result[ProviderConnectionTestResp]:
    """Test one provider connection and persist its health snapshot."""
    service = LlmService(db)
    return Result.success(
        data=await service.test_provider_connection(provider_id)
    )


@router.post(
    "/providers/{provider_id}/invoke-test",
    response_model=Result[ProviderInvokeTestResp],
)
async def invoke_provider_test(
    provider_id: int,
    payload: ProviderInvokeTestReq,
    db: AsyncSession = Depends(get_db_session),
) -> Result[ProviderInvokeTestResp]:
    """Run one real LiteLLM test invocation for the provider."""
    service = LlmService(db)
    return Result.success(
        data=await service.invoke_provider_test(provider_id, payload)
    )
