"""Request-scoped context helpers."""

from contextvars import ContextVar, Token
from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class RequestContext:
    """Request-scoped metadata used by logging and tracing."""

    request_id: str
    trace_id: str
    method: str
    path: str
    user_id: str | None = None
    tenant_id: str | None = None
    client_ip: str | None = None


_request_context: ContextVar[RequestContext | None] = ContextVar(
    "request_context",
    default=None,
)


def set_request_context(
    context: RequestContext,
) -> Token[RequestContext | None]:
    """Store request context for the active coroutine."""
    return _request_context.set(context)


def reset_request_context(token: Token[RequestContext | None]) -> None:
    """Reset request context to the previous token."""
    _request_context.reset(token)


def get_request_context() -> RequestContext | None:
    """Return the current request context if present."""
    return _request_context.get()


def bind_request_user(user_id: str | None) -> RequestContext | None:
    """Attach the authenticated user to the current request context."""
    context = get_request_context()
    if context is None:
        return None
    updated = replace(context, user_id=user_id)
    _request_context.set(updated)
    return updated
