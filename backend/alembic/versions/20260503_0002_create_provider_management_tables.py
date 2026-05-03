"""create provider management tables

Revision ID: 20260503_0002
Revises: 20260502_0001
Create Date: 2026-05-03 12:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260503_0002"
down_revision: str | None = "20260502_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "provider_instances",
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("provider_type", sa.String(length=64), nullable=False),
        sa.Column("api_family", sa.String(length=64), nullable=False),
        sa.Column("base_url", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint("name <> ''", name=op.f("ck_provider_instances_name_non_empty")),
        sa.CheckConstraint("priority >= 0", name=op.f("ck_provider_instances_priority_non_negative")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_provider_instances")),
        sa.UniqueConstraint("name", name=op.f("uq_provider_instances_name")),
    )
    op.create_index(
        op.f("ix_provider_instances_deleted_at"),
        "provider_instances",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_provider_instances_provider_type"),
        "provider_instances",
        ["provider_type"],
        unique=False,
    )

    op.create_table(
        "provider_auth_secrets",
        sa.Column("provider_instance_id", sa.BigInteger(), nullable=False),
        sa.Column("auth_type", sa.String(length=32), nullable=False),
        sa.Column("secret_ciphertext", sa.Text(), nullable=False),
        sa.Column("secret_masked", sa.String(length=255), nullable=False),
        sa.Column("secret_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("encryption_key_version", sa.String(length=64), nullable=False),
        sa.Column("last_rotated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "secret_ciphertext <> ''",
            name=op.f("ck_provider_auth_secrets_ciphertext_non_empty"),
        ),
        sa.ForeignKeyConstraint(
            ["provider_instance_id"],
            ["provider_instances.id"],
            name=op.f("fk_provider_auth_secrets_provider_instance_id_provider_instances"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_provider_auth_secrets")),
        sa.UniqueConstraint(
            "provider_instance_id",
            name=op.f("uq_provider_auth_secrets_provider_instance_id"),
        ),
    )
    op.create_index(
        op.f("ix_provider_auth_secrets_deleted_at"),
        "provider_auth_secrets",
        ["deleted_at"],
        unique=False,
    )

    op.create_table(
        "provider_models",
        sa.Column("provider_instance_id", sa.BigInteger(), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("supports_chat", sa.Boolean(), nullable=False),
        sa.Column("supports_stream", sa.Boolean(), nullable=False),
        sa.Column("supports_tools", sa.Boolean(), nullable=False),
        sa.Column("supports_structured_output", sa.Boolean(), nullable=False),
        sa.Column("supports_vision_input", sa.Boolean(), nullable=False),
        sa.Column("supports_audio_input", sa.Boolean(), nullable=False),
        sa.Column("supports_reasoning", sa.Boolean(), nullable=False),
        sa.Column("supports_embeddings", sa.Boolean(), nullable=False),
        sa.Column("context_window", sa.Integer(), nullable=True),
        sa.Column("max_output_tokens", sa.Integer(), nullable=True),
        sa.Column("max_input_tokens", sa.Integer(), nullable=True),
        sa.Column("temperature_supported", sa.Boolean(), nullable=False),
        sa.Column("top_p_supported", sa.Boolean(), nullable=False),
        sa.Column("tags_json", sa.JSON(), nullable=True),
        sa.Column("pricing_json", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "model_name <> ''",
            name=op.f("ck_provider_models_model_name_non_empty"),
        ),
        sa.CheckConstraint(
            "sort_order >= 0",
            name=op.f("ck_provider_models_sort_order_non_negative"),
        ),
        sa.ForeignKeyConstraint(
            ["provider_instance_id"],
            ["provider_instances.id"],
            name=op.f("fk_provider_models_provider_instance_id_provider_instances"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_provider_models")),
        sa.UniqueConstraint(
            "provider_instance_id",
            "model_name",
            name=op.f("uq_provider_models_provider_instance_id_model_name"),
        ),
    )
    op.create_index(
        op.f("ix_provider_models_deleted_at"),
        "provider_models",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_provider_models_provider_instance_id"),
        "provider_models",
        ["provider_instance_id"],
        unique=False,
    )

    op.create_table(
        "provider_health_statuses",
        sa.Column("provider_instance_id", sa.BigInteger(), nullable=False),
        sa.Column("health_state", sa.String(length=32), nullable=False),
        sa.Column("auth_state", sa.String(length=32), nullable=False),
        sa.Column("connectivity_state", sa.String(length=32), nullable=False),
        sa.Column("inference_state", sa.String(length=32), nullable=False),
        sa.Column("last_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False),
        sa.Column("latency_ms_p50", sa.Integer(), nullable=True),
        sa.Column("latency_ms_p95", sa.Integer(), nullable=True),
        sa.Column("last_error_code", sa.String(length=64), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["provider_instance_id"],
            ["provider_instances.id"],
            name=op.f("fk_provider_health_statuses_provider_instance_id_provider_instances"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_provider_health_statuses")),
        sa.UniqueConstraint(
            "provider_instance_id",
            name=op.f("uq_provider_health_statuses_provider_instance_id"),
        ),
    )
    op.create_index(
        op.f("ix_provider_health_statuses_deleted_at"),
        "provider_health_statuses",
        ["deleted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_provider_health_statuses_deleted_at"),
        table_name="provider_health_statuses",
    )
    op.drop_table("provider_health_statuses")

    op.drop_index(op.f("ix_provider_models_provider_instance_id"), table_name="provider_models")
    op.drop_index(op.f("ix_provider_models_deleted_at"), table_name="provider_models")
    op.drop_table("provider_models")

    op.drop_index(
        op.f("ix_provider_auth_secrets_deleted_at"),
        table_name="provider_auth_secrets",
    )
    op.drop_table("provider_auth_secrets")

    op.drop_index(
        op.f("ix_provider_instances_provider_type"),
        table_name="provider_instances",
    )
    op.drop_index(
        op.f("ix_provider_instances_deleted_at"),
        table_name="provider_instances",
    )
    op.drop_table("provider_instances")
