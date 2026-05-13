from json import loads

import pytest
from httpx import AsyncClient, MockTransport, Request, Response

from app.core.config import get_settings
from app.knowledge.embedding import (
    SiliconFlowEmbeddingClient,
    create_embedding_client,
)
from app.knowledge.vector import build_vector_literal, cosine_search_sql


def test_settings_reads_embedding_provider_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EMBEDDDINGS_SECRET_KEY", "test-key")
    monkeypatch.setenv("EMBEDDINGS_MODEL", "BAAI/bge-m3")
    monkeypatch.setenv("EMBEDDINGS_DIMENSIONS", "768")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.embeddings_secret_key == "test-key"
    assert settings.embeddings_model == "BAAI/bge-m3"
    assert settings.embeddings_dimensions == 768

    get_settings.cache_clear()


def test_create_embedding_client_uses_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EMBEDDDINGS_SECRET_KEY", "test-key")
    monkeypatch.setenv("EMBEDDINGS_MODEL", "Qwen/Qwen3-Embedding-0.6B")
    monkeypatch.setenv("EMBEDDINGS_DIMENSIONS", "512")
    get_settings.cache_clear()

    client = create_embedding_client()

    assert client.api_key == "test-key"
    assert client.model == "Qwen/Qwen3-Embedding-0.6B"
    assert client.dimensions == 512

    get_settings.cache_clear()


def test_build_vector_literal_serializes_pgvector_input() -> None:
    vector = build_vector_literal([0.125, -1.5, 2])

    assert vector == "[0.125,-1.5,2.0]"


def test_cosine_search_sql_orders_by_vector_distance() -> None:
    statement = cosine_search_sql("knowledge_chunks", "embedding")
    compiled = str(statement)

    assert "embedding <=> CAST(:query_embedding AS public.vector)" in compiled
    assert "FROM knowledge_chunks" in compiled
    assert (
        "ORDER BY embedding <=> CAST(:query_embedding AS public.vector)"
        in compiled
    )
    assert "LIMIT :limit" in compiled


@pytest.mark.asyncio
async def test_siliconflow_embedding_client_returns_embedding() -> None:
    async def handler(request: Request) -> Response:
        assert request.url == "https://api.siliconflow.cn/v1/embeddings"
        assert request.headers["Authorization"] == "Bearer test-key"
        assert request.headers["Content-Type"] == "application/json"
        assert loads(request.read()) == {
            "model": "Qwen/Qwen3-Embedding-8B",
            "input": "测试文档",
            "encoding_format": "float",
            "dimensions": 1024,
        }
        return Response(
            status_code=200,
            json={
                "object": "list",
                "model": "Qwen/Qwen3-Embedding-8B",
                "data": [
                    {
                        "object": "embedding",
                        "embedding": [0.1, 0.2, 0.3],
                        "index": 0,
                    }
                ],
                "usage": {"total_tokens": 3},
            },
        )

    async with AsyncClient(transport=MockTransport(handler)) as http_client:
        client = SiliconFlowEmbeddingClient(
            api_key="test-key",
            http_client=http_client,
        )

        embedding = await client.embed("测试文档")

    assert embedding == [0.1, 0.2, 0.3]
