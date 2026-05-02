"""Auth module request and response schemas."""

from pydantic import BaseModel, ConfigDict, Field


class LoginPreviewResp(BaseModel):
    """Response schema for the auth preview endpoint."""

    module: str
    status: str
    capabilities: list[str]


class CurrentUserResp(BaseModel):
    """Current authenticated user payload."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    user_id: str = Field(alias="userId")
    username: str
    role: str
