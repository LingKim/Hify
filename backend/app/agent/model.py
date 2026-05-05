"""Agent configuration ORM models."""

from __future__ import annotations

from typing import Any, ClassVar

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampSoftDeleteMixin


class Agent(TimestampSoftDeleteMixin, Base):
    """A configurable agent that can be loaded by conversation."""

    __tablename__: ClassVar[str] = "agents"
    __table_args__ = (
        CheckConstraint("name <> ''", name="ck_agents_name_non_empty"),
        CheckConstraint("status <> ''", name="ck_agents_status_non_empty"),
        CheckConstraint(
            "orchestration_mode <> ''",
            name="ck_agents_orchestration_mode_non_empty",
        ),
        CheckConstraint("version >= 1", name="ck_agents_version_positive"),
        Index(
            "ux_agents_name_active",
            "name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="draft",
        server_default="draft",
    )
    orchestration_mode: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="agent",
        server_default="agent",
    )
    provider_instance_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )
    provider_model_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("provider_models.id"),
        nullable=True,
    )
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    opening_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_config_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    runtime_config_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    workflow_ref_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    tags_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    tool_bindings: Mapped[list[AgentToolBinding]] = relationship(
        back_populates="agent",
    )
    knowledge_bindings: Mapped[list[AgentKnowledgeBinding]] = relationship(
        back_populates="agent",
    )


class AgentToolBinding(TimestampSoftDeleteMixin, Base):
    """Tool binding configured for one agent."""

    __tablename__: ClassVar[str] = "agent_tool_bindings"
    __table_args__ = (
        CheckConstraint(
            "tool_id > 0",
            name="ck_agent_tool_bindings_tool_id_positive",
        ),
        CheckConstraint(
            "sort_order >= 0",
            name="ck_agent_tool_bindings_sort_order_non_negative",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_agent_tool_bindings_version_positive",
        ),
        Index(
            "ux_agent_tool_bindings_agent_id_tool_id_active",
            "agent_id",
            "tool_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    agent_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("agents.id"),
        nullable=False,
    )
    tool_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    binding_name: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    config_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    agent: Mapped[Agent] = relationship(back_populates="tool_bindings")


class AgentKnowledgeBinding(TimestampSoftDeleteMixin, Base):
    """Knowledge-base binding configured for one agent."""

    __tablename__: ClassVar[str] = "agent_knowledge_bindings"
    __table_args__ = (
        CheckConstraint(
            "knowledge_base_id > 0",
            name="ck_agent_knowledge_bindings_knowledge_base_id_positive",
        ),
        CheckConstraint(
            "sort_order >= 0",
            name="ck_agent_knowledge_bindings_sort_order_non_negative",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_agent_knowledge_bindings_version_positive",
        ),
        Index(
            "ux_agent_knowledge_bindings_agent_id_knowledge_base_id_active",
            "agent_id",
            "knowledge_base_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    agent_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("agents.id"),
        nullable=False,
    )
    knowledge_base_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    retrieval_config_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    agent: Mapped[Agent] = relationship(back_populates="knowledge_bindings")
