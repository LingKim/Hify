"""Conversation module routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.conversation.schema import ConversationChatPreviewResp
from app.conversation.service import ConversationService
from app.core.database import get_db_session
from app.core.responses import Result

router = APIRouter(prefix="/api/v1/conversations", tags=["conversation"])


@router.get(
    "/chat-preview",
    response_model=Result[ConversationChatPreviewResp],
)
async def chat_preview(
    db: AsyncSession = Depends(get_db_session),
) -> Result[ConversationChatPreviewResp]:
    """Return the conversation module preview endpoint response."""
    service = ConversationService(db)
    return Result.success(data=await service.preview())
