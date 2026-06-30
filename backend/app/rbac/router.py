"""RBAC module routes."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.responses import PageResult, Result
from app.rbac.deps import require_permission
from app.rbac.schema import (
    PermissionItemResp,
    PermissionListParams,
    RoleCreateReq,
    RoleDetailResp,
    RoleListParams,
    RoleOptionResp,
    RolePermissionUpdateReq,
    RoleSummaryResp,
    RoleUpdateReq,
    UserRoleAssignmentResp,
    UserRoleUpdateReq,
)
from app.rbac.service import RbacService

router = APIRouter(prefix="/api/v1/rbac", tags=["rbac"])


@router.get("/roles", response_model=Result[PageResult[RoleSummaryResp]])
async def list_roles(
    params: RoleListParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    _current_user: object = Depends(require_permission("rbac.read")),
) -> Result[PageResult[RoleSummaryResp]]:
    """Return paginated role records."""
    service = RbacService(db)
    return Result.success(data=await service.list_roles(params))


@router.get("/roles/options", response_model=Result[list[RoleOptionResp]])
async def list_role_options(
    keyword: str | None = None,
    include_disabled: bool = False,
    db: AsyncSession = Depends(get_db_session),
    _current_user: object = Depends(require_permission("rbac.read")),
) -> Result[list[RoleOptionResp]]:
    """Return role options for selectors."""
    service = RbacService(db)
    return Result.success(
        data=await service.list_role_options(
            keyword=keyword,
            include_disabled=include_disabled,
        )
    )


@router.post(
    "/roles",
    response_model=Result[RoleDetailResp],
    status_code=status.HTTP_201_CREATED,
)
async def create_role(
    payload: RoleCreateReq,
    db: AsyncSession = Depends(get_db_session),
    _current_user: object = Depends(require_permission("rbac.manage")),
) -> Result[RoleDetailResp]:
    """Create one role."""
    service = RbacService(db)
    return Result.success(
        data=await service.create_role(payload),
        code=status.HTTP_201_CREATED,
    )


@router.get("/roles/{role_id}", response_model=Result[RoleDetailResp])
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_db_session),
    _current_user: object = Depends(require_permission("rbac.read")),
) -> Result[RoleDetailResp]:
    """Return one role detail."""
    service = RbacService(db)
    return Result.success(data=await service.get_role(role_id))


@router.put("/roles/{role_id}", response_model=Result[RoleDetailResp])
async def update_role(
    role_id: int,
    payload: RoleUpdateReq,
    db: AsyncSession = Depends(get_db_session),
    _current_user: object = Depends(require_permission("rbac.manage")),
) -> Result[RoleDetailResp]:
    """Update one role."""
    service = RbacService(db)
    return Result.success(data=await service.update_role(role_id, payload))


@router.post("/roles/{role_id}/enable", response_model=Result[RoleDetailResp])
async def enable_role(
    role_id: int,
    db: AsyncSession = Depends(get_db_session),
    _current_user: object = Depends(require_permission("rbac.manage")),
) -> Result[RoleDetailResp]:
    """Enable one role."""
    service = RbacService(db)
    return Result.success(data=await service.enable_role(role_id))


@router.post("/roles/{role_id}/disable", response_model=Result[RoleDetailResp])
async def disable_role(
    role_id: int,
    db: AsyncSession = Depends(get_db_session),
    _current_user: object = Depends(require_permission("rbac.manage")),
) -> Result[RoleDetailResp]:
    """Disable one role."""
    service = RbacService(db)
    return Result.success(data=await service.disable_role(role_id))


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db_session),
    _current_user: object = Depends(require_permission("rbac.manage")),
) -> Response:
    """Soft-delete one role."""
    service = RbacService(db)
    await service.delete_role(role_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/permissions", response_model=Result[list[PermissionItemResp]])
async def list_permissions(
    params: PermissionListParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    _current_user: object = Depends(require_permission("rbac.read")),
) -> Result[list[PermissionItemResp]]:
    """Return system permissions."""
    service = RbacService(db)
    return Result.success(data=await service.list_permissions(params))


@router.put(
    "/roles/{role_id}/permissions",
    response_model=Result[RoleDetailResp],
)
async def replace_role_permissions(
    role_id: int,
    payload: RolePermissionUpdateReq,
    db: AsyncSession = Depends(get_db_session),
    _current_user: object = Depends(require_permission("rbac.manage")),
) -> Result[RoleDetailResp]:
    """Replace permissions for one role."""
    service = RbacService(db)
    return Result.success(
        data=await service.replace_role_permissions(
            role_id,
            payload.permission_ids,
        )
    )


@router.get(
    "/users/{user_id}/roles",
    response_model=Result[UserRoleAssignmentResp],
)
async def get_user_roles(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    _current_user: object = Depends(require_permission("rbac.read")),
) -> Result[UserRoleAssignmentResp]:
    """Return one user's role assignment."""
    service = RbacService(db)
    return Result.success(data=await service.get_user_roles(user_id))


@router.put(
    "/users/{user_id}/roles",
    response_model=Result[UserRoleAssignmentResp],
)
async def replace_user_roles(
    user_id: int,
    payload: UserRoleUpdateReq,
    db: AsyncSession = Depends(get_db_session),
    _current_user: object = Depends(require_permission("rbac.manage")),
) -> Result[UserRoleAssignmentResp]:
    """Replace roles for one user."""
    service = RbacService(db)
    return Result.success(
        data=await service.replace_user_roles(user_id, payload.role_ids)
    )
