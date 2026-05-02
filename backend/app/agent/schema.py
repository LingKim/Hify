"""Agent module request and response schemas."""

from pydantic import BaseModel


class AgentConfigPreviewResp(BaseModel):
    """Response schema for the agent preview endpoint."""

    module: str
    status: str
    capabilities: list[str]
