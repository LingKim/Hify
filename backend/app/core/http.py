"""Unified outbound HTTP client with retry behavior."""

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import get_settings

RETRYABLE_STATUS_CODES = {429, 502, 503, 504}


@dataclass(frozen=True, slots=True)
class ExternalResponse:
    """Normalized external HTTP response payload."""

    ok: bool
    status_code: int
    data: Any | None
    error: str | None
    headers: dict[str, str]
    attempt_count: int


class ExternalHttpClient:
    """HTTP client wrapper with consistent timeout and retry behavior."""

    def __init__(
        self,
        *,
        client: httpx.AsyncClient | None = None,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
        retry_backoff_seconds: float | None = None,
        user_agent: str | None = None,
    ) -> None:
        settings = get_settings()
        self.client = client
        self.timeout_seconds = (
            timeout_seconds or settings.http_client_timeout_seconds
        )
        self.max_retries = max_retries or settings.http_client_max_retries
        self.retry_backoff_seconds = (
            retry_backoff_seconds
            if retry_backoff_seconds is not None
            else settings.http_client_retry_backoff_seconds
        )
        self.user_agent = user_agent or settings.http_client_user_agent

    async def request_json(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> ExternalResponse:
        """Send a JSON request and normalize the response."""
        request_headers = {"User-Agent": self.user_agent}
        if headers is not None:
            request_headers.update(headers)

        owns_client = self.client is None
        client = self.client or httpx.AsyncClient(timeout=self.timeout_seconds)
        try:
            last_error: str | None = None
            for attempt in range(1, self.max_retries + 1):
                try:
                    response = await client.request(
                        method,
                        url,
                        headers=request_headers,
                        params=params,
                        json=json_body,
                    )
                except (httpx.TimeoutException, httpx.TransportError) as exc:
                    last_error = str(exc)
                    if attempt < self.max_retries:
                        await asyncio.sleep(self.retry_backoff_seconds)
                        continue
                    return ExternalResponse(
                        ok=False,
                        status_code=0,
                        data=None,
                        error=last_error or "external request failed",
                        headers={},
                        attempt_count=attempt,
                    )

                if (
                    response.status_code in RETRYABLE_STATUS_CODES
                    and attempt < self.max_retries
                ):
                    await asyncio.sleep(self.retry_backoff_seconds)
                    continue

                try:
                    data = response.json()
                except ValueError:
                    data = None

                return ExternalResponse(
                    ok=response.is_success,
                    status_code=response.status_code,
                    data=data,
                    error=None if response.is_success else response.text,
                    headers=dict(response.headers),
                    attempt_count=attempt,
                )

            return ExternalResponse(
                ok=False,
                status_code=0,
                data=None,
                error=last_error or "external request failed",
                headers={},
                attempt_count=self.max_retries,
            )
        finally:
            if owns_client:
                await client.aclose()
