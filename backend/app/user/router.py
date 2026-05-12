"""User management routes."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_active_user
from app.auth.model import User
from app.core.database import get_db_session
from app.core.responses import PageResult, Result
from app.user.schema import (
    UserCreateReq,
    UserDetailResp,
    UserDisableReq,
    UserListParams,
    UserResetPasswordReq,
    UserResetPasswordResp,
    UserSummaryResp,
    UserUpdateReq,
)
from app.user.service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["user"])


@router.get("", response_model=Result[PageResult[UserSummaryResp]])
async def list_users(
    params: UserListParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[PageResult[UserSummaryResp]]:
    """Return paginated user records for the admin page."""
    del current_user
    service = UserService(db)
    return Result.success(data=await service.list_users(params))


@router.get("/{user_id}", response_model=Result[UserDetailResp])
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[UserDetailResp]:
    """Return one user detail record."""
    del current_user
    service = UserService(db)
    return Result.success(data=await service.get_user(user_id))


@router.post(
    "",
    response_model=Result[UserDetailResp],
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    payload: UserCreateReq,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[UserDetailResp]:
    """Create one user account."""
    del current_user
    service = UserService(db)
    return Result.success(
        data=await service.create_user(payload),
        code=status.HTTP_201_CREATED,
    )


@router.put("/{user_id}", response_model=Result[UserDetailResp])
async def update_user(
    user_id: int,
    payload: UserUpdateReq,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[UserDetailResp]:
    """Update one user account."""
    service = UserService(db)
    return Result.success(
        data=await service.update_user(
            user_id,
            payload,
            actor_user_id=current_user.id,
        )
    )


@router.post("/{user_id}/enable", response_model=Result[UserDetailResp])
async def enable_user(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[UserDetailResp]:
    """Enable one user account."""
    del current_user
    service = UserService(db)
    return Result.success(data=await service.enable_user(user_id))


@router.post("/{user_id}/disable", response_model=Result[UserDetailResp])
async def disable_user(
    user_id: int,
    payload: UserDisableReq | None = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[UserDetailResp]:
    """Disable one user account."""
    del payload
    service = UserService(db)
    return Result.success(
        data=await service.disable_user(
            user_id,
            actor_user_id=current_user.id,
        )
    )


@router.post(
    "/{user_id}/reset-password",
    response_model=Result[UserResetPasswordResp],
)
async def reset_password(
    user_id: int,
    payload: UserResetPasswordReq,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[UserResetPasswordResp]:
    """Reset one user's password."""
    del current_user
    service = UserService(db)
    return Result.success(
        data=await service.reset_password(user_id, payload)
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """Soft-delete one user account."""
    service = UserService(db)
    await service.delete_user(user_id, actor_user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
