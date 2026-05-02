"""Top-level API router aggregation."""

from fastapi import APIRouter, Response, status

from app.agent.router import router as agent_router
from app.auth.router import router as auth_router
from app.conversation.router import router as conversation_router
from app.core.metrics import metrics_registry
from app.core.observability import get_readiness_snapshot
from app.core.responses import Result
from app.knowledge.router import router as knowledge_router
from app.llm.router import router as llm_router
from app.tool.router import router as tool_router

api_router = APIRouter()


@api_router.get("/health", response_model=Result[dict[str, str]])
async def health() -> Result[dict[str, str]]:
    """Return a minimal health status payload."""
    return Result.success(data={"status": "ok"})


@api_router.get("/api/v1/health", response_model=Result[dict[str, str]])
async def versioned_health() -> Result[dict[str, str]]:
    """Return the versioned health status used by frontend proxies."""
    return Result.success(data={"status": "ok"})


@api_router.get("/metrics", response_model=Result[dict[str, object]])
async def metrics() -> Result[dict[str, object]]:
    """Return an application metrics snapshot."""
    return Result.success(data=metrics_registry.snapshot())


@api_router.get("/ready", response_model=Result[dict[str, object]])
async def readiness(response: Response) -> Result[dict[str, object]]:
    """Return the unversioned readiness status for infrastructure checks."""
    payload = await get_readiness_snapshot()
    if payload["status"] != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return Result.success(data=payload)


@api_router.get("/api/v1/ready", response_model=Result[dict[str, object]])
async def versioned_readiness(
    response: Response,
) -> Result[dict[str, object]]:
    """Return the versioned readiness status for frontend proxies."""
    payload = await get_readiness_snapshot()
    if payload["status"] != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return Result.success(data=payload)


api_router.include_router(auth_router)
api_router.include_router(llm_router)
api_router.include_router(tool_router)
api_router.include_router(agent_router)
api_router.include_router(knowledge_router)
api_router.include_router(conversation_router)
