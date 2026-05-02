"""Provider registry and config helpers for LLM integrations."""

from dataclasses import dataclass
from typing import Any


def mask_secret(secret: str) -> str:
    """Mask a provider secret while keeping a small visible prefix/suffix."""
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}...{secret[-4:]}"


@dataclass(frozen=True, slots=True)
class ProviderConfig:
    """Provider connection settings shared by LLM adapters."""

    provider: str
    model: str
    api_key: str
    base_url: str | None = None

    @property
    def masked_api_key(self) -> str:
        """Return a masked provider secret for logs and admin views."""
        return mask_secret(self.api_key)


class ProviderRegistry:
    """Register and resolve provider adapters by provider name."""

    def __init__(self) -> None:
        self._adapters: dict[str, Any] = {}

    def register(self, provider: str, adapter: Any) -> None:
        """Register an adapter instance under the provider name."""
        self._adapters[provider] = adapter

    def resolve(self, provider: str) -> Any:
        """Return the adapter registered for the provider."""
        return self._adapters[provider]

    def list_providers(self) -> list[str]:
        """Return all registered provider names."""
        return sorted(self._adapters.keys())
