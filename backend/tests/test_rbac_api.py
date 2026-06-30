from __future__ import annotations

import os
import uuid
from dataclasses import dataclass

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.auth.model import User
from app.auth.password import hash_password
from app.core.auth import AccessTokenPayload, create_access_token
from app.core.database import Base, get_db_session
from app.main import app
from app.rbac.model import (
    Permission,
    Role,
    RolePermissionBinding,
    UserRoleBinding,
)


def _database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    env_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        ".env.development",
    )
    values: dict[str, str] = {}
    with open(env_path, encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values["DATABASE_URL"]


async def _create_schema(engine: AsyncEngine, schema_name: str) -> None:
    async with engine.begin() as connection:
        await connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))


async def _create_tables(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def _drop_schema(engine: AsyncEngine, schema_name: str) -> None:
    async with engine.begin() as connection:
        await connection.execute(text(f'DROP SCHEMA "{schema_name}" CASCADE'))


@dataclass
class RbacApiHarness:
    client: httpx.AsyncClient
    session_factory: async_sessionmaker[AsyncSession]
    admin_id: int
    member_id: int
    admin_headers: dict[str, str]
    member_headers: dict[str, str]


async def _seed_permission(
    session: AsyncSession,
    *,
    code: str,
    name: str,
    module: str,
    action: str,
) -> Permission:
    permission = Permission(
        code=code,
        name=name,
        module=module,
        action=action,
        description=name,
        is_system=True,
    )
    session.add(permission)
    await session.flush()
    return permission


@pytest_asyncio.fixture
async def rbac_api_harness() -> RbacApiHarness:
    database_url = _database_url()
    schema_name = f"test_rbac_{uuid.uuid4().hex}"
    admin_engine = create_async_engine(database_url)
    test_engine = create_async_engine(
        database_url,
        connect_args={
            "server_settings": {
                "search_path": schema_name,
            }
        },
    )
    session_factory = async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False,
        autoflush=False,
    )

    await _create_schema(admin_engine, schema_name)
    await _create_tables(test_engine)

    async with session_factory() as session:
        admin = User(
            username="admin",
            email="admin@hify.ai",
            password_hash=hash_password("Admin123!"),
            is_active=True,
        )
        member = User(
            username="member",
            email="member@hify.ai",
            password_hash=hash_password("Member123!"),
            is_active=True,
        )
        session.add_all([admin, member])
        await session.flush()

        admin_role = Role(
            code="admin",
            name="管理员",
            description="系统管理员",
            status="enabled",
            is_system=True,
        )
        member_role = Role(
            code="member",
            name="普通用户",
            description="普通成员",
            status="enabled",
            is_system=True,
        )
        session.add_all([admin_role, member_role])
        await session.flush()

        rbac_read = await _seed_permission(
            session,
            code="rbac.read",
            name="查看角色权限",
            module="rbac",
            action="read",
        )
        rbac_manage = await _seed_permission(
            session,
            code="rbac.manage",
            name="管理角色权限",
            module="rbac",
            action="manage",
        )
        conversation_use = await _seed_permission(
            session,
            code="conversation.use",
            name="使用 Web 对话",
            module="conversation",
            action="use",
        )

        session.add_all(
            [
                UserRoleBinding(user_id=admin.id, role_id=admin_role.id),
                UserRoleBinding(user_id=member.id, role_id=member_role.id),
                RolePermissionBinding(
                    role_id=admin_role.id,
                    permission_id=rbac_read.id,
                ),
                RolePermissionBinding(
                    role_id=admin_role.id,
                    permission_id=rbac_manage.id,
                ),
                RolePermissionBinding(
                    role_id=member_role.id,
                    permission_id=conversation_use.id,
                ),
            ]
        )
        await session.commit()
        admin_id = admin.id
        member_id = member.id

    admin_token = create_access_token(
        AccessTokenPayload(
            sub=str(admin_id),
            username="admin",
            role="admin",
        )
    )
    member_token = create_access_token(
        AccessTokenPayload(
            sub=str(member_id),
            username="member",
            role="member",
        )
    )

    async def override_get_db_session():  # type: ignore[no-untyped-def]
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        yield RbacApiHarness(
            client=client,
            session_factory=session_factory,
            admin_id=admin_id,
            member_id=member_id,
            admin_headers={"Authorization": f"Bearer {admin_token}"},
            member_headers={"Authorization": f"Bearer {member_token}"},
        )

    app.dependency_overrides.clear()
    await _drop_schema(admin_engine, schema_name)
    await test_engine.dispose()
    await admin_engine.dispose()


@pytest.mark.asyncio
async def test_auth_me_returns_roles_and_permissions(
    rbac_api_harness: RbacApiHarness,
) -> None:
    response = await rbac_api_harness.client.get(
        "/api/v1/auth/me",
        headers=rbac_api_harness.admin_headers,
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["roles"][0]["code"] == "admin"
    assert "rbac.manage" in payload["permissions"]
    assert "role" not in payload
    assert "roleLabel" not in payload


@pytest.mark.asyncio
async def test_admin_can_manage_roles_and_assign_user_roles(
    rbac_api_harness: RbacApiHarness,
) -> None:
    permissions_response = await rbac_api_harness.client.get(
        "/api/v1/rbac/permissions",
        headers=rbac_api_harness.admin_headers,
    )
    assert permissions_response.status_code == 200
    permissions = {
        item["code"]: item["id"]
        for item in permissions_response.json()["data"]
    }
    permission_id = permissions["conversation.use"]
    rbac_read_id = permissions["rbac.read"]

    create_response = await rbac_api_harness.client.post(
        "/api/v1/rbac/roles",
        json={
            "code": "ops",
            "name": "运维",
            "description": "运维角色",
            "status": "enabled",
            "permissionIds": [permission_id],
        },
        headers=rbac_api_harness.admin_headers,
    )
    assert create_response.status_code == 201
    role = create_response.json()["data"]
    assert role["code"] == "ops"
    assert role["permissions"][0]["id"] == permission_id

    replace_permissions_response = await rbac_api_harness.client.put(
        f"/api/v1/rbac/roles/{role['id']}/permissions",
        json={"permissionIds": [rbac_read_id]},
        headers=rbac_api_harness.admin_headers,
    )
    assert replace_permissions_response.status_code == 200
    assert replace_permissions_response.json()["data"]["permissions"] == [
        {
            "id": rbac_read_id,
            "code": "rbac.read",
            "name": "查看角色权限",
            "module": "rbac",
            "moduleLabel": "权限",
            "action": "read",
            "actionLabel": "查看",
            "description": "查看角色权限",
            "isSystem": True,
        }
    ]

    assign_response = await rbac_api_harness.client.put(
        f"/api/v1/rbac/users/{rbac_api_harness.member_id}/roles",
        json={"roleIds": [role["id"]]},
        headers=rbac_api_harness.admin_headers,
    )
    assert assign_response.status_code == 200
    assert assign_response.json()["data"]["roles"][0]["code"] == "ops"


@pytest.mark.asyncio
async def test_member_without_rbac_permission_is_forbidden(
    rbac_api_harness: RbacApiHarness,
) -> None:
    response = await rbac_api_harness.client.get(
        "/api/v1/rbac/roles",
        headers=rbac_api_harness.member_headers,
    )

    assert response.status_code == 403
