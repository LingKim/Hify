"""Tool module ORM models."""

from __future__ import annotations

from datetime import datetime
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
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampSoftDeleteMixin


class Tool(TimestampSoftDeleteMixin, Base):
    """One executable HTTP tool definition."""

    __tablename__: ClassVar[str] = "tools"
    __table_args__ = (
        CheckConstraint("name <> ''", name="ck_tools_name_non_empty"),
        CheckConstraint("status <> ''", name="ck_tools_status_non_empty"),
        CheckConstraint("tool_type = 'http'", name="ck_tools_type_http"),
        CheckConstraint(
            "source_type IN ('manual', 'openapi')",
            name="ck_tools_source_type_allowed",
        ),
        CheckConstraint(
            "http_method IN ('GET', 'POST', 'PUT', 'PATCH', 'DELETE')",
            name="ck_tools_http_method_allowed",
        ),
        CheckConstraint("url <> ''", name="ck_tools_url_non_empty"),
        CheckConstraint(
            "timeout_seconds > 0",
            name="ck_tools_timeout_positive",
        ),
        CheckConstraint(
            "timeout_seconds <= 60",
            name="ck_tools_timeout_max",
        ),
        CheckConstraint(
            "last_test_latency_ms >= 0",
            name="ck_tools_last_test_latency_non_negative",
        ),
        CheckConstraint("version >= 1", name="ck_tools_version_positive"),
        Index("ix_tools_owner_user_id", "owner_user_id"),
        Index("ix_tools_status", "status"),
        Index("ix_tools_tool_type", "tool_type"),
        Index("ix_tools_source_type", "source_type"),
        Index("ix_tools_deleted_at", "deleted_at"),
        Index("ix_tools_updated_at", "updated_at"),
        Index(
            "ux_tools_owner_user_id_name_active",
            "owner_user_id",
            "name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    owner_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="draft",
        server_default="draft",
    )
    tool_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="http",
        server_default="http",
    )
    source_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="manual",
        server_default="manual",
    )
    http_method: Mapped[str] = mapped_column(String(16), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=15,
        server_default="15",
    )
    headers_template_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    query_template_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    body_template_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    content_type: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        default="application/json",
        server_default="application/json",
    )
    openapi_source_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    last_test_status: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )
    last_test_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_test_latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    auth_secret: Mapped[ToolAuthSecret | None] = relationship(
        back_populates="tool",
        primaryjoin=(
            "and_(Tool.id == ToolAuthSecret.tool_id, "
            "ToolAuthSecret.deleted_at.is_(None))"
        ),
        uselist=False,
    )
    parameters: Mapped[list[ToolParameter]] = relationship(
        back_populates="tool",
    )
    execution_logs: Mapped[list[ToolExecutionLog]] = relationship(
        back_populates="tool",
    )


class ToolAuthSecret(TimestampSoftDeleteMixin, Base):
    """Encrypted authentication material for one tool."""

    __tablename__: ClassVar[str] = "tool_auth_secrets"
    __table_args__ = (
        CheckConstraint(
            "auth_type IN ('none', 'bearer', 'api_key_header', "
            "'api_key_query')",
            name="ck_tool_auth_secrets_auth_type_allowed",
        ),
        CheckConstraint(
            "auth_type = 'none' OR secret_ciphertext IS NOT NULL",
            name="ck_tool_auth_secrets_ciphertext_required",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_tool_auth_secrets_version_positive",
        ),
        Index("ix_tool_auth_secrets_tool_id", "tool_id"),
        Index("ix_tool_auth_secrets_deleted_at", "deleted_at"),
        Index(
            "ux_tool_auth_secrets_tool_id_active",
            "tool_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    tool_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tools.id"),
        nullable=False,
    )
    auth_type: Mapped[str] = mapped_column(String(32), nullable=False)
    secret_ciphertext: Mapped[str | None] = mapped_column(Text, nullable=True)
    secret_masked: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    secret_fingerprint: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    encryption_key_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="v1",
        server_default="v1",
    )
    last_rotated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    tool: Mapped[Tool] = relationship(back_populates="auth_secret")


class ToolParameter(TimestampSoftDeleteMixin, Base):
    """One input parameter definition for a tool."""

    __tablename__: ClassVar[str] = "tool_parameters"
    __table_args__ = (
        CheckConstraint(
            "name <> ''",
            name="ck_tool_parameters_name_non_empty",
        ),
        CheckConstraint(
            "param_location IN ('path', 'query', 'header', 'body')",
            name="ck_tool_parameters_location_allowed",
        ),
        CheckConstraint(
            "schema_type IN ('string', 'number', 'integer', 'boolean', "
            "'object', 'array')",
            name="ck_tool_parameters_schema_type_allowed",
        ),
        CheckConstraint(
            "sort_order >= 0",
            name="ck_tool_parameters_sort_order_non_negative",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_tool_parameters_version_positive",
        ),
        Index("ix_tool_parameters_tool_id", "tool_id"),
        Index("ix_tool_parameters_param_location", "param_location"),
        Index("ix_tool_parameters_deleted_at", "deleted_at"),
        Index(
            "ux_tool_parameters_tool_id_name_location_active",
            "tool_id",
            "name",
            "param_location",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    tool_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tools.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    param_location: Mapped[str] = mapped_column(String(32), nullable=False)
    schema_type: Mapped[str] = mapped_column(String(32), nullable=False)
    is_required: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        server_default="false",
    )
    default_value_json: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    enum_values_json: Mapped[list[Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    schema_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    tool: Mapped[Tool] = relationship(back_populates="parameters")


class ToolExecutionLog(TimestampSoftDeleteMixin, Base):
    """One tool execution attempt for tests or conversations."""

    __tablename__: ClassVar[str] = "tool_execution_logs"
    __table_args__ = (
        CheckConstraint(
            "source IN ('test', 'conversation')",
            name="ck_tool_execution_logs_source_allowed",
        ),
        CheckConstraint(
            "status IN ('success', 'failed', 'timeout')",
            name="ck_tool_execution_logs_status_allowed",
        ),
        CheckConstraint(
            "request_method <> ''",
            name="ck_tool_execution_logs_method_non_empty",
        ),
        CheckConstraint(
            "request_url <> ''",
            name="ck_tool_execution_logs_url_non_empty",
        ),
        CheckConstraint(
            "response_status_code IS NULL OR "
            "(response_status_code >= 100 AND response_status_code <= 599)",
            name="ck_tool_execution_logs_response_status_range",
        ),
        CheckConstraint(
            "latency_ms >= 0",
            name="ck_tool_execution_logs_latency_non_negative",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_tool_execution_logs_version_positive",
        ),
        Index("ix_tool_execution_logs_tool_id", "tool_id"),
        Index("ix_tool_execution_logs_executor_user_id", "executor_user_id"),
        Index("ix_tool_execution_logs_source", "source"),
        Index("ix_tool_execution_logs_status", "status"),
        Index("ix_tool_execution_logs_created_at", "created_at"),
        Index("ix_tool_execution_logs_conversation_id", "conversation_id"),
        Index("ix_tool_execution_logs_run_id", "run_id"),
    )

    tool_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tools.id"),
        nullable=False,
    )
    executor_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
    )
    conversation_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )
    run_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    request_method: Mapped[str] = mapped_column(String(16), nullable=False)
    request_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    request_headers_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    request_body_preview: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    response_status_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    response_headers_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    response_body_preview: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    tool: Mapped[Tool] = relationship(back_populates="execution_logs")
