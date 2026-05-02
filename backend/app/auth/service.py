"""Auth module business services."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schema import LoginPreviewResp


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
