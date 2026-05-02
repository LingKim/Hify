"""Knowledge module request and response schemas."""

from pydantic import BaseModel


class KnowledgeRetrievalPreviewResp(BaseModel):
    """Response schema for the knowledge preview endpoint."""

    module: str
    status: str
    capabilities: list[str]
