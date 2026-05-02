"""Knowledge module routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.responses import Result
from app.knowledge.schema import KnowledgeRetrievalPreviewResp
from app.knowledge.service import KnowledgeService

router = APIRouter(prefix="/api/v1/knowledge-bases", tags=["knowledge"])


@router.get(
    "/retrieval-preview",
    response_model=Result[KnowledgeRetrievalPreviewResp],
)
async def retrieval_preview(
    db: AsyncSession = Depends(get_db_session),
) -> Result[KnowledgeRetrievalPreviewResp]:
    """Return the knowledge module preview endpoint response."""
    service = KnowledgeService(db)
    return Result.success(data=await service.preview())
