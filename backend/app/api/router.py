"""Top-level API router aggregation."""

from fastapi import APIRouter

from app.agent.router import router as agent_router
from app.auth.router import router as auth_router
from app.conversation.router import router as conversation_router
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


api_router.include_router(auth_router)
api_router.include_router(llm_router)
api_router.include_router(tool_router)
api_router.include_router(agent_router)
api_router.include_router(knowledge_router)
api_router.include_router(conversation_router)
