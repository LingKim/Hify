"""User management request and response schemas."""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.responses import PageParams

USER_ROLES = {"admin", "member"}
ROLE_LABELS = {
    "admin": "管理员",
    "member": "普通用户",
}
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserListParams(PageParams):
    """List query params for user summaries."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    keyword: str | None = None
    role: str | None = None
    is_active: bool | None = Field(default=None, alias="isActive")

    @field_validator("role")
    @classmethod
    def validate_role(cls, role: str | None) -> str | None:
        """Validate the optional role filter."""
        if role is not None and role not in USER_ROLES:
            raise ValueError("角色不合法")
        return role


class UserCreateReq(BaseModel):
    """Create payload for one user."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    username: str = Field(min_length=1, max_length=64)
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: str
    is_active: bool = Field(default=True, alias="isActive")

    @field_validator("username", "email", "role")
    @classmethod
    def validate_non_blank(cls, value: str) -> str:
        """Reject blank string values."""
        normalized = value.strip()
        if normalized == "":
            raise ValueError("不能为空")
        return normalized

    @field_validator("email")
    @classmethod
    def validate_email(cls, email: str) -> str:
        """Validate email syntax without adding another dependency."""
        if EMAIL_PATTERN.match(email) is None:
            raise ValueError("邮箱格式不合法")
        return email

    @field_validator("role")
    @classmethod
    def validate_role(cls, role: str) -> str:
        """Validate the requested role."""
        if role not in USER_ROLES:
            raise ValueError("角色不合法")
        return role


class UserUpdateReq(BaseModel):
    """Update payload for one user."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    username: str = Field(min_length=1, max_length=64)
    email: str = Field(min_length=1, max_length=255)
    role: str
    is_active: bool = Field(alias="isActive")

    @field_validator("username", "email", "role")
    @classmethod
    def validate_non_blank(cls, value: str) -> str:
        """Reject blank string values."""
        normalized = value.strip()
        if normalized == "":
            raise ValueError("不能为空")
        return normalized

    @field_validator("email")
    @classmethod
    def validate_email(cls, email: str) -> str:
        """Validate email syntax without adding another dependency."""
        if EMAIL_PATTERN.match(email) is None:
            raise ValueError("邮箱格式不合法")
        return email

    @field_validator("role")
    @classmethod
    def validate_role(cls, role: str) -> str:
        """Validate the requested role."""
        if role not in USER_ROLES:
            raise ValueError("角色不合法")
        return role


class UserDisableReq(BaseModel):
    """Optional disable payload."""

    reason: str | None = Field(default=None, max_length=255)


class UserResetPasswordReq(BaseModel):
    """Reset password payload."""

    password: str = Field(min_length=8, max_length=128)


class UserSummaryResp(BaseModel):
    """Summary response used by the user list page."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int
    username: str
    email: str
    role: str
    role_label: str = Field(alias="roleLabel")
    is_active: bool = Field(alias="isActive")
    last_login_at: datetime | None = Field(default=None, alias="lastLoginAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class UserDetailResp(UserSummaryResp):
    """Detail response for one user."""


class UserResetPasswordResp(BaseModel):
    """Response for password reset."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int
    password_updated: bool = Field(alias="passwordUpdated")
    updated_at: datetime = Field(alias="updatedAt")
