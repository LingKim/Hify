"""Auth module routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schema import LoginPreviewResp
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
