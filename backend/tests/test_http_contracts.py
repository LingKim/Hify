from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.exceptions import BizException, register_exception_handlers
from app.main import app


class ValidationPayload(BaseModel):
    name: str


def test_health_returns_result_envelope() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "code": 200,
        "message": "success",
        "data": {"status": "ok"},
    }


def test_versioned_health_returns_result_envelope() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "code": 200,
        "message": "success",
        "data": {"status": "ok"},
    }


def test_biz_exception_returns_business_payload() -> None:
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/biz-error")
    async def biz_error() -> None:
        raise BizException(code=4001, message="Agent 不存在", http_status=404)

    client = TestClient(test_app)

    response = client.get("/biz-error")

    assert response.status_code == 404
    assert response.json() == {
        "code": 4001,
        "message": "Agent 不存在",
        "data": None,
    }


def test_validation_error_maps_to_common_code() -> None:
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.post("/validate")
    async def validate(payload: ValidationPayload) -> dict[str, str]:
        return {"name": payload.name}

    client = TestClient(test_app)

    response = client.post("/validate", json={})

    assert response.status_code == 422
    assert response.json()["code"] == 1001
    assert response.json()["message"] == "参数校验失败"


def test_unknown_exception_maps_to_unknown_error() -> None:
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/unknown-error")
    async def unknown_error() -> None:
        raise RuntimeError("boom")

    client = TestClient(test_app, raise_server_exceptions=False)

    response = client.get("/unknown-error")

    assert response.status_code == 500
    assert response.json() == {
        "code": 1000,
        "message": "未知错误",
        "data": None,
    }
