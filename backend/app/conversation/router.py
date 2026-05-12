"""Conversation module routes."""

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_active_user
from app.auth.model import User
from app.conversation.schema import (
    ConversationAgentRuntimePreviewResp,
    ConversationChatPreviewResp,
    ConversationCreateReq,
    ConversationDetailResp,
    ConversationListParams,
    ConversationMessageListParams,
    ConversationMessageResp,
    ConversationStreamMessageReq,
    ConversationSummaryResp,
    ConversationUpdateReq,
)
from app.conversation.service import ConversationService
from app.conversation.sse import stream_events
from app.core.database import get_db_session
from app.core.responses import PageResult, Result

router = APIRouter(prefix="/api/v1/conversations", tags=["conversation"])


@router.get(
    "/chat-preview",
    response_model=Result[ConversationChatPreviewResp],
)
async def chat_preview(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[ConversationChatPreviewResp]:
    """Return the conversation module preview endpoint response."""
    del current_user
    service = ConversationService(db)
    return Result.success(data=await service.preview())


@router.get("", response_model=Result[PageResult[ConversationSummaryResp]])
async def list_conversations(
    params: ConversationListParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[PageResult[ConversationSummaryResp]]:
    """Return current user's conversations."""
    service = ConversationService(db)
    return Result.success(
        data=await service.list_conversations(
            params,
            user_id=current_user.id,
        )
    )


@router.post(
    "",
    response_model=Result[ConversationDetailResp],
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    payload: ConversationCreateReq,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[ConversationDetailResp]:
    """Create one conversation."""
    service = ConversationService(db)
    data = await service.create_conversation(
        payload,
        user_id=current_user.id,
    )
    return Result.success(data=data, code=status.HTTP_201_CREATED)


@router.get(
    "/agents/{agent_id}/runtime-preview",
    response_model=Result[ConversationAgentRuntimePreviewResp],
)
async def get_agent_runtime_preview(
    agent_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[ConversationAgentRuntimePreviewResp]:
    """Return one agent runtime preview for conversation."""
    del current_user
    service = ConversationService(db)
    return Result.success(
        data=await service.get_agent_runtime_preview(agent_id)
    )


@router.get(
    "/{conversation_id}",
    response_model=Result[ConversationDetailResp],
)
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[ConversationDetailResp]:
    """Return one conversation detail."""
    service = ConversationService(db)
    return Result.success(
        data=await service.get_conversation(
            conversation_id,
            user_id=current_user.id,
        )
    )


@router.patch(
    "/{conversation_id}",
    response_model=Result[ConversationDetailResp],
)
async def update_conversation(
    conversation_id: int,
    payload: ConversationUpdateReq,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[ConversationDetailResp]:
    """Update one conversation."""
    service = ConversationService(db)
    return Result.success(
        data=await service.update_conversation(
            conversation_id,
            payload,
            user_id=current_user.id,
        )
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """Soft-delete one conversation."""
    service = ConversationService(db)
    await service.delete_conversation(
        conversation_id,
        user_id=current_user.id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{conversation_id}/messages",
    response_model=Result[PageResult[ConversationMessageResp]],
)
async def list_messages(
    conversation_id: int,
    params: ConversationMessageListParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[PageResult[ConversationMessageResp]]:
    """Return conversation message history."""
    service = ConversationService(db)
    return Result.success(
        data=await service.list_messages(
            conversation_id,
            params,
            user_id=current_user.id,
        )
    )


@router.post("/{conversation_id}/messages/stream")
async def stream_message(
    conversation_id: int,
    payload: ConversationStreamMessageReq,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> StreamingResponse:
    """Send one user message and stream assistant output through SSE."""
    service = ConversationService(db)
    prepared = await service.prepare_stream_message(
        conversation_id,
        payload,
        user_id=current_user.id,
    )
    return StreamingResponse(
        stream_events(service, prepared),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
