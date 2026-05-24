"""Tool module routes."""

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_active_user
from app.auth.model import User
from app.core.database import get_db_session
from app.core.responses import PageResult, Result
from app.tool.schema import (
    OpenApiPreviewReq,
    OpenApiPreviewResp,
    ToolCreateReq,
    ToolDetailResp,
    ToolExecuteTestReq,
    ToolExecutionLogListParams,
    ToolExecutionLogSummaryResp,
    ToolExecutionPreviewResp,
    ToolExecutionResp,
    ToolListParams,
    ToolOptionResp,
    ToolSummaryResp,
    ToolUpdateReq,
)
from app.tool.service import ToolService

router = APIRouter(prefix="/api/v1/tools", tags=["tool"])


@router.get(
    "/execution-preview",
    response_model=Result[ToolExecutionPreviewResp],
)
async def execution_preview(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[ToolExecutionPreviewResp]:
    """Return the tool module preview endpoint response."""
    del current_user
    service = ToolService(db)
    return Result.success(data=await service.preview())


@router.get("", response_model=Result[PageResult[ToolSummaryResp]])
async def list_tools(
    params: ToolListParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[PageResult[ToolSummaryResp]]:
    """Return paginated tool summaries."""
    del current_user
    service = ToolService(db)
    return Result.success(data=await service.list_tools(params))


@router.get("/options", response_model=Result[list[ToolOptionResp]])
async def list_tool_options(
    keyword: str | None = None,
    status_value: str | None = Query(default="enabled", alias="status"),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[list[ToolOptionResp]]:
    """Return tool options for Agent configuration forms."""
    del current_user
    service = ToolService(db)
    return Result.success(
        data=await service.list_options(
            keyword=keyword,
            status_value=status_value,
        )
    )


@router.post(
    "/import-openapi/preview",
    response_model=Result[OpenApiPreviewResp],
)
async def preview_openapi_import(
    payload: OpenApiPreviewReq,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[OpenApiPreviewResp]:
    """Preview a single OpenAPI operation as an editable tool draft."""
    del current_user
    service = ToolService(db)
    return Result.success(data=await service.preview_openapi(payload))


@router.post(
    "",
    response_model=Result[ToolDetailResp],
    status_code=status.HTTP_201_CREATED,
)
async def create_tool(
    payload: ToolCreateReq,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[ToolDetailResp]:
    """Create one aggregated tool."""
    service = ToolService(db)
    data = await service.create_tool(payload, user_id=current_user.id)
    return Result.success(data=data, code=status.HTTP_201_CREATED)


@router.get("/{tool_id}", response_model=Result[ToolDetailResp])
async def get_tool(
    tool_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[ToolDetailResp]:
    """Return one tool detail."""
    del current_user
    service = ToolService(db)
    return Result.success(data=await service.get_tool(tool_id))


@router.put("/{tool_id}", response_model=Result[ToolDetailResp])
async def update_tool(
    tool_id: int,
    payload: ToolUpdateReq,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[ToolDetailResp]:
    """Update one aggregated tool."""
    service = ToolService(db)
    return Result.success(
        data=await service.update_tool(
            tool_id,
            payload,
            user_id=current_user.id,
        )
    )


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(
    tool_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """Soft-delete one tool."""
    del current_user
    service = ToolService(db)
    await service.delete_tool(tool_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{tool_id}/execute-test",
    response_model=Result[ToolExecutionResp],
)
async def execute_tool_test(
    tool_id: int,
    payload: ToolExecuteTestReq,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[ToolExecutionResp]:
    """Execute one tool with test parameters."""
    service = ToolService(db)
    return Result.success(
        data=await service.execute_test(
            tool_id,
            payload,
            user_id=current_user.id,
        )
    )


@router.get(
    "/{tool_id}/execution-logs",
    response_model=Result[PageResult[ToolExecutionLogSummaryResp]],
)
async def list_tool_execution_logs(
    tool_id: int,
    params: ToolExecutionLogListParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[PageResult[ToolExecutionLogSummaryResp]]:
    """Return execution logs for one tool."""
    del current_user
    service = ToolService(db)
    return Result.success(
        data=await service.list_execution_logs(tool_id, params)
    )
