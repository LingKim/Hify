"""RBAC dependencies for route authorization."""

from collections.abc import Callable

from fastapi import Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_active_user
from app.auth.model import User
from app.core.database import get_db_session
from app.core.errors import CommonErrorCode
from app.core.exceptions import BizException
from app.rbac.service import RbacService


def require_permission(permission_code: str) -> Callable[..., object]:
    """Build a FastAPI dependency requiring one permission."""

    async def dependency(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session),
    ) -> User:
        service = RbacService(db)
        has_permission = await service.user_has_permission(
            current_user.id,
            permission_code,
        )
        if not has_permission:
            raise BizException(
                code=CommonErrorCode.FORBIDDEN,
                message="权限不足",
                http_status=status.HTTP_403_FORBIDDEN,
            )
        return current_user

    return dependency
