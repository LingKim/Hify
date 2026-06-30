"""RBAC business services."""

from __future__ import annotations

from collections.abc import Iterable

from fastapi import status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.auth.model import User
from app.core.errors import CommonErrorCode
from app.core.exceptions import BizException
from app.core.responses import PageResult
from app.rbac.errors import RbacErrorCode
from app.rbac.model import (
    Permission,
    Role,
    RolePermissionBinding,
    UserRoleBinding,
)
from app.rbac.schema import (
    PermissionItemResp,
    PermissionListParams,
    RoleCreateReq,
    RoleDetailResp,
    RoleListParams,
    RoleOptionResp,
    RoleRefResp,
    RoleSummaryResp,
    RoleUpdateReq,
    UserRoleAssignmentResp,
)

MODULE_LABELS = {
    "provider": "模型提供商",
    "agent": "Agent",
    "tool": "工具",
    "knowledge": "知识库",
    "conversation": "会话",
    "user": "用户",
    "rbac": "权限",
}
ACTION_LABELS = {
    "read": "查看",
    "manage": "管理",
    "use": "使用",
}
RBAC_MANAGE_PERMISSION = "rbac.manage"
MEMBER_ROLE_CODE = "member"


class RbacService:
    """RBAC service with role and permission operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the RBAC service."""
        self.db = db

    async def list_roles(
        self,
        params: RoleListParams,
    ) -> PageResult[RoleSummaryResp]:
        """Return paginated role summaries."""
        filters: list[ColumnElement[bool]] = [Role.deleted_at.is_(None)]
        if params.keyword:
            keyword = f"%{params.keyword.strip()}%"
            filters.append(
                or_(
                    Role.code.ilike(keyword),
                    Role.name.ilike(keyword),
                    Role.description.ilike(keyword),
                )
            )
        if params.status:
            filters.append(Role.status == params.status)
        if params.is_system is not None:
            filters.append(Role.is_system.is_(params.is_system))

        total = int(
            (
                await self.db.execute(
                    select(func.count()).select_from(Role).where(*filters)
                )
            ).scalar_one()
        )
        roles = list(
            (
                await self.db.scalars(
                    select(Role)
                    .where(*filters)
                    .order_by(Role.is_system.desc(), Role.id.asc())
                    .offset(params.offset)
                    .limit(params.page_size)
                )
            ).all()
        )
        return PageResult.create(
            items=[await self._build_role_summary(role) for role in roles],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    async def get_role(self, role_id: int) -> RoleDetailResp:
        """Return one role detail."""
        role = await self._get_role_or_raise(role_id)
        return await self._build_role_detail(role)

    async def create_role(self, payload: RoleCreateReq) -> RoleDetailResp:
        """Create one role and optional permission bindings."""
        await self._ensure_role_code_unique(payload.code)
        permissions = await self._load_permissions(payload.permission_ids)
        role = Role(
            code=payload.code,
            name=payload.name,
            description=payload.description,
            status=payload.status,
            is_system=False,
        )
        self.db.add(role)
        await self.db.flush()
        self.db.add_all(
            [
                RolePermissionBinding(
                    role_id=role.id,
                    permission_id=permission.id,
                )
                for permission in permissions
            ]
        )
        await self._ensure_rbac_manager_exists()
        await self.db.commit()
        return await self.get_role(role.id)

    async def update_role(
        self,
        role_id: int,
        payload: RoleUpdateReq,
    ) -> RoleDetailResp:
        """Update one role."""
        role = await self._get_role_or_raise(role_id)
        if role.is_system and payload.code != role.code:
            raise BizException(
                code=RbacErrorCode.SYSTEM_ROLE_PROTECTED,
                message="系统角色不能修改编码",
                http_status=status.HTTP_400_BAD_REQUEST,
            )
        await self._ensure_role_code_unique(payload.code, exclude_id=role.id)
        previous_status = role.status
        role.code = payload.code
        role.name = payload.name
        role.description = payload.description
        role.status = payload.status
        role.version += 1
        if previous_status == "enabled" and payload.status != "enabled":
            await self._ensure_rbac_manager_exists(exclude_role_id=role.id)
        await self.db.commit()
        return await self.get_role(role_id)

    async def enable_role(self, role_id: int) -> RoleDetailResp:
        """Enable one role."""
        role = await self._get_role_or_raise(role_id)
        role.status = "enabled"
        role.version += 1
        await self.db.commit()
        return await self.get_role(role_id)

    async def disable_role(self, role_id: int) -> RoleDetailResp:
        """Disable one role."""
        role = await self._get_role_or_raise(role_id)
        await self._ensure_rbac_manager_exists(exclude_role_id=role.id)
        role.status = "disabled"
        role.version += 1
        await self.db.commit()
        return await self.get_role(role_id)

    async def delete_role(self, role_id: int) -> None:
        """Soft-delete one non-system role and its bindings."""
        role = await self._get_role_or_raise(role_id)
        if role.is_system:
            raise BizException(
                code=RbacErrorCode.SYSTEM_ROLE_PROTECTED,
                message="系统角色不能删除",
                http_status=status.HTTP_400_BAD_REQUEST,
            )
        await self._ensure_rbac_manager_exists(exclude_role_id=role.id)
        role.soft_delete()
        role.version += 1
        await self._soft_delete_role_bindings(role.id)
        await self.db.commit()

    async def list_permissions(
        self,
        params: PermissionListParams,
    ) -> list[PermissionItemResp]:
        """Return visible permissions."""
        filters: list[ColumnElement[bool]] = [Permission.deleted_at.is_(None)]
        if params.module:
            filters.append(Permission.module == params.module)
        if params.action:
            filters.append(Permission.action == params.action)
        if params.keyword:
            keyword = f"%{params.keyword.strip()}%"
            filters.append(
                or_(
                    Permission.code.ilike(keyword),
                    Permission.name.ilike(keyword),
                    Permission.description.ilike(keyword),
                )
            )
        permissions = list(
            (
                await self.db.scalars(
                    select(Permission)
                    .where(*filters)
                    .order_by(Permission.module.asc(), Permission.id.asc())
                )
            ).all()
        )
        return [self._build_permission_response(item) for item in permissions]

    async def replace_role_permissions(
        self,
        role_id: int,
        permission_ids: list[int],
    ) -> RoleDetailResp:
        """Replace permissions for one role."""
        role = await self._get_role_or_raise(role_id)
        permissions = await self._load_permissions(permission_ids)
        removing_rbac_manage = await self._role_has_permission(
            role.id,
            RBAC_MANAGE_PERMISSION,
        ) and all(
            permission.code != RBAC_MANAGE_PERMISSION
            for permission in permissions
        )
        if removing_rbac_manage:
            await self._ensure_rbac_manager_exists(exclude_role_id=role.id)
        await self._replace_permission_bindings(role.id, permissions)
        role.version += 1
        await self.db.commit()
        return await self.get_role(role_id)

    async def get_user_roles(self, user_id: int) -> UserRoleAssignmentResp:
        """Return one user's role assignment."""
        user = await self._get_user_or_raise(user_id)
        return await self._build_user_assignment(user)

    async def replace_user_roles(
        self,
        user_id: int,
        role_ids: list[int],
    ) -> UserRoleAssignmentResp:
        """Replace roles for one user."""
        if not role_ids:
            raise BizException(
                code=RbacErrorCode.EMPTY_ROLE_ASSIGNMENT,
                message="用户至少需要一个角色",
                http_status=status.HTTP_400_BAD_REQUEST,
            )
        user = await self._get_user_or_raise(user_id)
        roles = await self._load_enabled_roles(role_ids)
        current_has_manage = await self.user_has_permission(
            user.id,
            RBAC_MANAGE_PERMISSION,
        )
        next_has_manage = await self._roles_have_permission(
            [role.id for role in roles],
            RBAC_MANAGE_PERMISSION,
        )
        if current_has_manage and not next_has_manage:
            await self._ensure_rbac_manager_exists(exclude_user_id=user.id)
        await self._replace_user_role_bindings(user.id, roles)
        await self.db.commit()
        return await self.get_user_roles(user.id)

    async def list_role_options(
        self,
        *,
        keyword: str | None = None,
        include_disabled: bool = False,
    ) -> list[RoleOptionResp]:
        """Return role options for selectors."""
        filters: list[ColumnElement[bool]] = [Role.deleted_at.is_(None)]
        if not include_disabled:
            filters.append(Role.status == "enabled")
        if keyword:
            pattern = f"%{keyword.strip()}%"
            filters.append(
                or_(
                    Role.code.ilike(pattern),
                    Role.name.ilike(pattern),
                )
            )
        roles = list(
            (
                await self.db.scalars(
                    select(Role)
                    .where(*filters)
                    .order_by(Role.is_system.desc(), Role.id.asc())
                )
            ).all()
        )
        return [
            RoleOptionResp(
                value=role.id,
                label=role.name,
                code=role.code,
                isSystem=role.is_system,
            )
            for role in roles
        ]

    async def get_user_permission_codes(self, user_id: int) -> list[str]:
        """Return effective permission codes for one active user."""
        statement = (
            select(Permission.code)
            .join(
                RolePermissionBinding,
                and_(
                    RolePermissionBinding.permission_id == Permission.id,
                    RolePermissionBinding.deleted_at.is_(None),
                ),
            )
            .join(
                Role,
                and_(
                    Role.id == RolePermissionBinding.role_id,
                    Role.deleted_at.is_(None),
                    Role.status == "enabled",
                ),
            )
            .join(
                UserRoleBinding,
                and_(
                    UserRoleBinding.role_id == Role.id,
                    UserRoleBinding.deleted_at.is_(None),
                ),
            )
            .where(
                UserRoleBinding.user_id == user_id,
                Permission.deleted_at.is_(None),
            )
            .order_by(Permission.code.asc())
        )
        return list((await self.db.scalars(statement)).all())

    async def get_user_role_refs(self, user_id: int) -> list[RoleRefResp]:
        """Return active roles for one user."""
        roles = await self._load_user_roles(user_id)
        return [self._build_role_ref(role) for role in roles]

    async def user_has_permission(
        self,
        user_id: int,
        permission_code: str,
    ) -> bool:
        """Return whether one user has the permission."""
        statement = (
            select(Permission.id)
            .join(
                RolePermissionBinding,
                and_(
                    RolePermissionBinding.permission_id == Permission.id,
                    RolePermissionBinding.deleted_at.is_(None),
                ),
            )
            .join(
                Role,
                and_(
                    Role.id == RolePermissionBinding.role_id,
                    Role.deleted_at.is_(None),
                    Role.status == "enabled",
                ),
            )
            .join(
                UserRoleBinding,
                and_(
                    UserRoleBinding.role_id == Role.id,
                    UserRoleBinding.deleted_at.is_(None),
                ),
            )
            .where(
                UserRoleBinding.user_id == user_id,
                Permission.deleted_at.is_(None),
                Permission.code == permission_code,
            )
            .limit(1)
        )
        return await self.db.scalar(statement) is not None

    async def _get_role_or_raise(self, role_id: int) -> Role:
        statement = (
            select(Role)
            .where(Role.id == role_id, Role.deleted_at.is_(None))
            .options(
                selectinload(Role.permission_bindings).selectinload(
                    RolePermissionBinding.permission
                )
            )
        )
        role = await self.db.scalar(statement)
        if role is None:
            raise BizException(
                code=RbacErrorCode.ROLE_NOT_FOUND,
                message="角色不存在",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        return role

    async def _get_user_or_raise(self, user_id: int) -> User:
        user = await self.db.scalar(
            select(User).where(
                User.id == user_id,
                User.deleted_at.is_(None),
            )
        )
        if user is None:
            raise BizException(
                code=CommonErrorCode.RESOURCE_NOT_FOUND,
                message="用户不存在",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        return user

    async def _ensure_role_code_unique(
        self,
        code: str,
        *,
        exclude_id: int | None = None,
    ) -> None:
        filters = [Role.code == code, Role.deleted_at.is_(None)]
        if exclude_id is not None:
            filters.append(Role.id != exclude_id)
        if await self.db.scalar(select(Role.id).where(*filters)) is not None:
            raise BizException(
                code=RbacErrorCode.ROLE_CODE_EXISTS,
                message="角色编码已存在",
                http_status=status.HTTP_409_CONFLICT,
            )

    async def _load_permissions(
        self,
        permission_ids: Iterable[int],
    ) -> list[Permission]:
        ids = sorted(set(permission_ids))
        if not ids:
            return []
        permissions = list(
            (
                await self.db.scalars(
                    select(Permission).where(
                        Permission.id.in_(ids),
                        Permission.deleted_at.is_(None),
                    )
                )
            ).all()
        )
        if len(permissions) != len(ids):
            raise BizException(
                code=RbacErrorCode.PERMISSION_NOT_FOUND,
                message="权限不存在",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        return permissions

    async def _load_enabled_roles(self, role_ids: Iterable[int]) -> list[Role]:
        ids = sorted(set(role_ids))
        roles = list(
            (
                await self.db.scalars(
                    select(Role).where(
                        Role.id.in_(ids),
                        Role.deleted_at.is_(None),
                    )
                )
            ).all()
        )
        if len(roles) != len(ids):
            raise BizException(
                code=RbacErrorCode.ROLE_NOT_FOUND,
                message="角色不存在",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        if any(role.status != "enabled" for role in roles):
            raise BizException(
                code=RbacErrorCode.ROLE_DISABLED,
                message="角色已禁用，不能分配",
                http_status=status.HTTP_400_BAD_REQUEST,
            )
        return roles

    async def _load_user_roles(self, user_id: int) -> list[Role]:
        return list(
            (
                await self.db.scalars(
                    select(Role)
                    .join(
                        UserRoleBinding,
                        and_(
                            UserRoleBinding.role_id == Role.id,
                            UserRoleBinding.deleted_at.is_(None),
                        ),
                    )
                    .where(
                        UserRoleBinding.user_id == user_id,
                        Role.deleted_at.is_(None),
                        Role.status == "enabled",
                    )
                    .order_by(Role.is_system.desc(), Role.id.asc())
                )
            ).all()
        )

    async def _replace_permission_bindings(
        self,
        role_id: int,
        permissions: list[Permission],
    ) -> None:
        existing = list(
            (
                await self.db.scalars(
                    select(RolePermissionBinding).where(
                        RolePermissionBinding.role_id == role_id,
                        RolePermissionBinding.deleted_at.is_(None),
                    )
                )
            ).all()
        )
        for binding in existing:
            binding.soft_delete()
            binding.version += 1
        self.db.add_all(
            [
                RolePermissionBinding(
                    role_id=role_id,
                    permission_id=permission.id,
                )
                for permission in permissions
            ]
        )

    async def _replace_user_role_bindings(
        self,
        user_id: int,
        roles: list[Role],
    ) -> None:
        existing = list(
            (
                await self.db.scalars(
                    select(UserRoleBinding).where(
                        UserRoleBinding.user_id == user_id,
                        UserRoleBinding.deleted_at.is_(None),
                    )
                )
            ).all()
        )
        for binding in existing:
            binding.soft_delete()
            binding.version += 1
        self.db.add_all(
            [
                UserRoleBinding(user_id=user_id, role_id=role.id)
                for role in roles
            ]
        )

    async def _soft_delete_role_bindings(self, role_id: int) -> None:
        for model in (UserRoleBinding, RolePermissionBinding):
            bindings = list(
                (
                    await self.db.scalars(
                        select(model).where(
                            model.role_id == role_id,
                            model.deleted_at.is_(None),
                        )
                    )
                ).all()
            )
            for binding in bindings:
                binding.soft_delete()
                binding.version += 1

    async def _role_has_permission(
        self,
        role_id: int,
        permission_code: str,
    ) -> bool:
        return await self.db.scalar(
            select(Permission.id)
            .join(
                RolePermissionBinding,
                RolePermissionBinding.permission_id == Permission.id,
            )
            .where(
                RolePermissionBinding.role_id == role_id,
                RolePermissionBinding.deleted_at.is_(None),
                Permission.deleted_at.is_(None),
                Permission.code == permission_code,
            )
            .limit(1)
        ) is not None

    async def _roles_have_permission(
        self,
        role_ids: list[int],
        permission_code: str,
    ) -> bool:
        if not role_ids:
            return False
        return await self.db.scalar(
            select(Permission.id)
            .join(
                RolePermissionBinding,
                RolePermissionBinding.permission_id == Permission.id,
            )
            .where(
                RolePermissionBinding.role_id.in_(role_ids),
                RolePermissionBinding.deleted_at.is_(None),
                Permission.deleted_at.is_(None),
                Permission.code == permission_code,
            )
            .limit(1)
        ) is not None

    async def _ensure_rbac_manager_exists(
        self,
        *,
        exclude_user_id: int | None = None,
        exclude_role_id: int | None = None,
    ) -> None:
        filters = [
            User.deleted_at.is_(None),
            User.is_active.is_(True),
            UserRoleBinding.deleted_at.is_(None),
            Role.deleted_at.is_(None),
            Role.status == "enabled",
            RolePermissionBinding.deleted_at.is_(None),
            Permission.deleted_at.is_(None),
            Permission.code == RBAC_MANAGE_PERMISSION,
        ]
        if exclude_user_id is not None:
            filters.append(User.id != exclude_user_id)
        if exclude_role_id is not None:
            filters.append(Role.id != exclude_role_id)
        count = int(
            (
                await self.db.execute(
                    select(func.count(func.distinct(User.id)))
                    .select_from(User)
                    .join(UserRoleBinding, UserRoleBinding.user_id == User.id)
                    .join(Role, Role.id == UserRoleBinding.role_id)
                    .join(
                        RolePermissionBinding,
                        RolePermissionBinding.role_id == Role.id,
                    )
                    .join(
                        Permission,
                        Permission.id == RolePermissionBinding.permission_id,
                    )
                    .where(*filters)
                )
            ).scalar_one()
        )
        if count == 0:
            raise BizException(
                code=RbacErrorCode.RBAC_SELF_LOCK_RISK,
                message="至少需要保留一个权限管理员",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

    async def _build_role_summary(self, role: Role) -> RoleSummaryResp:
        user_count = int(
            (
                await self.db.execute(
                    select(func.count())
                    .select_from(UserRoleBinding)
                    .where(
                        UserRoleBinding.role_id == role.id,
                        UserRoleBinding.deleted_at.is_(None),
                    )
                )
            ).scalar_one()
        )
        permission_count = int(
            (
                await self.db.execute(
                    select(func.count())
                    .select_from(RolePermissionBinding)
                    .where(
                        RolePermissionBinding.role_id == role.id,
                        RolePermissionBinding.deleted_at.is_(None),
                    )
                )
            ).scalar_one()
        )
        return RoleSummaryResp(
            id=role.id,
            code=role.code,
            name=role.name,
            description=role.description,
            status=role.status,
            isSystem=role.is_system,
            userCount=user_count,
            permissionCount=permission_count,
            createdAt=role.created_at,
            updatedAt=role.updated_at,
        )

    async def _build_role_detail(self, role: Role) -> RoleDetailResp:
        permissions = list(
            (
                await self.db.scalars(
                    select(Permission)
                    .join(
                        RolePermissionBinding,
                        RolePermissionBinding.permission_id == Permission.id,
                    )
                    .where(
                        RolePermissionBinding.role_id == role.id,
                        RolePermissionBinding.deleted_at.is_(None),
                        Permission.deleted_at.is_(None),
                    )
                    .order_by(Permission.id.asc())
                )
            ).all()
        )
        return RoleDetailResp(
            id=role.id,
            code=role.code,
            name=role.name,
            description=role.description,
            status=role.status,
            isSystem=role.is_system,
            permissions=[
                self._build_permission_response(permission)
                for permission in permissions
            ],
            createdAt=role.created_at,
            updatedAt=role.updated_at,
        )

    async def _build_user_assignment(
        self,
        user: User,
    ) -> UserRoleAssignmentResp:
        roles = await self._load_user_roles(user.id)
        return UserRoleAssignmentResp(
            userId=user.id,
            username=user.username,
            email=user.email,
            isActive=user.is_active,
            roles=[self._build_role_ref(role) for role in roles],
            permissions=await self.get_user_permission_codes(user.id),
        )

    def _build_role_ref(self, role: Role) -> RoleRefResp:
        return RoleRefResp(
            id=role.id,
            code=role.code,
            name=role.name,
            status=role.status,
            isSystem=role.is_system,
        )

    def _build_permission_response(
        self,
        permission: Permission,
    ) -> PermissionItemResp:
        return PermissionItemResp(
            id=permission.id,
            code=permission.code,
            name=permission.name,
            module=permission.module,
            moduleLabel=MODULE_LABELS.get(permission.module, permission.module),
            action=permission.action,
            actionLabel=ACTION_LABELS.get(permission.action, permission.action),
            description=permission.description,
            isSystem=permission.is_system,
        )
