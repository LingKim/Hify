"""Knowledge module routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_active_user
from app.auth.model import User
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
    current_user: User = Depends(get_current_active_user),
) -> Result[KnowledgeRetrievalPreviewResp]:
    """Return the knowledge module preview endpoint response."""
    del current_user
    service = KnowledgeService(db)
    return Result.success(data=await service.preview())
