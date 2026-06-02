"""LiteLLM execution helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from time import perf_counter
from typing import Any

import litellm

from app.core.exceptions import BizException
from app.llm.errors import LlmErrorCode
from app.llm.provider import LiteLLMRuntimeConfig


@dataclass(frozen=True, slots=True)
class InvokeResult:
    """Normalized result returned from a LiteLLM text invocation."""

    model_name: str
    litellm_model: str
    output_text: str
    latency_ms: int


@dataclass(frozen=True, slots=True)
class StreamChunk:
    """Normalized token delta returned from a LiteLLM stream."""

    delta: str


@dataclass(frozen=True, slots=True)
class ToolCall:
    """Normalized tool call returned by an upstream model."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ToolDecision:
    """Normalized non-streaming response used before tool execution."""

    assistant_message: dict[str, Any]
    tool_calls: list[ToolCall]


class LiteLLMExecutor:
    """Thin adapter around LiteLLM async chat completion."""

    async def invoke_text(
        self,
        runtime_config: LiteLLMRuntimeConfig,
        *,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> InvokeResult:
        """Execute one real text invocation using LiteLLM."""
        start_clock = perf_counter()
        try:
            response = await litellm.acompletion(
                model=runtime_config.litellm_model,
                messages=[{"role": "user", "content": prompt}],
                api_base=runtime_config.api_base,
                api_key=runtime_config.api_key or None,
                extra_headers=runtime_config.extra_headers or None,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except litellm.AuthenticationError as exc:
            raise BizException(
                code=LlmErrorCode.PROVIDER_AUTH_FAILED,
                message="模型调用鉴权失败",
                http_status=401,
            ) from exc
        except litellm.RateLimitError as exc:
            raise BizException(
                code=LlmErrorCode.PROVIDER_RATE_LIMITED,
                message="模型调用触发限流",
                http_status=429,
            ) from exc
        except (litellm.Timeout, litellm.APIConnectionError) as exc:
            raise BizException(
                code=LlmErrorCode.REQUEST_TIMEOUT,
                message="模型调用超时或连接失败",
                http_status=504,
            ) from exc
        except (litellm.BadRequestError, litellm.APIError) as exc:
            raise BizException(
                code=LlmErrorCode.INVALID_MODEL_PARAMETERS,
                message="模型调用参数无效或服务异常",
                http_status=400,
            ) from exc

        latency_ms = int((perf_counter() - start_clock) * 1000)
        return InvokeResult(
            model_name=runtime_config.model_name,
            litellm_model=runtime_config.litellm_model,
            output_text=_extract_output_text(response),
            latency_ms=latency_ms,
        )

    async def stream_text(
        self,
        runtime_config: LiteLLMRuntimeConfig,
        *,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """Execute one streaming text invocation using LiteLLM."""
        try:
            stream = await litellm.acompletion(
                model=runtime_config.litellm_model,
                messages=messages,
                api_base=runtime_config.api_base,
                api_key=runtime_config.api_key or None,
                extra_headers=runtime_config.extra_headers or None,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            async for chunk in stream:
                delta = _extract_stream_delta(chunk)
                if delta:
                    yield StreamChunk(delta=delta)
        except litellm.AuthenticationError as exc:
            raise BizException(
                code=LlmErrorCode.PROVIDER_AUTH_FAILED,
                message="模型调用鉴权失败",
                http_status=401,
            ) from exc
        except litellm.RateLimitError as exc:
            raise BizException(
                code=LlmErrorCode.PROVIDER_RATE_LIMITED,
                message="模型调用触发限流",
                http_status=429,
            ) from exc
        except (litellm.Timeout, litellm.APIConnectionError) as exc:
            raise BizException(
                code=LlmErrorCode.REQUEST_TIMEOUT,
                message="模型调用超时或连接失败",
                http_status=504,
            ) from exc
        except (litellm.BadRequestError, litellm.APIError) as exc:
            raise BizException(
                code=LlmErrorCode.INVALID_MODEL_PARAMETERS,
                message="模型调用参数无效或服务异常",
                http_status=400,
            ) from exc

    async def invoke_with_tools(
        self,
        runtime_config: LiteLLMRuntimeConfig,
        *,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ToolDecision:
        """Ask the model whether to call tools using OpenAI tool format."""
        try:
            response = await litellm.acompletion(
                model=runtime_config.litellm_model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                api_base=runtime_config.api_base,
                api_key=runtime_config.api_key or None,
                extra_headers=runtime_config.extra_headers or None,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except litellm.AuthenticationError as exc:
            raise BizException(
                code=LlmErrorCode.PROVIDER_AUTH_FAILED,
                message="模型调用鉴权失败",
                http_status=401,
            ) from exc
        except litellm.RateLimitError as exc:
            raise BizException(
                code=LlmErrorCode.PROVIDER_RATE_LIMITED,
                message="模型调用触发限流",
                http_status=429,
            ) from exc
        except (litellm.Timeout, litellm.APIConnectionError) as exc:
            raise BizException(
                code=LlmErrorCode.REQUEST_TIMEOUT,
                message="模型调用超时或连接失败",
                http_status=504,
            ) from exc
        except (litellm.BadRequestError, litellm.APIError) as exc:
            raise BizException(
                code=LlmErrorCode.INVALID_MODEL_PARAMETERS,
                message="模型调用参数无效或服务异常",
                http_status=400,
            ) from exc

        message = _extract_response_message(response)
        return ToolDecision(
            assistant_message=message,
            tool_calls=_extract_tool_calls(message),
        )


def _extract_output_text(response: Any) -> str:
    """Best-effort extraction of text content from LiteLLM responses."""
    choices = getattr(response, "choices", None)
    if choices:
        first_choice = choices[0]
        message = getattr(first_choice, "message", None)
        if message is not None:
            content = getattr(message, "content", None)
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                text_parts = [
                    str(item.get("text", ""))
                    for item in content
                    if isinstance(item, dict)
                ]
                merged = "".join(text_parts).strip()
                if merged:
                    return merged

    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    return ""


def _extract_stream_delta(chunk: Any) -> str:
    """Best-effort extraction of text delta from LiteLLM stream chunks."""
    choices = getattr(chunk, "choices", None)
    if not choices:
        return ""

    first_choice = choices[0]
    delta = getattr(first_choice, "delta", None)
    if delta is None:
        return ""

    content = getattr(delta, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            str(item.get("text", ""))
            for item in content
            if isinstance(item, dict)
        )
    return ""


def _extract_response_message(response: Any) -> dict[str, Any]:
    """Return the first response message as a plain dict."""
    choices = getattr(response, "choices", None)
    if not choices:
        return {"role": "assistant", "content": ""}

    message = getattr(choices[0], "message", None)
    if message is None:
        return {"role": "assistant", "content": ""}
    if isinstance(message, dict):
        return dict(message)
    if hasattr(message, "model_dump"):
        return dict(message.model_dump())

    result: dict[str, Any] = {
        "role": getattr(message, "role", "assistant"),
        "content": getattr(message, "content", None),
    }
    tool_calls = getattr(message, "tool_calls", None)
    if tool_calls is not None:
        result["tool_calls"] = tool_calls
    return result


def _extract_tool_calls(message: dict[str, Any]) -> list[ToolCall]:
    """Normalize OpenAI-format tool calls from a message dict."""
    raw_tool_calls = message.get("tool_calls") or []
    result: list[ToolCall] = []
    for index, raw_call in enumerate(raw_tool_calls):
        call_id = _read_attr(raw_call, "id") or f"tool_call_{index + 1}"
        function = _read_attr(raw_call, "function") or {}
        name = _read_attr(function, "name")
        raw_arguments = _read_attr(function, "arguments") or "{}"
        if not isinstance(name, str) or not name:
            continue
        arguments = _parse_tool_arguments(raw_arguments)
        result.append(ToolCall(id=str(call_id), name=name, arguments=arguments))
    return result


def _read_attr(value: Any, name: str) -> Any:
    """Read an attribute from dict-like or object-like values."""
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


def _parse_tool_arguments(value: Any) -> dict[str, Any]:
    """Parse a model-provided JSON object argument payload."""
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return {}
    import json

    try:
        parsed = json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}
