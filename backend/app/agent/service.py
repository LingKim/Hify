"""Agent module business services."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.schema import AgentConfigPreviewResp


class AgentService:
    """Agent service placeholder."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the agent service."""
        self.db = db

    async def preview(self) -> AgentConfigPreviewResp:
        """Return the agent module preview payload."""
        return AgentConfigPreviewResp(
            module="agent",
            status="skeleton_ready",
            capabilities=[
                "Agent 配置管理",
                "模型与知识库绑定",
                "工具集合编排",
            ],
        )
