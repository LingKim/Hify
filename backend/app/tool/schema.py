"""Tool module request and response schemas."""

from pydantic import BaseModel


class ToolExecutionPreviewResp(BaseModel):
    """Response schema for the tool preview endpoint."""

    module: str
    status: str
    capabilities: list[str]
