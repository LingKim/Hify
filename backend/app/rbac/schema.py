"""RBAC request and response schemas."""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.responses import PageParams

ROLE_CODE_PATTERN = re.compile(r"^[a-z0-9_-]+$")
ROLE_STATUSES = {"enabled", "disabled"}


class RoleListParams(PageParams):
    """List query params for role summaries."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    keyword: str | None = None
    status: str | None = None
    is_system: bool | None = Field(default=None, alias="isSystem")

    @field_validator("status")
    @classmethod
    def validate_status(cls, status: str | None) -> str | None:
        """Validate the optional status filter."""
        if status is not None and status not in ROLE_STATUSES:
            raise ValueError("角色状态不合法")
        return status


class PermissionListParams(BaseModel):
    """List query params for permissions."""

    module: str | None = None
    action: str | None = None
    keyword: str | None = None


class RoleCreateReq(BaseModel):
    """Create payload for one role."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    status: str = "enabled"
    permission_ids: list[int] = Field(
        default_factory=list,
        alias="permissionIds",
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, code: str) -> str:
        """Validate role code syntax."""
        normalized = code.strip()
        if ROLE_CODE_PATTERN.match(normalized) is None:
            raise ValueError("角色编码不合法")
        return normalized

    @field_validator("name", "status")
    @classmethod
    def validate_non_blank(cls, value: str) -> str:
        """Reject blank string values."""
        normalized = value.strip()
        if normalized == "":
            raise ValueError("不能为空")
        return normalized

    @field_validator("status")
    @classmethod
    def validate_status(cls, status: str) -> str:
        """Validate role status."""
        if status not in ROLE_STATUSES:
            raise ValueError("角色状态不合法")
        return status


class RoleUpdateReq(BaseModel):
    """Update payload for one role."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    status: str = "enabled"

    _validate_code = field_validator("code")(RoleCreateReq.validate_code)
    _validate_non_blank = field_validator("name", "status")(
        RoleCreateReq.validate_non_blank
    )
    _validate_status = field_validator("status")(RoleCreateReq.validate_status)


class RolePermissionUpdateReq(BaseModel):
    """Replace permissions for one role."""

    permission_ids: list[int] = Field(alias="permissionIds")


class UserRoleUpdateReq(BaseModel):
    """Replace roles for one user."""

    role_ids: list[int] = Field(alias="roleIds")


class RoleOptionResp(BaseModel):
    """Role option for selectors."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    value: int
    label: str
    code: str
    is_system: bool = Field(alias="isSystem")


class RoleRefResp(BaseModel):
    """Compact role payload used in assignments and auth snapshots."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int
    code: str
    name: str
    status: str
    is_system: bool = Field(alias="isSystem")


class PermissionItemResp(BaseModel):
    """Permission response item."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int
    code: str
    name: str
    module: str
    module_label: str = Field(alias="moduleLabel")
    action: str
    action_label: str = Field(alias="actionLabel")
    description: str | None = None
    is_system: bool = Field(alias="isSystem")


class RoleSummaryResp(BaseModel):
    """Role summary used by list pages."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int
    code: str
    name: str
    description: str | None = None
    status: str
    is_system: bool = Field(alias="isSystem")
    user_count: int = Field(alias="userCount")
    permission_count: int = Field(alias="permissionCount")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class RoleDetailResp(BaseModel):
    """Role detail response."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int
    code: str
    name: str
    description: str | None = None
    status: str
    is_system: bool = Field(alias="isSystem")
    permissions: list[PermissionItemResp]
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class UserRoleAssignmentResp(BaseModel):
    """User role assignment response."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    user_id: int = Field(alias="userId")
    username: str
    email: str
    is_active: bool = Field(alias="isActive")
    roles: list[RoleRefResp]
    permissions: list[str]
