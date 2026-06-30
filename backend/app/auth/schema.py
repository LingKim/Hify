"""Auth module request and response schemas."""

from pydantic import BaseModel, ConfigDict, Field

from app.rbac.schema import RoleRefResp


class LoginPreviewResp(BaseModel):
    """Response schema for the auth preview endpoint."""

    module: str
    status: str
    capabilities: list[str]


class LoginReq(BaseModel):
    """Login payload for local account authentication."""

    account: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class CurrentUserResp(BaseModel):
    """Current authenticated user payload."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int
    username: str
    email: str
    roles: list[RoleRefResp]
    permissions: list[str]


class LoginResp(BaseModel):
    """Login response with access token and current user."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    access_token: str = Field(alias="accessToken")
    token_type: str = Field(alias="tokenType")
    expires_in: int = Field(alias="expiresIn")
    user: CurrentUserResp
