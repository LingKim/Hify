"""Conversation module business services."""

from __future__ import annotations

from fastapi import status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.model import User
from app.conversation.errors import ConversationErrorCode
from app.conversation.model import (
    ConversationMessage,
    ConversationRun,
    ConversationSession,
)
from app.conversation.presenter import (
    build_agent_snapshot,
    build_detail_response,
    build_message_response,
    build_runtime_preview_response,
    build_summary_response,
    optional_float,
    optional_int,
    preview_text,
)
from app.conversation.runtime import ConversationRuntime, PreparedConversationRun
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
from app.core.database import utc_now
from app.core.exceptions import BizException
from app.core.responses import PageResult
from app.llm.executor import LiteLLMExecutor
from app.llm.provider import ProviderSecretCodec


class ConversationService:
    """Conversation service with CRUD and streaming orchestration."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        executor: LiteLLMExecutor | None = None,
    ) -> None:
        """Initialize the conversation service."""
        self.db = db
        self.secret_codec = ProviderSecretCodec()
        self.executor = executor or LiteLLMExecutor()
        self.runtime = ConversationRuntime(
            db,
            secret_codec=self.secret_codec,
            executor=self.executor,
        )

    async def preview(self) -> ConversationChatPreviewResp:
        """Return the conversation module preview payload."""
        return ConversationChatPreviewResp(
            module="conversation",
            status="skeleton_ready",
            capabilities=[
                "多轮对话管理",
                "SSE 流式输出",
                "Agent 执行编排入口",
            ],
        )

    async def list_conversations(
        self,
        params: ConversationListParams,
    ) -> PageResult[ConversationSummaryResp]:
        """Return paginated conversation summaries for the current user."""
        user = await self._get_root_user()
        filters = [
            ConversationSession.user_id == user.id,
            ConversationSession.deleted_at.is_(None),
        ]
        if params.keyword:
            keyword = f"%{params.keyword.strip()}%"
            filters.append(
                or_(
                    ConversationSession.title.ilike(keyword),
                    ConversationSession.last_message_preview.ilike(keyword),
                )
            )
        if params.agent_id is not None:
            filters.append(ConversationSession.agent_id == params.agent_id)
        if params.status is not None:
            filters.append(ConversationSession.status == params.status)
        elif not params.include_archived:
            filters.append(ConversationSession.status != "archived")

        total_statement = (
            select(func.count())
            .select_from(ConversationSession)
            .where(*filters)
        )
        total = int((await self.db.execute(total_statement)).scalar_one())

        statement = (
            select(ConversationSession)
            .where(*filters)
            .order_by(
                ConversationSession.last_message_at.desc().nulls_last(),
                ConversationSession.updated_at.desc(),
            )
            .offset(params.offset)
            .limit(params.page_size)
        )
        rows = list((await self.db.scalars(statement)).all())
        return PageResult.create(
            items=[build_summary_response(row) for row in rows],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    async def create_conversation(
        self,
        payload: ConversationCreateReq,
    ) -> ConversationDetailResp:
        """Create a conversation for the root user."""
        user = await self._get_root_user()
        agent, model, provider, _secret = await self.runtime.load_runnable_agent(
            payload.agent_id
        )
        snapshot = build_agent_snapshot(agent, model, provider)
        conversation = ConversationSession(
            user_id=user.id,
            agent_id=agent.id,
            title=payload.title or "新会话",
            status="active",
            channel=payload.channel,
            agent_snapshot_json=snapshot,
            metadata_json=payload.metadata,
        )
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        return build_detail_response(conversation)

    async def get_conversation(self, conversation_id: int) -> ConversationDetailResp:
        """Return one conversation detail for the root user."""
        conversation = await self._get_conversation_or_raise(conversation_id)
        return build_detail_response(conversation)

    async def update_conversation(
        self,
        conversation_id: int,
        payload: ConversationUpdateReq,
    ) -> ConversationDetailResp:
        """Update one conversation title or archive status."""
        conversation = await self._get_conversation_or_raise(conversation_id)
        if payload.title is not None:
            conversation.title = payload.title.strip()
        if payload.status is not None:
            conversation.status = payload.status
        conversation.version += 1
        await self.db.commit()
        await self.db.refresh(conversation)
        return build_detail_response(conversation)

    async def delete_conversation(self, conversation_id: int) -> None:
        """Soft-delete one conversation and its messages/runs."""
        conversation = await self._get_conversation_or_raise(conversation_id)
        now = utc_now()
        conversation.deleted_at = now
        conversation.status = "deleted"
        conversation.version += 1

        message_statement = select(ConversationMessage).where(
            ConversationMessage.conversation_id == conversation.id,
            ConversationMessage.deleted_at.is_(None),
        )
        for message in list((await self.db.scalars(message_statement)).all()):
            message.deleted_at = now
            message.version += 1

        run_statement = select(ConversationRun).where(
            ConversationRun.conversation_id == conversation.id,
            ConversationRun.deleted_at.is_(None),
        )
        for run in list((await self.db.scalars(run_statement)).all()):
            run.deleted_at = now
            run.version += 1

        await self.db.commit()

    async def list_messages(
        self,
        conversation_id: int,
        params: ConversationMessageListParams,
    ) -> PageResult[ConversationMessageResp]:
        """Return paginated messages in one conversation."""
        conversation = await self._get_conversation_or_raise(conversation_id)
        filters = [
            ConversationMessage.conversation_id == conversation.id,
            ConversationMessage.deleted_at.is_(None),
        ]
        if params.role is not None:
            filters.append(ConversationMessage.role == params.role)

        total_statement = (
            select(func.count())
            .select_from(ConversationMessage)
            .where(*filters)
        )
        total = int((await self.db.execute(total_statement)).scalar_one())
        statement = (
            select(ConversationMessage)
            .where(*filters)
            .order_by(ConversationMessage.sequence.asc())
            .offset(params.offset)
            .limit(params.page_size)
        )
        messages = list((await self.db.scalars(statement)).all())
        return PageResult.create(
            items=[build_message_response(message) for message in messages],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    async def get_agent_runtime_preview(
        self,
        agent_id: int,
    ) -> ConversationAgentRuntimePreviewResp:
        """Return conversation-specific runtime preview for one agent."""
        try:
            agent, model, provider, _secret = (
                await self.runtime.load_runnable_agent(agent_id)
            )
            blocked_reason = None
        except BizException as exc:
            agent = await self.runtime.get_agent_or_raise(agent_id)
            model = None
            provider = None
            blocked_reason = exc.message

        return build_runtime_preview_response(
            agent=agent,
            model=model,
            provider=provider,
            blocked_reason=blocked_reason,
        )

    async def prepare_stream_message(
        self,
        conversation_id: int,
        payload: ConversationStreamMessageReq,
    ) -> PreparedConversationRun:
        """Persist stream placeholders before making the upstream LLM call."""
        conversation = await self._get_conversation_or_raise(conversation_id)
        if conversation.status != "active":
            raise BizException(
                code=ConversationErrorCode.CONVERSATION_CLOSED,
                message="会话已归档，不能继续发送消息",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        agent, model, provider, secret = (
            await self.runtime.load_runnable_agent(conversation.agent_id)
        )
        runtime_config = self.runtime.build_runtime_config(
            provider,
            model,
            secret,
        )
        next_sequence = await self.runtime.next_message_sequence(
            conversation.id
        )
        now = utc_now()
        user_message = ConversationMessage(
            conversation_id=conversation.id,
            role="user",
            status="completed",
            content=payload.content,
            sequence=next_sequence,
            metadata_json=payload.metadata,
        )
        self.db.add(user_message)
        await self.db.flush()

        assistant_message = ConversationMessage(
            conversation_id=conversation.id,
            role="assistant",
            status="streaming",
            content="",
            sequence=next_sequence + 1,
            model_snapshot_json=conversation.agent_snapshot_json.get("model"),
        )
        self.db.add(assistant_message)
        await self.db.flush()

        run = ConversationRun(
            conversation_id=conversation.id,
            agent_id=agent.id,
            status="running",
            trigger_message_id=user_message.id,
            assistant_message_id=assistant_message.id,
            provider_instance_id=provider.id,
            provider_model_id=model.id,
            litellm_model=runtime_config.litellm_model,
            started_at=now,
            request_json={"messageCount": next_sequence + 1},
        )
        self.db.add(run)
        await self.db.flush()
        user_message.run_id = run.id
        assistant_message.run_id = run.id
        conversation.last_message_role = "user"
        conversation.last_message_preview = preview_text(payload.content)
        conversation.last_message_at = now
        conversation.message_count += 2
        conversation.version += 1
        await self.db.commit()

        messages = await self.runtime.build_llm_messages(
            conversation.id,
            agent,
            payload.content,
        )
        model_config = agent.model_config_json or {}
        return PreparedConversationRun(
            conversation=conversation,
            run=run,
            user_message=user_message,
            assistant_message=assistant_message,
            runtime_config=runtime_config,
            messages=messages,
            temperature=optional_float(model_config.get("temperature")),
            max_tokens=optional_int(
                model_config.get("maxTokens")
                or model_config.get("max_tokens")
            ),
        )

    async def _get_root_user(self) -> User:
        statement = select(User).where(
            User.username == "root",
            User.deleted_at.is_(None),
        )
        user = await self.db.scalar(statement)
        if user is not None:
            return user

        now = utc_now()
        user = User(
            username="root",
            email="root@hify.local",
            password_hash="seeded-root-password",
            role="admin",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def _get_conversation_or_raise(
        self,
        conversation_id: int,
    ) -> ConversationSession:
        user = await self._get_root_user()
        statement = select(ConversationSession).where(
            ConversationSession.id == conversation_id,
            ConversationSession.user_id == user.id,
            ConversationSession.deleted_at.is_(None),
        )
        conversation = await self.db.scalar(statement)
        if conversation is None:
            raise BizException(
                code=ConversationErrorCode.CONVERSATION_NOT_FOUND,
                message="会话不存在",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        return conversation
