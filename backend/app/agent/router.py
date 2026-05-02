"""Agent module routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.schema import AgentConfigPreviewResp
from app.agent.service import AgentService
from app.core.database import get_db_session
from app.core.responses import Result

router = APIRouter(prefix="/api/v1/agents", tags=["agent"])


@router.get("/config-preview", response_model=Result[AgentConfigPreviewResp])
async def config_preview(
    db: AsyncSession = Depends(get_db_session),
) -> Result[AgentConfigPreviewResp]:
    """Return the agent module preview endpoint response."""
    service = AgentService(db)
    return Result.success(data=await service.preview())
