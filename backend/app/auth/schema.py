"""Auth module request and response schemas."""

from pydantic import BaseModel


class LoginPreviewResp(BaseModel):
    """Response schema for the auth preview endpoint."""

    module: str
    status: str
    capabilities: list[str]
