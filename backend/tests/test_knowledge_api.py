from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.auth.model import User
from app.auth.password import hash_password
from app.core.auth import AccessTokenPayload, create_access_token
from app.core.config import get_settings
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
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))


async def _create_tables(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def _drop_schema(engine: AsyncEngine, schema_name: str) -> None:
    async with engine.begin() as connection:
        await connection.execute(text(f'DROP SCHEMA "{schema_name}" CASCADE'))


class FakeEmbeddingClient:
    def __init__(self, **kwargs: Any) -> None:
        del kwargs

    async def embed(self, input_text: str) -> list[float]:
        del input_text
        return [0.1, 0.2, 0.3]


@dataclass
class KnowledgeApiHarness:
    client: httpx.AsyncClient
    session_factory: async_sessionmaker[AsyncSession]
    user_id: int
    headers: dict[str, str]


@pytest_asyncio.fixture
async def knowledge_api_harness(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> KnowledgeApiHarness:
    database_url = _database_url()
    schema_name = f"test_knowledge_{uuid.uuid4().hex}"
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

    monkeypatch.setenv("EMBEDDDINGS_SECRET_KEY", "test-key")
    monkeypatch.setenv("EMBEDDINGS_DIMENSIONS", "3")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "app.knowledge.service.DEFAULT_STORAGE_DIR",
        tmp_path,
    )
    monkeypatch.setattr(
        "app.knowledge.service.SiliconFlowEmbeddingClient",
        FakeEmbeddingClient,
    )

    try:
        await _create_schema(admin_engine, schema_name)
    except (ConnectionRefusedError, OSError, SQLAlchemyError) as exc:
        await test_engine.dispose()
        await admin_engine.dispose()
        pytest.skip(f"PostgreSQL is not available for API test: {exc}")
    await _create_tables(test_engine)

    async with session_factory() as session:
        user = User(
            username="member",
            email="member@hify.ai",
            password_hash=hash_password("Member123!"),
            role="member",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        user_id = user.id

    token = create_access_token(
        AccessTokenPayload(
            sub=str(user_id),
            username="member",
            role="member",
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
        headers=headers,
    ) as client:
        yield KnowledgeApiHarness(
            client=client,
            session_factory=session_factory,
            user_id=user_id,
            headers=headers,
        )

    app.dependency_overrides.clear()
    get_settings.cache_clear()
    await _drop_schema(admin_engine, schema_name)
    await test_engine.dispose()
    await admin_engine.dispose()


@pytest.mark.asyncio
async def test_create_upload_and_list_knowledge_document(
    knowledge_api_harness: KnowledgeApiHarness,
) -> None:
    create_response = await knowledge_api_harness.client.post(
        "/api/v1/knowledge-bases",
        json={
            "name": "产品资料库",
            "description": "产品文档",
            "status": "enabled",
            "chunkSize": 10,
            "chunkOverlap": 2,
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()["data"]
    assert created["name"] == "产品资料库"
    assert created["documentCount"] == 0

    upload_response = await knowledge_api_harness.client.post(
        f"/api/v1/knowledge-bases/{created['id']}/documents",
        files={
            "file": (
                "guide.txt",
                b"abcdefghijklmnopqrstuvwxyz",
                "text/plain",
            )
        },
    )
    assert upload_response.status_code == 201
    uploaded = upload_response.json()["data"]
    assert uploaded["filename"] == "guide.txt"
    assert uploaded["status"] == "completed"
    assert uploaded["chunkCount"] == 3

    list_response = await knowledge_api_harness.client.get(
        f"/api/v1/knowledge-bases/{created['id']}/documents"
    )
    assert list_response.status_code == 200
    assert list_response.json()["data"]["total"] == 1
