"""Conversation module business services."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.conversation.schema import ConversationChatPreviewResp


class ConversationService:
    """Conversation service placeholder."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the conversation service."""
        self.db = db

    async def preview(self) -> ConversationChatPreviewResp:
        """Return the conversation module preview payload."""
        return ConversationChatPreviewResp(
            module="conversation",
            status="skeleton_ready",
            capabilities=[
                "多轮对话管理",
                "SSE 流式输出",
                "Agent 执行编排入口",
            ],
        )
