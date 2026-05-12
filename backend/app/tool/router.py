"""Tool module routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_active_user
from app.auth.model import User
from app.core.database import get_db_session
from app.core.responses import Result
from app.tool.schema import ToolExecutionPreviewResp
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
