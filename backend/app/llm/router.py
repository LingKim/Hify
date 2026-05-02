"""LLM module routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.responses import Result
from app.llm.schema import ModelPreviewResp
from app.llm.service import LlmService

router = APIRouter(prefix="/api/v1/llms", tags=["llm"])


@router.get("/model-preview", response_model=Result[ModelPreviewResp])
async def model_preview(
    db: AsyncSession = Depends(get_db_session),
) -> Result[ModelPreviewResp]:
    """Return the llm module preview endpoint response."""
    service = LlmService(db)
    return Result.success(data=await service.preview())
