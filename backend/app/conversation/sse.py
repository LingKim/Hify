"""SSE serialization helpers for conversation streams."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from app.conversation.runtime import PreparedConversationRun
from app.conversation.service import ConversationService
from app.core.exceptions import BizException


async def stream_events(
    service: ConversationService,
    prepared: PreparedConversationRun,
) -> AsyncIterator[str]:
    """Serialize one prepared run into SSE events."""
    yield sse(
        "run.started",
        {
            "runId": prepared.run.id,
            "conversationId": prepared.conversation.id,
            "status": "running",
            "startedAt": prepared.run.started_at.isoformat()
            if prepared.run.started_at is not None
            else None,
        },
    )
    yield sse(
        "message.created",
        {
            "userMessage": compact_message(prepared.user_message),
            "assistantMessage": compact_message(prepared.assistant_message),
        },
    )
    delta_sequence = 1
    try:
        async for delta in service.runtime.stream_assistant_response(prepared):
            yield sse(
                "message.delta",
                {
                    "runId": prepared.run.id,
                    "messageId": prepared.assistant_message.id,
                    "delta": delta,
                    "sequence": delta_sequence,
                },
            )
            delta_sequence += 1
    except BizException as exc:
        yield sse(
            "error",
            {
                "runId": prepared.run.id,
                "messageId": prepared.assistant_message.id,
                "code": int(exc.code),
                "message": exc.message,
                "status": "failed",
                "retryable": exc.http_status in {408, 429, 500, 502, 503, 504},
            },
        )
        return

    yield sse(
        "message.completed",
        {
            "runId": prepared.run.id,
            "message": {
                **compact_message(prepared.assistant_message),
                "status": "completed",
            },
        },
    )
    yield sse("run.completed", {"runId": prepared.run.id, "status": "completed"})
    yield sse(
        "done",
        {"runId": prepared.run.id, "conversationId": prepared.conversation.id},
    )


def compact_message(message: Any) -> dict[str, Any]:
    """Return a compact message payload for SSE events."""
    return {
        "id": message.id,
        "role": message.role,
        "status": message.status,
        "content": message.content,
        "sequence": message.sequence,
        "createdAt": message.created_at.isoformat()
        if message.created_at is not None
        else None,
    }


def sse(event: str, data: dict[str, Any]) -> str:
    """Serialize one SSE event."""
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {payload}\n\n"
