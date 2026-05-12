"""Authentication dependencies that validate persisted user state."""

from fastapi import Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.errors import AuthErrorCode
from app.auth.model import User
from app.core.auth import AccessTokenPayload
from app.core.database import get_db_session
from app.core.deps import get_current_user
from app.core.errors import CommonErrorCode
from app.core.exceptions import BizException

ACCOUNT_DISABLED_ERROR_CODE = 2005


async def get_current_active_user(
    token_user: AccessTokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Return the persisted current user if the account is active."""
    try:
        user_id = int(token_user.sub)
    except ValueError as exc:
        raise BizException(
            code=AuthErrorCode.TOKEN_INVALID,
            message="未登录或登录已过期",
            http_status=status.HTTP_401_UNAUTHORIZED,
        ) from exc

    statement = select(User).where(
        User.id == user_id,
        User.deleted_at.is_(None),
    )
    user = await db.scalar(statement)
    if user is None:
        raise BizException(
            code=AuthErrorCode.TOKEN_INVALID,
            message="未登录或登录已过期",
            http_status=status.HTTP_401_UNAUTHORIZED,
        )
    if not user.is_active:
        raise BizException(
            code=AuthErrorCode.ACCOUNT_DISABLED,
            message="账户已禁用",
            http_status=status.HTTP_403_FORBIDDEN,
        )
    return user


async def require_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Return the current user if it has administrator privileges."""
    if current_user.role != "admin":
        raise BizException(
            code=CommonErrorCode.FORBIDDEN,
            message="权限不足",
            http_status=status.HTTP_403_FORBIDDEN,
        )
    return current_user
