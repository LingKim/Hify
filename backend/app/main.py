"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.observability import install_observability

OPENAPI_TAGS = [
    {"name": "auth", "description": "认证与鉴权接口"},
    {"name": "llm", "description": "模型与提供商相关接口"},
    {"name": "tool", "description": "工具管理与执行接口"},
    {"name": "agent", "description": "Agent 配置与管理接口"},
    {"name": "knowledge", "description": "知识库与检索接口"},
    {"name": "conversation", "description": "对话与编排接口"},
    {"name": "user", "description": "用户管理接口"},
]


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    configure_logging(settings.log_level)
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        openapi_tags=OPENAPI_TAGS,
    )
    install_observability(app)
    register_exception_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
