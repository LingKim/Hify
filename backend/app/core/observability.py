"""Request middleware and readiness helpers."""

import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request

from app.core.cache import get_cache
from app.core.context import (
    RequestContext,
    reset_request_context,
    set_request_context,
)
from app.core.database import ping_database
from app.core.metrics import metrics_registry
from app.core.tracing import generate_trace_id

logger = logging.getLogger(__name__)


def install_observability(app: FastAPI) -> None:
    """Install request context and structured request logging middleware."""

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        trace_id = request.headers.get("X-Trace-ID", generate_trace_id())
        client_ip = None
        if request.client is not None:
            client_ip = request.client.host
        context = RequestContext(
            request_id=request_id,
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
            tenant_id=request.headers.get("X-Tenant-ID"),
            client_ip=client_ip,
        )
        token = set_request_context(context)
        started_at = perf_counter()
        response = None
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Trace-ID"] = trace_id
            return response
        finally:
            latency_ms = round((perf_counter() - started_at) * 1000, 2)
            status_code = 500
            if response is not None:
                status_code = response.status_code
            metrics_registry.increment("http.server.requests")
            metrics_registry.observe("http.server.latency_ms", latency_ms)
            logger.info(
                "request completed status=%s latency_ms=%s",
                status_code,
                latency_ms,
            )
            reset_request_context(token)


async def get_readiness_snapshot() -> dict[str, object]:
    """Collect dependency readiness for database and cache."""
    checks: dict[str, dict[str, object]] = {}

    try:
        database_ok = await ping_database()
        checks["database"] = {"status": "ok" if database_ok else "error"}
    except Exception as exc:
        checks["database"] = {
            "status": "error",
            "detail": str(exc),
        }

    cache = get_cache()
    if cache.__class__.__name__ == "NullCache":
        checks["cache"] = {"status": "disabled"}
    else:
        try:
            cache_ok = await cache.ping()
            checks["cache"] = {"status": "ok" if cache_ok else "error"}
        except Exception as exc:
            checks["cache"] = {
                "status": "error",
                "detail": str(exc),
            }

    overall_status = "ok"
    for check in checks.values():
        if check["status"] == "error":
            overall_status = "degraded"
            break
    return {"status": overall_status, "checks": checks}
