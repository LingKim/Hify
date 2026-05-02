"""Knowledge module business services."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge.schema import KnowledgeRetrievalPreviewResp


class KnowledgeService:
    """Knowledge service placeholder."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the knowledge service."""
        self.db = db

    async def preview(self) -> KnowledgeRetrievalPreviewResp:
        """Return the knowledge module preview payload."""
        return KnowledgeRetrievalPreviewResp(
            module="knowledge",
            status="skeleton_ready",
            capabilities=[
                "知识库管理",
                "文档切片处理",
                "检索增强查询",
            ],
        )
