"""Provider registry and secret helpers for LLM integrations."""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from typing import Any

from cryptography.fernet import Fernet

from app.core.config import get_settings


def mask_secret(secret: str) -> str:
    """Mask a provider secret while keeping a small visible prefix/suffix."""
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}...{secret[-4:]}"


def fingerprint_secret(secret: str) -> str:
    """Return a stable fingerprint for secret change detection."""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def _derive_fernet_key(secret_key: str) -> bytes:
    digest = hashlib.sha256(secret_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


@dataclass(frozen=True, slots=True)
class ProviderSecretPayload:
    """Structured secret payload stored in encrypted form."""

    secret_value: str
    headers: dict[str, str] | None = None
    query_params: dict[str, str] | None = None
    metadata: dict[str, Any] | None = None

    def to_json(self) -> str:
        """Serialize the payload into a compact JSON string."""
        return json.dumps(
            {
                "secret_value": self.secret_value,
                "headers": self.headers or {},
                "query_params": self.query_params or {},
                "metadata": self.metadata or {},
            },
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )

    @classmethod
    def from_json(cls, payload: str) -> ProviderSecretPayload:
        """Deserialize a secret payload from encrypted JSON."""
        raw = json.loads(payload)
        return cls(
            secret_value=raw["secret_value"],
            headers=raw.get("headers") or None,
            query_params=raw.get("query_params") or None,
            metadata=raw.get("metadata") or None,
        )


class ProviderSecretCodec:
    """Encrypt and decrypt provider secret payloads."""

    def __init__(self, secret_key: str | None = None) -> None:
        settings = get_settings()
        material = secret_key or settings.provider_secret_key
        self._fernet = Fernet(_derive_fernet_key(material))

    def encrypt(self, payload: ProviderSecretPayload) -> str:
        """Encrypt a provider secret payload for database storage."""
        token = self._fernet.encrypt(payload.to_json().encode("utf-8"))
        return token.decode("utf-8")

    def decrypt(self, ciphertext: str) -> ProviderSecretPayload:
        """Decrypt a provider secret payload from database storage."""
        payload = self._fernet.decrypt(ciphertext.encode("utf-8")).decode(
            "utf-8"
        )
        return ProviderSecretPayload.from_json(payload)


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


@dataclass(frozen=True, slots=True)
class LiteLLMRuntimeConfig:
    """Resolved runtime config used to invoke LiteLLM."""

    provider_type: str
    api_family: str
    model_name: str
    litellm_model: str
    api_base: str
    api_key: str
    extra_headers: dict[str, str]
    query_params: dict[str, str]

    @property
    def masked_api_key(self) -> str:
        """Return a masked secret for UI-safe previews."""
        return mask_secret(self.api_key)


def resolve_litellm_model(provider_type: str, model_name: str) -> str:
    """Resolve a LiteLLM model string from provider type and raw model name."""
    if provider_type == "openai":
        return model_name
    if provider_type == "openai_compatible":
        return f"openai/{model_name}"
    if provider_type == "anthropic":
        return f"anthropic/{model_name}"
    if provider_type == "gemini":
        return f"gemini/{model_name}"
    if provider_type == "ollama":
        return f"ollama/{model_name}"
    return model_name


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
