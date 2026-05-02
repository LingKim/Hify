"""LLM module request and response schemas."""

from pydantic import BaseModel


class ModelPreviewResp(BaseModel):
    """Response schema for the LLM preview endpoint."""

    module: str
    status: str
    capabilities: list[str]
