"""LLM provider management ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampSoftDeleteMixin


class ProviderInstance(TimestampSoftDeleteMixin, Base):
    """A provider account instance managed by the platform."""

    __tablename__: ClassVar[str] = "provider_instances"
    __table_args__ = (
        UniqueConstraint("name", name="uq_provider_instances_name"),
        CheckConstraint(
            "name <> ''",
            name="ck_provider_instances_name_non_empty",
        ),
        CheckConstraint(
            "priority >= 0",
            name="ck_provider_instances_priority_non_negative",
        ),
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(64), nullable=False)
    api_family: Mapped[str] = mapped_column(String(64), nullable=False)
    base_url: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="draft",
        server_default="draft",
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
    )

    auth_secret: Mapped[ProviderAuthSecret | None] = relationship(
        back_populates="provider_instance",
        uselist=False,
    )
    models: Mapped[list[ProviderModel]] = relationship(
        back_populates="provider_instance",
    )
    health_status: Mapped[ProviderHealthStatus | None] = relationship(
        back_populates="provider_instance",
        uselist=False,
    )


class ProviderAuthSecret(TimestampSoftDeleteMixin, Base):
    """Encrypted authentication material for one provider instance."""

    __tablename__: ClassVar[str] = "provider_auth_secrets"
    __table_args__ = (
        UniqueConstraint(
            "provider_instance_id",
            name="uq_provider_auth_secrets_provider_instance_id",
        ),
        CheckConstraint(
            "secret_ciphertext <> ''",
            name="ck_provider_auth_secrets_ciphertext_non_empty",
        ),
    )

    provider_instance_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("provider_instances.id"),
        nullable=False,
    )
    auth_type: Mapped[str] = mapped_column(String(32), nullable=False)
    secret_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    secret_masked: Mapped[str] = mapped_column(String(255), nullable=False)
    secret_fingerprint: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    encryption_key_version: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    last_rotated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
    )

    provider_instance: Mapped[ProviderInstance] = relationship(
        back_populates="auth_secret",
    )


class ProviderModel(TimestampSoftDeleteMixin, Base):
    """A manually managed model under a provider instance."""

    __tablename__: ClassVar[str] = "provider_models"
    __table_args__ = (
        CheckConstraint(
            "model_name <> ''",
            name="ck_provider_models_model_name_non_empty",
        ),
        CheckConstraint(
            "sort_order >= 0",
            name="ck_provider_models_sort_order_non_negative",
        ),
        Index(
            "ux_provider_models_provider_instance_id_model_name_active",
            "provider_instance_id",
            "model_name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    provider_instance_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("provider_instances.id"),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        server_default="active",
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    supports_chat: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    supports_stream: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    supports_tools: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    supports_structured_output: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    supports_vision_input: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    supports_audio_input: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    supports_reasoning: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    supports_embeddings: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    context_window: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )
    max_output_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )
    max_input_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )
    temperature_supported: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    top_p_supported: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    tags_json: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
    )
    pricing_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
    )

    provider_instance: Mapped[ProviderInstance] = relationship(
        back_populates="models",
    )


class ProviderHealthStatus(TimestampSoftDeleteMixin, Base):
    """Current health snapshot for a provider instance."""

    __tablename__: ClassVar[str] = "provider_health_statuses"
    __table_args__ = (
        UniqueConstraint(
            "provider_instance_id",
            name="uq_provider_health_statuses_provider_instance_id",
        ),
    )

    provider_instance_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("provider_instances.id"),
        nullable=False,
    )
    health_state: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="unknown",
        server_default="unknown",
    )
    auth_state: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="unknown",
        server_default="unknown",
    )
    connectivity_state: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="unknown",
        server_default="unknown",
    )
    inference_state: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="never",
        server_default="never",
    )
    last_check_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    last_success_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    last_failure_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    consecutive_failures: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    latency_ms_p50: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )
    latency_ms_p95: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )
    last_error_code: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        default=None,
    )
    last_error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )
    last_error_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    provider_instance: Mapped[ProviderInstance] = relationship(
        back_populates="health_status",
    )
