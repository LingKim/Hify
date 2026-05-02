"""Auth module routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schema import CurrentUserResp, LoginPreviewResp
from app.auth.service import AuthService
from app.core.auth import AccessTokenPayload
from app.core.database import get_db_session
from app.core.deps import get_current_user
from app.core.responses import Result

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/login-preview", response_model=Result[LoginPreviewResp])
async def login_preview(
    db: AsyncSession = Depends(get_db_session),
) -> Result[LoginPreviewResp]:
    """Return the auth module preview endpoint response."""
    service = AuthService(db)
    return Result.success(data=await service.preview())


@router.get("/me", response_model=Result[CurrentUserResp])
async def me(
    current_user: AccessTokenPayload = Depends(get_current_user),
) -> Result[CurrentUserResp]:
    """Return the current authenticated user."""
    return Result.success(
        data=CurrentUserResp(
            userId=current_user.sub,
            username=current_user.username,
            role=current_user.role,
        )
    )
