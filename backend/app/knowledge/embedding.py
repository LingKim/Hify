"""Embedding provider integration for knowledge retrieval."""

from dataclasses import dataclass

import httpx

from app.core.config import get_settings


@dataclass(frozen=True, slots=True)
class EmbeddingUsage:
    """Token usage returned by an embedding provider."""

    prompt_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class EmbeddingResult:
    """Single embedding result with optional provider usage metadata."""

    embedding: list[float]
    model: str
    usage: EmbeddingUsage | None = None


class SiliconFlowEmbeddingClient:
    """Client for SiliconFlow's OpenAI-compatible embeddings endpoint."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.siliconflow.cn/v1",
        model: str = "Qwen/Qwen3-Embedding-8B",
        dimensions: int = 1024,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.dimensions = dimensions
        self.http_client = http_client

    async def embed(self, input_text: str) -> list[float]:
        """Return only the embedding vector for raw-vector callers."""
        result = await self.create_embedding(input_text)
        return result.embedding

    async def create_embedding(self, input_text: str) -> EmbeddingResult:
        """Create one embedding from text input."""
        payload = {
            "model": self.model,
            "input": input_text,
            "encoding_format": "float",
            "dimensions": self.dimensions,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        owns_client = self.http_client is None
        client = self.http_client or httpx.AsyncClient(timeout=30.0)
        try:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            usage = data.get("usage") or {}
            return EmbeddingResult(
                embedding=[
                    float(value)
                    for value in data["data"][0]["embedding"]
                ],
                model=str(data.get("model") or self.model),
                usage=EmbeddingUsage(
                    prompt_tokens=usage.get("prompt_tokens"),
                    total_tokens=usage.get("total_tokens"),
                ),
            )
        finally:
            if owns_client:
                await client.aclose()


def create_embedding_client() -> SiliconFlowEmbeddingClient:
    """Create the configured embedding client for knowledge services."""
    settings = get_settings()
    if not settings.embeddings_secret_key:
        raise RuntimeError(
            "Missing EMBEDDDINGS_SECRET_KEY in backend environment files"
        )

    return SiliconFlowEmbeddingClient(
        api_key=settings.embeddings_secret_key,
        base_url=settings.embeddings_base_url,
        model=settings.embeddings_model,
        dimensions=settings.embeddings_dimensions,
    )
