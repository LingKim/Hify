"""Auth module business services."""

from fastapi import status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.errors import AuthErrorCode
from app.auth.model import User
from app.auth.password import verify_password
from app.auth.schema import (
    CurrentUserResp,
    LoginPreviewResp,
    LoginReq,
    LoginResp,
)
from app.core.auth import AccessTokenPayload, create_access_token
from app.core.config import get_settings
from app.core.database import utc_now
from app.core.exceptions import BizException

ROLE_LABELS = {
    "admin": "管理员",
    "member": "普通用户",
}


class AuthService:
    """Auth service placeholder."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the auth service."""
        self.db = db

    async def preview(self) -> LoginPreviewResp:
        """Return the auth module preview payload."""
        return LoginPreviewResp(
            module="auth",
            status="skeleton_ready",
            capabilities=[
                "用户名密码认证",
                "Token 鉴权",
                "角色与权限控制",
            ],
        )

    async def login(self, payload: LoginReq) -> LoginResp:
        """Authenticate a local user and return an access token."""
        account = payload.account.strip()
        statement = select(User).where(
            User.deleted_at.is_(None),
            or_(User.username == account, User.email == account),
        )
        user = await self.db.scalar(statement)
        if user is None or not verify_password(
            payload.password,
            user.password_hash,
        ):
            raise BizException(
                code=AuthErrorCode.INVALID_CREDENTIALS,
                message="用户名或密码错误",
                http_status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            raise BizException(
                code=AuthErrorCode.ACCOUNT_DISABLED,
                message="账户已禁用",
                http_status=status.HTTP_403_FORBIDDEN,
            )

        settings = get_settings()
        expires_in = settings.jwt_access_token_ttl_seconds
        access_token = create_access_token(
            AccessTokenPayload(
                sub=str(user.id),
                username=user.username,
                role=user.role,
            ),
            expires_in_seconds=expires_in,
        )
        user.last_login_at = utc_now()
        user.version += 1
        await self.db.commit()
        await self.db.refresh(user)
        return LoginResp(
            accessToken=access_token,
            tokenType="Bearer",
            expiresIn=expires_in,
            user=self.build_current_user(user),
        )

    def build_current_user(self, user: User) -> CurrentUserResp:
        """Build the current user payload shared by login and /me."""
        return CurrentUserResp(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            roleLabel=ROLE_LABELS.get(user.role, user.role),
        )
