"""User management business services."""

from __future__ import annotations

from fastapi import status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.auth.model import User
from app.auth.password import hash_password
from app.core.errors import CommonErrorCode
from app.core.exceptions import BizException
from app.core.responses import PageResult
from app.user.schema import (
    ROLE_LABELS,
    UserCreateReq,
    UserDetailResp,
    UserListParams,
    UserResetPasswordReq,
    UserResetPasswordResp,
    UserSummaryResp,
    UserUpdateReq,
)

ADMIN_ROLE = "admin"


class UserService:
    """User service with account management operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the user service."""
        self.db = db

    async def list_users(
        self,
        params: UserListParams,
    ) -> PageResult[UserSummaryResp]:
        """Return paginated user summaries."""
        filters: list[ColumnElement[bool]] = [User.deleted_at.is_(None)]
        if params.keyword:
            keyword = f"%{params.keyword.strip()}%"
            filters.append(
                or_(
                    User.username.ilike(keyword),
                    User.email.ilike(keyword),
                )
            )
        if params.role:
            filters.append(User.role == params.role)
        if params.is_active is not None:
            filters.append(User.is_active.is_(params.is_active))

        total_statement = select(func.count()).select_from(User).where(
            *filters
        )
        total = int((await self.db.execute(total_statement)).scalar_one())

        statement = (
            select(User)
            .where(*filters)
            .order_by(User.created_at.desc(), User.id.desc())
            .offset(params.offset)
            .limit(params.page_size)
        )
        users = list((await self.db.scalars(statement)).all())
        return PageResult.create(
            items=[self._build_summary_response(user) for user in users],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    async def get_user(self, user_id: int) -> UserDetailResp:
        """Return one user detail payload."""
        user = await self._get_user_or_raise(user_id)
        return self._build_detail_response(user)

    async def create_user(self, payload: UserCreateReq) -> UserDetailResp:
        """Create one user account."""
        await self._ensure_username_unique(payload.username)
        await self._ensure_email_unique(payload.email)

        user = User(
            username=payload.username,
            email=payload.email,
            password_hash=hash_password(payload.password),
            role=payload.role,
            is_active=payload.is_active,
        )
        self.db.add(user)
        await self.db.commit()
        return await self.get_user(user.id)

    async def update_user(
        self,
        user_id: int,
        payload: UserUpdateReq,
        *,
        actor_user_id: int,
    ) -> UserDetailResp:
        """Update one user account."""
        user = await self._get_user_or_raise(user_id)
        await self._ensure_username_unique(
            payload.username,
            exclude_id=user_id,
        )
        await self._ensure_email_unique(payload.email, exclude_id=user_id)

        await self._ensure_admin_not_removed(
            target_user=user,
            next_role=payload.role,
            next_is_active=payload.is_active,
        )
        if actor_user_id == user.id and not payload.is_active:
            raise BizException(
                code=CommonErrorCode.VALIDATION_ERROR,
                message="不能禁用当前登录用户",
            )

        user.username = payload.username
        user.email = payload.email
        user.role = payload.role
        user.is_active = payload.is_active
        user.version += 1

        await self.db.commit()
        return await self.get_user(user_id)

    async def enable_user(self, user_id: int) -> UserDetailResp:
        """Enable one user account."""
        user = await self._get_user_or_raise(user_id)
        user.is_active = True
        user.version += 1
        await self.db.commit()
        return await self.get_user(user_id)

    async def disable_user(
        self,
        user_id: int,
        *,
        actor_user_id: int,
    ) -> UserDetailResp:
        """Disable one user account."""
        user = await self._get_user_or_raise(user_id)
        if actor_user_id == user.id:
            raise BizException(
                code=CommonErrorCode.VALIDATION_ERROR,
                message="不能禁用当前登录用户",
            )
        await self._ensure_admin_not_removed(
            target_user=user,
            next_role=user.role,
            next_is_active=False,
        )
        user.is_active = False
        user.version += 1
        await self.db.commit()
        return await self.get_user(user_id)

    async def reset_password(
        self,
        user_id: int,
        payload: UserResetPasswordReq,
    ) -> UserResetPasswordResp:
        """Reset one user's password."""
        user = await self._get_user_or_raise(user_id)
        user.password_hash = hash_password(payload.password)
        user.version += 1
        await self.db.commit()
        await self.db.refresh(user)
        return UserResetPasswordResp(
            id=user.id,
            passwordUpdated=True,
            updatedAt=user.updated_at,
        )

    async def delete_user(
        self,
        user_id: int,
        *,
        actor_user_id: int,
    ) -> None:
        """Soft-delete one user account."""
        user = await self._get_user_or_raise(user_id)
        if actor_user_id == user.id:
            raise BizException(
                code=CommonErrorCode.VALIDATION_ERROR,
                message="不能删除当前登录用户",
            )
        await self._ensure_admin_not_removed(
            target_user=user,
            next_role=user.role,
            next_is_active=False,
        )
        user.soft_delete()
        user.version += 1
        await self.db.commit()

    async def _get_user_or_raise(self, user_id: int) -> User:
        statement = select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None),
        )
        user = await self.db.scalar(statement)
        if user is None:
            raise BizException(
                code=CommonErrorCode.RESOURCE_NOT_FOUND,
                message="用户不存在",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        return user

    async def _ensure_username_unique(
        self,
        username: str,
        *,
        exclude_id: int | None = None,
    ) -> None:
        filters = [User.username == username, User.deleted_at.is_(None)]
        if exclude_id is not None:
            filters.append(User.id != exclude_id)
        exists = await self.db.scalar(select(User.id).where(*filters))
        if exists is not None:
            raise BizException(
                code=CommonErrorCode.RESOURCE_ALREADY_EXISTS,
                message="用户名已存在",
                http_status=status.HTTP_409_CONFLICT,
            )

    async def _ensure_email_unique(
        self,
        email: str,
        *,
        exclude_id: int | None = None,
    ) -> None:
        filters = [User.email == email, User.deleted_at.is_(None)]
        if exclude_id is not None:
            filters.append(User.id != exclude_id)
        exists = await self.db.scalar(select(User.id).where(*filters))
        if exists is not None:
            raise BizException(
                code=CommonErrorCode.RESOURCE_ALREADY_EXISTS,
                message="邮箱已存在",
                http_status=status.HTTP_409_CONFLICT,
            )

    async def _ensure_admin_not_removed(
        self,
        *,
        target_user: User,
        next_role: str,
        next_is_active: bool,
    ) -> None:
        if target_user.role != ADMIN_ROLE or not target_user.is_active:
            return
        if next_role == ADMIN_ROLE and next_is_active:
            return

        active_admin_count = await self._count_active_admins(
            exclude_user_id=target_user.id,
        )
        if active_admin_count == 0:
            raise BizException(
                code=CommonErrorCode.VALIDATION_ERROR,
                message="至少需要保留一个启用的管理员",
            )

    async def _count_active_admins(
        self,
        *,
        exclude_user_id: int | None = None,
    ) -> int:
        filters = [
            User.deleted_at.is_(None),
            User.is_active.is_(True),
            User.role == ADMIN_ROLE,
        ]
        if exclude_user_id is not None:
            filters.append(User.id != exclude_user_id)
        statement = select(func.count()).select_from(User).where(*filters)
        return int((await self.db.execute(statement)).scalar_one())

    def _build_summary_response(self, user: User) -> UserSummaryResp:
        return UserSummaryResp(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            roleLabel=ROLE_LABELS.get(user.role, user.role),
            isActive=user.is_active,
            lastLoginAt=user.last_login_at,
            createdAt=user.created_at,
            updatedAt=user.updated_at,
        )

    def _build_detail_response(self, user: User) -> UserDetailResp:
        return UserDetailResp(
            **self._build_summary_response(user).model_dump(by_alias=True)
        )
