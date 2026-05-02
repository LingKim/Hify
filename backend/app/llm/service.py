"""LLM module business services."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.schema import ModelPreviewResp


class LlmService:
    """LLM service placeholder."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the LLM service."""
        self.db = db

    async def preview(self) -> ModelPreviewResp:
        """Return the llm module preview payload."""
        return ModelPreviewResp(
            module="llm",
            status="skeleton_ready",
            capabilities=[
                "多模型配置管理",
                "Provider 适配",
                "调用参数统一封装",
            ],
        )
