"""Conversation module ORM models."""

from __future__ import annotations

from typing import Any, ClassVar

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampSoftDeleteMixin


class ConversationSession(TimestampSoftDeleteMixin, Base):
    """A user's ongoing conversation with one agent."""

    __tablename__: ClassVar[str] = "conversation_sessions"
    __table_args__ = (
        CheckConstraint(
            "title <> ''",
            name="ck_conversation_sessions_title_non_empty",
        ),
        CheckConstraint(
            "status <> ''",
            name="ck_conversation_sessions_status_non_empty",
        ),
        CheckConstraint(
            "channel <> ''",
            name="ck_conversation_sessions_channel_non_empty",
        ),
        CheckConstraint(
            "message_count >= 0",
            name="ck_conversation_sessions_message_count_non_negative",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_conversation_sessions_version_positive",
        ),
        Index("ix_conversation_sessions_user_id", "user_id"),
        Index("ix_conversation_sessions_agent_id", "agent_id"),
        Index("ix_conversation_sessions_status", "status"),
        Index("ix_conversation_sessions_user_id_status", "user_id", "status"),
        Index("ix_conversation_sessions_last_message_at", "last_message_at"),
        Index("ix_conversation_sessions_deleted_at", "deleted_at"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )
    agent_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("agents.id"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        server_default="active",
    )
    channel: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="web",
        server_default="web",
    )
    agent_snapshot_json: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )
    last_message_role: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )
    last_message_preview: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    last_message_at: Mapped[Any | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    message_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )


class ConversationRun(TimestampSoftDeleteMixin, Base):
    """One execution run triggered by a user message."""

    __tablename__: ClassVar[str] = "conversation_runs"
    __table_args__ = (
        CheckConstraint(
            "status <> ''",
            name="ck_conversation_runs_status_non_empty",
        ),
        CheckConstraint(
            "latency_ms >= 0",
            name="ck_conversation_runs_latency_ms_non_negative",
        ),
        CheckConstraint(
            "input_token_count >= 0",
            name="ck_conversation_runs_input_token_count_non_negative",
        ),
        CheckConstraint(
            "output_token_count >= 0",
            name="ck_conversation_runs_output_token_count_non_negative",
        ),
        CheckConstraint(
            "total_token_count >= 0",
            name="ck_conversation_runs_total_token_count_non_negative",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_conversation_runs_version_positive",
        ),
        Index("ix_conversation_runs_conversation_id", "conversation_id"),
        Index("ix_conversation_runs_agent_id", "agent_id"),
        Index("ix_conversation_runs_status", "status"),
        Index("ix_conversation_runs_started_at", "started_at"),
        Index("ix_conversation_runs_deleted_at", "deleted_at"),
    )

    conversation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("conversation_sessions.id"),
        nullable=False,
    )
    agent_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("agents.id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="running",
        server_default="running",
    )
    trigger_message_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("conversation_messages.id", use_alter=True),
        nullable=True,
    )
    assistant_message_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("conversation_messages.id", use_alter=True),
        nullable=True,
    )
    provider_instance_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )
    provider_model_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )
    litellm_model: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    started_at: Mapped[Any | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Any | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_token_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    output_token_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    total_token_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    request_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    response_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    error_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )


class ConversationMessage(TimestampSoftDeleteMixin, Base):
    """One message inside a conversation."""

    __tablename__: ClassVar[str] = "conversation_messages"
    __table_args__ = (
        CheckConstraint(
            "role <> ''",
            name="ck_conversation_messages_role_non_empty",
        ),
        CheckConstraint(
            "status <> ''",
            name="ck_conversation_messages_status_non_empty",
        ),
        CheckConstraint(
            "content_format <> ''",
            name="ck_conversation_messages_content_format_non_empty",
        ),
        CheckConstraint(
            "sequence >= 1",
            name="ck_conversation_messages_sequence_positive",
        ),
        CheckConstraint(
            "token_count >= 0",
            name="ck_conversation_messages_token_count_non_negative",
        ),
        CheckConstraint(
            "latency_ms >= 0",
            name="ck_conversation_messages_latency_ms_non_negative",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_conversation_messages_version_positive",
        ),
        UniqueConstraint(
            "conversation_id",
            "sequence",
            "deleted_at",
            name="uq_conversation_messages_conversation_sequence_deleted",
        ),
        Index("ix_conversation_messages_conversation_id", "conversation_id"),
        Index("ix_conversation_messages_run_id", "run_id"),
        Index("ix_conversation_messages_role", "role"),
        Index("ix_conversation_messages_created_at", "created_at"),
        Index("ix_conversation_messages_deleted_at", "deleted_at"),
    )

    conversation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("conversation_sessions.id"),
        nullable=False,
    )
    run_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("conversation_runs.id"),
        nullable=True,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content_format: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="text",
        server_default="text",
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model_snapshot_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    tool_call_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    error_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )


Conversation = ConversationSession
