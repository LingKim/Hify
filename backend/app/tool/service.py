"""Tool module business services."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.tool.schema import ToolExecutionPreviewResp


class ToolService:
    """Tool service placeholder."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the tool service."""
        self.db = db

    async def preview(self) -> ToolExecutionPreviewResp:
        """Return the tool module preview payload."""
        return ToolExecutionPreviewResp(
            module="tool",
            status="skeleton_ready",
            capabilities=[
                "OpenAPI 工具注册",
                "HTTP 工具调用",
                "工具执行结果透传",
            ],
        )
