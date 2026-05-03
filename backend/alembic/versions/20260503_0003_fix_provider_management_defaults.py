"""fix provider management column defaults

Revision ID: 20260503_0003
Revises: 20260503_0002
Create Date: 2026-05-03 13:58:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260503_0003"
down_revision: str | None = "20260503_0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    for table_name in (
        "provider_instances",
        "provider_auth_secrets",
        "provider_models",
        "provider_health_statuses",
    ):
        op.alter_column(
            table_name,
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            existing_nullable=False,
        )
        op.alter_column(
            table_name,
            "updated_at",
            existing_type=sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            existing_nullable=False,
        )
        op.alter_column(
            table_name,
            "version",
            existing_type=sa.Integer(),
            server_default=sa.text("1"),
            existing_nullable=False,
        )

    op.alter_column(
        "provider_instances",
        "status",
        existing_type=sa.String(length=32),
        server_default=sa.text("'draft'"),
        existing_nullable=False,
    )
    op.alter_column(
        "provider_instances",
        "is_default",
        existing_type=sa.Boolean(),
        server_default=sa.text("false"),
        existing_nullable=False,
    )
    op.alter_column(
        "provider_instances",
        "priority",
        existing_type=sa.Integer(),
        server_default=sa.text("0"),
        existing_nullable=False,
    )

    op.alter_column(
        "provider_models",
        "status",
        existing_type=sa.String(length=32),
        server_default=sa.text("'active'"),
        existing_nullable=False,
    )
    for column_name, default_value in (
        ("is_default", "false"),
        ("sort_order", "0"),
        ("supports_chat", "true"),
        ("supports_stream", "true"),
        ("supports_tools", "false"),
        ("supports_structured_output", "false"),
        ("supports_vision_input", "false"),
        ("supports_audio_input", "false"),
        ("supports_reasoning", "false"),
        ("supports_embeddings", "false"),
        ("temperature_supported", "true"),
        ("top_p_supported", "true"),
    ):
        op.alter_column(
            "provider_models",
            column_name,
            existing_type=sa.Boolean()
            if column_name
            not in {"sort_order"}
            else sa.Integer(),
            server_default=sa.text(default_value),
            existing_nullable=False,
        )

    for column_name, default_value in (
        ("health_state", "'unknown'"),
        ("auth_state", "'unknown'"),
        ("connectivity_state", "'unknown'"),
        ("inference_state", "'never'"),
        ("consecutive_failures", "0"),
    ):
        op.alter_column(
            "provider_health_statuses",
            column_name,
            existing_type=sa.String(length=32)
            if column_name != "consecutive_failures"
            else sa.Integer(),
            server_default=sa.text(default_value),
            existing_nullable=False,
        )


def downgrade() -> None:
    for table_name in (
        "provider_instances",
        "provider_auth_secrets",
        "provider_models",
        "provider_health_statuses",
    ):
        op.alter_column(
            table_name,
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            server_default=None,
            existing_nullable=False,
        )
        op.alter_column(
            table_name,
            "updated_at",
            existing_type=sa.DateTime(timezone=True),
            server_default=None,
            existing_nullable=False,
        )
        op.alter_column(
            table_name,
            "version",
            existing_type=sa.Integer(),
            server_default=None,
            existing_nullable=False,
        )

    for table_name, column_name, column_type in (
        ("provider_instances", "status", sa.String(length=32)),
        ("provider_instances", "is_default", sa.Boolean()),
        ("provider_instances", "priority", sa.Integer()),
        ("provider_models", "status", sa.String(length=32)),
        ("provider_models", "is_default", sa.Boolean()),
        ("provider_models", "sort_order", sa.Integer()),
        ("provider_models", "supports_chat", sa.Boolean()),
        ("provider_models", "supports_stream", sa.Boolean()),
        ("provider_models", "supports_tools", sa.Boolean()),
        ("provider_models", "supports_structured_output", sa.Boolean()),
        ("provider_models", "supports_vision_input", sa.Boolean()),
        ("provider_models", "supports_audio_input", sa.Boolean()),
        ("provider_models", "supports_reasoning", sa.Boolean()),
        ("provider_models", "supports_embeddings", sa.Boolean()),
        ("provider_models", "temperature_supported", sa.Boolean()),
        ("provider_models", "top_p_supported", sa.Boolean()),
        ("provider_health_statuses", "health_state", sa.String(length=32)),
        ("provider_health_statuses", "auth_state", sa.String(length=32)),
        (
            "provider_health_statuses",
            "connectivity_state",
            sa.String(length=32),
        ),
        (
            "provider_health_statuses",
            "inference_state",
            sa.String(length=32),
        ),
        (
            "provider_health_statuses",
            "consecutive_failures",
            sa.Integer(),
        ),
    ):
        op.alter_column(
            table_name,
            column_name,
            existing_type=column_type,
            server_default=None,
            existing_nullable=False,
        )
