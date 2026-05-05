"""Agent module routes."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.schema import (
    AgentAdminCreateReq,
    AgentAdminUpdateReq,
    AgentConfigPreviewResp,
    AgentDetailResp,
    AgentListParams,
    AgentRuntimePreviewResp,
    AgentSummaryResp,
)
from app.agent.service import AgentService
from app.core.database import get_db_session
from app.core.responses import PageResult, Result

router = APIRouter(prefix="/api/v1/agents", tags=["agent"])


@router.get("/config-preview", response_model=Result[AgentConfigPreviewResp])
async def config_preview(
    db: AsyncSession = Depends(get_db_session),
) -> Result[AgentConfigPreviewResp]:
    """Return the legacy agent module preview endpoint response."""
    service = AgentService(db)
    return Result.success(data=await service.preview())


@router.get("", response_model=Result[PageResult[AgentSummaryResp]])
async def list_agents(
    params: AgentListParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
) -> Result[PageResult[AgentSummaryResp]]:
    """Return paginated agent configuration summaries."""
    service = AgentService(db)
    return Result.success(data=await service.list_agents(params))


@router.get("/{agent_id}", response_model=Result[AgentDetailResp])
async def get_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> Result[AgentDetailResp]:
    """Return one aggregated agent configuration."""
    service = AgentService(db)
    return Result.success(data=await service.get_agent(agent_id))


@router.post(
    "",
    response_model=Result[AgentDetailResp],
    status_code=status.HTTP_201_CREATED,
)
async def create_agent(
    payload: AgentAdminCreateReq,
    db: AsyncSession = Depends(get_db_session),
) -> Result[AgentDetailResp]:
    """Create one aggregated agent configuration."""
    service = AgentService(db)
    return Result.success(
        data=await service.create_agent(payload),
        code=status.HTTP_201_CREATED,
    )


@router.put("/{agent_id}", response_model=Result[AgentDetailResp])
async def update_agent(
    agent_id: int,
    payload: AgentAdminUpdateReq,
    db: AsyncSession = Depends(get_db_session),
) -> Result[AgentDetailResp]:
    """Update one aggregated agent configuration."""
    service = AgentService(db)
    return Result.success(data=await service.update_agent(agent_id, payload))


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    """Soft-delete one agent configuration."""
    service = AgentService(db)
    await service.delete_agent(agent_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{agent_id}/config-preview",
    response_model=Result[AgentRuntimePreviewResp],
)
async def get_agent_config_preview(
    agent_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> Result[AgentRuntimePreviewResp]:
    """Return a UI-safe agent runtime configuration preview."""
    service = AgentService(db)
    return Result.success(data=await service.get_agent_config_preview(agent_id))
