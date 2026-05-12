"""Auth module routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_active_user
from app.auth.model import User
from app.auth.schema import (
    CurrentUserResp,
    LoginPreviewResp,
    LoginReq,
    LoginResp,
)
from app.auth.service import AuthService
from app.core.database import get_db_session
from app.core.responses import Result

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/login-preview", response_model=Result[LoginPreviewResp])
async def login_preview(
    db: AsyncSession = Depends(get_db_session),
) -> Result[LoginPreviewResp]:
    """Return the auth module preview endpoint response."""
    service = AuthService(db)
    return Result.success(data=await service.preview())


@router.post("/login", response_model=Result[LoginResp])
async def login(
    payload: LoginReq,
    db: AsyncSession = Depends(get_db_session),
) -> Result[LoginResp]:
    """Authenticate one local account and return a JWT access token."""
    service = AuthService(db)
    return Result.success(data=await service.login(payload))


@router.get("/me", response_model=Result[CurrentUserResp])
async def me(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> Result[CurrentUserResp]:
    """Return the current authenticated user."""
    service = AuthService(db)
    return Result.success(data=service.build_current_user(current_user))
