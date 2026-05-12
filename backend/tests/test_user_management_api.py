from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import select, text
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
class UserApiHarness:
    client: httpx.AsyncClient
    session_factory: async_sessionmaker[AsyncSession]
    admin_id: int
    headers: dict[str, str]


@pytest_asyncio.fixture
async def user_api_harness() -> UserApiHarness:
    database_url = _database_url()
    schema_name = f"test_user_management_{uuid.uuid4().hex}"
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
            role="admin",
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        admin_id = admin.id

    token = create_access_token(
        AccessTokenPayload(
            sub=str(admin_id),
            username="admin",
            role="admin",
        )
    )
    headers = {"Authorization": f"Bearer {token}"}

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
        yield UserApiHarness(
            client=client,
            session_factory=session_factory,
            admin_id=admin_id,
            headers=headers,
        )

    app.dependency_overrides.clear()
    await _drop_schema(admin_engine, schema_name)
    await test_engine.dispose()
    await admin_engine.dispose()


async def _create_user(
    harness: UserApiHarness,
    payload: dict[str, Any],
) -> dict[str, Any]:
    response = await harness.client.post(
        "/api/v1/users",
        json=payload,
        headers=harness.headers,
    )
    assert response.status_code == 201
    return response.json()["data"]


@pytest.mark.asyncio
async def test_create_list_update_disable_enable_reset_and_delete_user(
    user_api_harness: UserApiHarness,
) -> None:
    created = await _create_user(
        user_api_harness,
        {
            "username": "lisa",
            "email": "lisa@hify.ai",
            "password": "ChangeMe123!",
            "role": "member",
            "isActive": True,
        },
    )

    assert created["username"] == "lisa"
    assert created["roleLabel"] == "普通用户"
    assert "passwordHash" not in created

    list_response = await user_api_harness.client.get(
        "/api/v1/users",
        params={"keyword": "lis", "role": "member", "isActive": True},
        headers=user_api_harness.headers,
    )
    assert list_response.status_code == 200
    assert list_response.json()["data"]["total"] == 1

    update_response = await user_api_harness.client.put(
        f"/api/v1/users/{created['id']}",
        json={
            "username": "lisa.ops",
            "email": "lisa.ops@hify.ai",
            "role": "member",
            "isActive": True,
        },
        headers=user_api_harness.headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["username"] == "lisa.ops"

    disable_response = await user_api_harness.client.post(
        f"/api/v1/users/{created['id']}/disable",
        json={"reason": "测试禁用"},
        headers=user_api_harness.headers,
    )
    assert disable_response.status_code == 200
    assert disable_response.json()["data"]["isActive"] is False

    enable_response = await user_api_harness.client.post(
        f"/api/v1/users/{created['id']}/enable",
        headers=user_api_harness.headers,
    )
    assert enable_response.status_code == 200
    assert enable_response.json()["data"]["isActive"] is True

    reset_response = await user_api_harness.client.post(
        f"/api/v1/users/{created['id']}/reset-password",
        json={"password": "NewPassword123!"},
        headers=user_api_harness.headers,
    )
    assert reset_response.status_code == 200
    reset_payload = reset_response.json()["data"]
    assert reset_payload["passwordUpdated"] is True
    assert "passwordHash" not in reset_payload

    delete_response = await user_api_harness.client.delete(
        f"/api/v1/users/{created['id']}",
        headers=user_api_harness.headers,
    )
    assert delete_response.status_code == 204

    detail_response = await user_api_harness.client.get(
        f"/api/v1/users/{created['id']}",
        headers=user_api_harness.headers,
    )
    assert detail_response.status_code == 404


@pytest.mark.asyncio
async def test_user_uniqueness_only_checks_active_records(
    user_api_harness: UserApiHarness,
) -> None:
    created = await _create_user(
        user_api_harness,
        {
            "username": "reuse",
            "email": "reuse@hify.ai",
            "password": "ChangeMe123!",
            "role": "member",
            "isActive": True,
        },
    )
    duplicate_response = await user_api_harness.client.post(
        "/api/v1/users",
        json={
            "username": "reuse",
            "email": "reuse2@hify.ai",
            "password": "ChangeMe123!",
            "role": "member",
        },
        headers=user_api_harness.headers,
    )
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["message"] == "用户名已存在"

    await user_api_harness.client.delete(
        f"/api/v1/users/{created['id']}",
        headers=user_api_harness.headers,
    )
    recreated = await _create_user(
        user_api_harness,
        {
            "username": "reuse",
            "email": "reuse@hify.ai",
            "password": "ChangeMe123!",
            "role": "member",
            "isActive": True,
        },
    )
    assert recreated["username"] == "reuse"


@pytest.mark.asyncio
async def test_cannot_disable_or_delete_last_active_admin(
    user_api_harness: UserApiHarness,
) -> None:
    disable_response = await user_api_harness.client.post(
        f"/api/v1/users/{user_api_harness.admin_id}/disable",
        headers=user_api_harness.headers,
    )
    assert disable_response.status_code == 400
    assert disable_response.json()["message"] == "不能禁用当前登录用户"

    async with user_api_harness.session_factory() as session:
        admin = await session.scalar(
            select(User).where(User.id == user_api_harness.admin_id)
        )
        assert admin is not None
        admin_2 = User(
            username="admin2",
            email="admin2@hify.ai",
            password_hash=hash_password("Admin123!"),
            role="admin",
            is_active=True,
        )
        session.add(admin_2)
        await session.commit()

    update_response = await user_api_harness.client.put(
        f"/api/v1/users/{user_api_harness.admin_id}",
        json={
            "username": "admin",
            "email": "admin@hify.ai",
            "role": "member",
            "isActive": True,
        },
        headers=user_api_harness.headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["role"] == "member"


@pytest.mark.asyncio
async def test_disabled_account_cannot_access_auth_me(
    user_api_harness: UserApiHarness,
) -> None:
    async with user_api_harness.session_factory() as session:
        disabled = User(
            username="disabled",
            email="disabled@hify.ai",
            password_hash=hash_password("Admin123!"),
            role="admin",
            is_active=False,
        )
        session.add(disabled)
        await session.commit()
        disabled_id = disabled.id

    token = create_access_token(
        AccessTokenPayload(
            sub=str(disabled_id),
            username="disabled",
            role="admin",
        )
    )
    response = await user_api_harness.client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == 2005


@pytest.mark.asyncio
async def test_login_returns_token_and_current_user_profile(
    user_api_harness: UserApiHarness,
) -> None:
    response = await user_api_harness.client.post(
        "/api/v1/auth/login",
        json={"account": "admin", "password": "Admin123!"},
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["tokenType"] == "Bearer"
    assert isinstance(payload["accessToken"], str)
    assert payload["accessToken"] != ""
    assert payload["expiresIn"] > 0
    assert payload["user"] == {
        "id": user_api_harness.admin_id,
        "username": "admin",
        "email": "admin@hify.ai",
        "role": "admin",
        "roleLabel": "管理员",
    }
    assert "passwordHash" not in payload["user"]

    me_response = await user_api_harness.client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {payload['accessToken']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["data"]["email"] == "admin@hify.ai"

    async with user_api_harness.session_factory() as session:
        admin = await session.scalar(
            select(User).where(User.id == user_api_harness.admin_id)
        )
        assert admin is not None
        assert admin.last_login_at is not None


@pytest.mark.asyncio
async def test_login_rejects_invalid_or_disabled_accounts(
    user_api_harness: UserApiHarness,
) -> None:
    invalid_response = await user_api_harness.client.post(
        "/api/v1/auth/login",
        json={"account": "admin", "password": "wrong-password"},
    )
    assert invalid_response.status_code == 401
    assert invalid_response.json()["code"] == 2001

    async with user_api_harness.session_factory() as session:
        disabled = User(
            username="disabled-login",
            email="disabled-login@hify.ai",
            password_hash=hash_password("Admin123!"),
            role="member",
            is_active=False,
        )
        session.add(disabled)
        await session.commit()

    disabled_response = await user_api_harness.client.post(
        "/api/v1/auth/login",
        json={"account": "disabled-login", "password": "Admin123!"},
    )
    assert disabled_response.status_code == 403
    assert disabled_response.json()["code"] == 2005


@pytest.mark.asyncio
async def test_member_can_access_user_management_after_login(
    user_api_harness: UserApiHarness,
) -> None:
    async with user_api_harness.session_factory() as session:
        member = User(
            username="member",
            email="member@hify.ai",
            password_hash=hash_password("Member123!"),
            role="member",
            is_active=True,
        )
        session.add(member)
        await session.commit()

    login_response = await user_api_harness.client.post(
        "/api/v1/auth/login",
        json={"account": "member@hify.ai", "password": "Member123!"},
    )
    token = login_response.json()["data"]["accessToken"]
    list_response = await user_api_harness.client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200


@pytest.mark.asyncio
async def test_user_management_requires_login(
    user_api_harness: UserApiHarness,
) -> None:
    response = await user_api_harness.client.get("/api/v1/users")
    assert response.status_code == 401
