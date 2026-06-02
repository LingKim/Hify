from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any

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
from app.core.database import Base
from app.core.exceptions import BizException
from app.llm.provider import (
    ProviderSecretCodec,
    ProviderSecretPayload,
    mask_secret,
)
from app.tool.model import Tool, ToolAuthSecret, ToolExecutionLog, ToolParameter
from app.tool.schema import ToolExecuteTestReq
from app.tool.service import ToolService

from tests._p4_echo import ToolEchoServer, start_echo_server


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
class RealHttpHarness:
    session_factory: async_sessionmaker[AsyncSession]
    user_id: int
    echo: ToolEchoServer
    codec: ProviderSecretCodec


@pytest_asyncio.fixture
async def real_http_harness() -> RealHttpHarness:
    database_url = _database_url()
    schema_name = f"test_tool_real_{uuid.uuid4().hex}"
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

    codec = ProviderSecretCodec()
    async with session_factory() as session:
        user = User(
            username="real",
            email="real@hify.ai",
            password_hash=hash_password("Real12345!"),
            role="member",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        user_id = user.id

    echo = start_echo_server(slow_delay=1.5)
    try:
        yield RealHttpHarness(
            session_factory=session_factory,
            user_id=user_id,
            echo=echo,
            codec=codec,
        )
    finally:
        echo.stop()
        await _drop_schema(admin_engine, schema_name)
        await test_engine.dispose()
        await admin_engine.dispose()


async def _insert_tool(
    session: AsyncSession,
    *,
    user_id: int,
    name: str,
    url: str,
    method: str = "GET",
    status: str = "enabled",
    query_template: dict[str, Any] | None = None,
    body_template: dict[str, Any] | None = None,
    headers_template: dict[str, Any] | None = None,
    timeout_seconds: int = 5,
    parameters: list[dict[str, Any]] | None = None,
    auth: dict[str, Any] | None = None,
) -> int:
    """Insert a Tool row plus auth/parameters, bypassing URL safety checks."""

    tool = Tool(
        owner_user_id=user_id,
        name=name,
        status=status,
        tool_type="http",
        source_type="manual",
        http_method=method,
        url=url,
        timeout_seconds=timeout_seconds,
        headers_template_json=headers_template,
        query_template_json=query_template,
        body_template_json=body_template,
        content_type="application/json",
    )
    session.add(tool)
    await session.flush()

    codec = ProviderSecretCodec()
    auth_payload = auth or {"type": "none"}
    if auth_payload["type"] == "none":
        session.add(
            ToolAuthSecret(
                tool_id=tool.id,
                auth_type="none",
            )
        )
    else:
        secret_value = auth_payload["secret_value"]
        session.add(
            ToolAuthSecret(
                tool_id=tool.id,
                auth_type=auth_payload["type"],
                secret_ciphertext=codec.encrypt(
                    ProviderSecretPayload(secret_value=secret_value)
                ),
                secret_masked=mask_secret(secret_value),
                secret_fingerprint="real-test",
                encryption_key_version="v1",
                metadata_json={
                    "headerName": auth_payload.get("header_name"),
                    "queryName": auth_payload.get("query_name"),
                },
            )
        )

    for index, param in enumerate(parameters or []):
        session.add(
            ToolParameter(
                tool_id=tool.id,
                name=param["name"],
                label=param.get("label"),
                description=param.get("description"),
                param_location=param["location"],
                schema_type=param["type"],
                is_required=param.get("required", False),
                schema_json={"type": param["type"]},
                sort_order=index,
            )
        )

    await session.commit()
    return int(tool.id)


@pytest.mark.asyncio
async def test_execute_test_renders_url_query_and_injects_auth_header(
    real_http_harness: RealHttpHarness,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ToolService,
        "_validate_safe_url",
        lambda self, url: None,
    )
    base = real_http_harness.echo.base_url
    async with real_http_harness.session_factory() as session:
        tool_id = await _insert_tool(
            session,
            user_id=real_http_harness.user_id,
            name="查询天气",
            url=f"{base}/ok",
            method="GET",
            query_template={"city": "{{city}}"},
            headers_template={"Accept": "application/json"},
            parameters=[
                {
                    "name": "city",
                    "location": "query",
                    "type": "string",
                    "required": True,
                }
            ],
            auth={
                "type": "api_key_header",
                "secret_value": "sk-real-secret-987",
                "header_name": "X-API-Key",
            },
        )

    async with real_http_harness.session_factory() as session:
        service = ToolService(
            db=session,
            secret_codec=real_http_harness.codec,
        )
        result = await service.execute_test(
            tool_id,
            ToolExecuteTestReq(parameters={"city": "杭州"}),
            user_id=real_http_harness.user_id,
        )

    assert result.status == "success"
    assert result.response.status_code == 200
    assert result.latency_ms >= 0
    assert real_http_harness.echo.requests
    inbound = real_http_harness.echo.requests[-1]
    assert inbound.method == "GET"
    assert inbound.path == "/ok"
    assert inbound.query == {"city": "杭州"}
    inbound_header_map = {k.lower(): v for k, v in inbound.headers.items()}
    assert inbound_header_map.get("x-api-key") == "sk-real-secret-987"
    assert inbound_header_map.get("accept") == "application/json"
    request_header_map = {
        k.lower(): v for k, v in result.request.headers.items()
    }
    assert request_header_map.get("x-api-key") != "sk-real-secret-987"

    async with real_http_harness.session_factory() as session:
        log = await session.scalar(
            select(ToolExecutionLog).where(ToolExecutionLog.tool_id == tool_id)
        )
    assert log is not None
    assert log.source == "test"
    assert log.status == "success"
    log_header_map = {
        k.lower(): v for k, v in (log.request_headers_json or {}).items()
    }
    assert log_header_map.get("x-api-key") != "sk-real-secret-987"
    assert "sk-real-secret-987" not in " ".join(
        log_header_map.values()
    )
    assert log.response_status_code == 200


@pytest.mark.asyncio
async def test_execute_test_propagates_5xx_as_failed(
    real_http_harness: RealHttpHarness,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ToolService,
        "_validate_safe_url",
        lambda self, url: None,
    )
    base = real_http_harness.echo.base_url
    async with real_http_harness.session_factory() as session:
        tool_id = await _insert_tool(
            session,
            user_id=real_http_harness.user_id,
            name="故意失败",
            url=f"{base}/fail",
        )

    async with real_http_harness.session_factory() as session:
        service = ToolService(
            db=session,
            secret_codec=real_http_harness.codec,
        )
        result = await service.execute_test(
            tool_id,
            ToolExecuteTestReq(parameters={}),
            user_id=real_http_harness.user_id,
        )

    assert result.status == "failed"
    assert result.response.status_code == 500
    assert result.error_code == "http_error"
    assert "500" in (result.error_message or "")

    async with real_http_harness.session_factory() as session:
        log = await session.scalar(
            select(ToolExecutionLog).where(ToolExecutionLog.tool_id == tool_id)
        )
    assert log is not None
    assert log.status == "failed"
    assert log.response_status_code == 500
    assert log.error_code == "http_error"
    assert log.error_message and "500" in log.error_message


@pytest.mark.asyncio
async def test_execute_test_timeout_returns_timeout_status(
    real_http_harness: RealHttpHarness,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ToolService,
        "_validate_safe_url",
        lambda self, url: None,
    )
    base = real_http_harness.echo.base_url
    async with real_http_harness.session_factory() as session:
        tool_id = await _insert_tool(
            session,
            user_id=real_http_harness.user_id,
            name="慢响应",
            url=f"{base}/slow",
            timeout_seconds=2,
        )

    async with real_http_harness.session_factory() as session:
        service = ToolService(
            db=session,
            secret_codec=real_http_harness.codec,
        )
        result = await service.execute_test(
            tool_id,
            ToolExecuteTestReq(parameters={}, timeout_seconds=1),
            user_id=real_http_harness.user_id,
        )

    assert result.status == "timeout"
    assert result.error_code == "timeout"

    async with real_http_harness.session_factory() as session:
        log = await session.scalar(
            select(ToolExecutionLog).where(ToolExecutionLog.tool_id == tool_id)
        )
    assert log is not None
    assert log.status == "timeout"


@pytest.mark.asyncio
async def test_execute_test_missing_required_parameter_raises_400(
    real_http_harness: RealHttpHarness,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ToolService,
        "_validate_safe_url",
        lambda self, url: None,
    )
    base = real_http_harness.echo.base_url
    async with real_http_harness.session_factory() as session:
        tool_id = await _insert_tool(
            session,
            user_id=real_http_harness.user_id,
            name="必填城市",
            url=f"{base}/ok",
            parameters=[
                {
                    "name": "city",
                    "location": "query",
                    "type": "string",
                    "required": True,
                }
            ],
        )

    async with real_http_harness.session_factory() as session:
        service = ToolService(
            db=session,
            secret_codec=real_http_harness.codec,
        )
        with pytest.raises(BizException) as excinfo:
            await service.execute_test(
                tool_id,
                ToolExecuteTestReq(parameters={}),
                user_id=real_http_harness.user_id,
            )
    assert "city" in str(excinfo.value.message)
    assert not real_http_harness.echo.requests


@pytest.mark.asyncio
async def test_validate_safe_url_blocks_loopback_and_private() -> None:
    """Without monkeypatch the safety net must reject loopback / private IPs."""

    service = ToolService(  # type: ignore[arg-type]
        db=None,  # type: ignore[arg-type]
        secret_codec=ProviderSecretCodec(),
    )
    for blocked in (
        "http://localhost/api",
        "http://127.0.0.1/api",
        "http://10.0.0.1/api",
        "http://192.168.1.1/api",
        "http://169.254.169.254/latest/meta-data",
    ):
        with pytest.raises(BizException):
            service._validate_safe_url(blocked)
