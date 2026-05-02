"""Tool module routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

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
) -> Result[ToolExecutionPreviewResp]:
    """Return the tool module preview endpoint response."""
    service = ToolService(db)
    return Result.success(data=await service.preview())
