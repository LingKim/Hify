import pytest
from pydantic import ValidationError

from app.llm.provider import (
    ProviderSecretCodec,
    ProviderSecretPayload,
    fingerprint_secret,
    mask_secret,
)
from app.llm.schema import ProviderAdminCreateReq


def test_provider_secret_codec_encrypts_and_decrypts_payload() -> None:
    codec = ProviderSecretCodec(secret_key="unit-test-secret-key")
    payload = ProviderSecretPayload(
        secret_value="sk-test-123456",
        headers={"x-api-key": "sk-test-123456"},
        query_params={"version": "2026-05-03"},
        metadata={"provider": "openai"},
    )

    ciphertext = codec.encrypt(payload)
    restored = codec.decrypt(ciphertext)

    assert ciphertext != payload.secret_value
    assert restored == payload


def test_secret_helpers_mask_and_fingerprint_values() -> None:
    secret = "sk-1234567890"

    assert mask_secret(secret) == "sk-1...7890"
    assert fingerprint_secret(secret) == fingerprint_secret(secret)


def test_provider_create_schema_requires_at_least_one_model() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ProviderAdminCreateReq(
            name="OpenAI-prod",
            providerType="openai",
            apiFamily="openai_responses",
            baseUrl="https://api.openai.com/v1",
            auth={
                "authType": "api_key",
                "secretValue": "sk-test-123456",
            },
            models=[],
        )

    assert "至少需要配置一个模型" in str(exc_info.value)
