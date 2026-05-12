from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.model import Agent
from app.agent.service import AgentService
from app.auth.deps import get_current_active_user
from app.auth.model import User
from app.auth.service import AuthService
from app.conversation.model import Conversation
from app.conversation.service import ConversationService
from app.knowledge.model import KnowledgeBase
from app.knowledge.service import KnowledgeService
from app.llm.model import (
    ProviderAuthSecret,
    ProviderHealthStatus,
    ProviderInstance,
    ProviderModel,
)
from app.llm.service import LlmService
from app.main import app
from app.tool.model import Tool
from app.tool.service import ToolService


@pytest.mark.parametrize(
    ("path", "module_name"),
    [
        ("/api/v1/auth/login-preview", "auth"),
        ("/api/v1/llms/model-preview", "llm"),
        ("/api/v1/tools/execution-preview", "tool"),
        ("/api/v1/agents/config-preview", "agent"),
        ("/api/v1/knowledge-bases/retrieval-preview", "knowledge"),
        ("/api/v1/conversations/chat-preview", "conversation"),
    ],
)
def test_module_preview_endpoints_return_result_payload(
    path: str,
    module_name: str,
) -> None:
    async def override_current_user() -> User:
        return User(
            id=1,
            username="member",
            email="member@hify.ai",
            password_hash="hashed",
            role="member",
            is_active=True,
        )

    app.dependency_overrides[get_current_active_user] = override_current_user
    client = TestClient(app)

    try:
        response = client.get(path)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 200
    assert payload["message"] == "success"
    assert payload["data"]["module"] == module_name
    assert payload["data"]["status"] == "skeleton_ready"
    assert isinstance(payload["data"]["capabilities"], list)


@pytest.mark.parametrize(
    ("service_cls", "expected_module"),
    [
        (AuthService, "auth"),
        (LlmService, "llm"),
        (ToolService, "tool"),
        (AgentService, "agent"),
        (KnowledgeService, "knowledge"),
        (ConversationService, "conversation"),
    ],
)
@pytest.mark.asyncio
async def test_service_preview_methods_return_module_payload(
    service_cls: type[
        AuthService
        | LlmService
        | ToolService
        | AgentService
        | KnowledgeService
        | ConversationService
    ],
    expected_module: str,
) -> None:
    session = Mock(spec=AsyncSession)
    service = service_cls(session)

    payload = await service.preview()

    assert payload.module == expected_module
    assert payload.status == "skeleton_ready"
    assert isinstance(payload.capabilities, list)


def test_placeholder_models_are_importable() -> None:
    models = [
        User,
        ProviderInstance,
        ProviderAuthSecret,
        ProviderModel,
        ProviderHealthStatus,
        Tool,
        Agent,
        KnowledgeBase,
        Conversation,
    ]

    assert all(model.__name__ for model in models)
