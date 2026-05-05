"""create conversation tables

Revision ID: 20260505_0006
Revises: 20260505_0005
Create Date: 2026-05-05 14:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260505_0006"
down_revision: str | None = "20260505_0005"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "version",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "conversation_sessions",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("agent_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column(
            "channel",
            sa.String(length=32),
            server_default=sa.text("'web'"),
            nullable=False,
        ),
        sa.Column("agent_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("last_message_role", sa.String(length=32), nullable=True),
        sa.Column("last_message_preview", sa.String(length=500), nullable=True),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "message_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        *_audit_columns(),
        sa.CheckConstraint(
            "title <> ''",
            name=op.f("ck_conversation_sessions_title_non_empty"),
        ),
        sa.CheckConstraint(
            "status <> ''",
            name=op.f("ck_conversation_sessions_status_non_empty"),
        ),
        sa.CheckConstraint(
            "channel <> ''",
            name=op.f("ck_conversation_sessions_channel_non_empty"),
        ),
        sa.CheckConstraint(
            "message_count >= 0",
            name=op.f("ck_conversation_sessions_message_count_non_negative"),
        ),
        sa.CheckConstraint(
            "version >= 1",
            name=op.f("ck_conversation_sessions_version_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_conversation_sessions_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            name=op.f("fk_conversation_sessions_agent_id_agents"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversation_sessions")),
    )
    op.create_index(
        op.f("ix_conversation_sessions_agent_id"),
        "conversation_sessions",
        ["agent_id"],
    )
    op.create_index(
        op.f("ix_conversation_sessions_deleted_at"),
        "conversation_sessions",
        ["deleted_at"],
    )
    op.create_index(
        op.f("ix_conversation_sessions_last_message_at"),
        "conversation_sessions",
        ["last_message_at"],
    )
    op.create_index(
        op.f("ix_conversation_sessions_status"),
        "conversation_sessions",
        ["status"],
    )
    op.create_index(
        op.f("ix_conversation_sessions_user_id"),
        "conversation_sessions",
        ["user_id"],
    )
    op.create_index(
        op.f("ix_conversation_sessions_user_id_status"),
        "conversation_sessions",
        ["user_id", "status"],
    )

    op.create_table(
        "conversation_runs",
        sa.Column("conversation_id", sa.BigInteger(), nullable=False),
        sa.Column("agent_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default=sa.text("'running'"),
            nullable=False,
        ),
        sa.Column("trigger_message_id", sa.BigInteger(), nullable=True),
        sa.Column("assistant_message_id", sa.BigInteger(), nullable=True),
        sa.Column("provider_instance_id", sa.BigInteger(), nullable=True),
        sa.Column("provider_model_id", sa.BigInteger(), nullable=True),
        sa.Column("litellm_model", sa.String(length=255), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("input_token_count", sa.Integer(), nullable=True),
        sa.Column("output_token_count", sa.Integer(), nullable=True),
        sa.Column("total_token_count", sa.Integer(), nullable=True),
        sa.Column("request_json", sa.JSON(), nullable=True),
        sa.Column("response_json", sa.JSON(), nullable=True),
        sa.Column("error_json", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        *_audit_columns(),
        sa.CheckConstraint(
            "status <> ''",
            name=op.f("ck_conversation_runs_status_non_empty"),
        ),
        sa.CheckConstraint(
            "latency_ms >= 0",
            name=op.f("ck_conversation_runs_latency_ms_non_negative"),
        ),
        sa.CheckConstraint(
            "version >= 1",
            name=op.f("ck_conversation_runs_version_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversation_sessions.id"],
            name=op.f("fk_conversation_runs_conversation_id_conversation_sessions"),
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            name=op.f("fk_conversation_runs_agent_id_agents"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversation_runs")),
    )
    op.create_index(
        op.f("ix_conversation_runs_agent_id"),
        "conversation_runs",
        ["agent_id"],
    )
    op.create_index(
        op.f("ix_conversation_runs_conversation_id"),
        "conversation_runs",
        ["conversation_id"],
    )
    op.create_index(
        op.f("ix_conversation_runs_deleted_at"),
        "conversation_runs",
        ["deleted_at"],
    )
    op.create_index(
        op.f("ix_conversation_runs_started_at"),
        "conversation_runs",
        ["started_at"],
    )
    op.create_index(
        op.f("ix_conversation_runs_status"),
        "conversation_runs",
        ["status"],
    )

    op.create_table(
        "conversation_messages",
        sa.Column("conversation_id", sa.BigInteger(), nullable=False),
        sa.Column("run_id", sa.BigInteger(), nullable=True),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "content_format",
            sa.String(length=32),
            server_default=sa.text("'text'"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("model_snapshot_json", sa.JSON(), nullable=True),
        sa.Column("tool_call_json", sa.JSON(), nullable=True),
        sa.Column("error_json", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        *_audit_columns(),
        sa.CheckConstraint(
            "role <> ''",
            name=op.f("ck_conversation_messages_role_non_empty"),
        ),
        sa.CheckConstraint(
            "status <> ''",
            name=op.f("ck_conversation_messages_status_non_empty"),
        ),
        sa.CheckConstraint(
            "content_format <> ''",
            name=op.f("ck_conversation_messages_content_format_non_empty"),
        ),
        sa.CheckConstraint(
            "sequence >= 1",
            name=op.f("ck_conversation_messages_sequence_positive"),
        ),
        sa.CheckConstraint(
            "version >= 1",
            name=op.f("ck_conversation_messages_version_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversation_sessions.id"],
            name=op.f(
                "fk_conversation_messages_conversation_id_conversation_sessions"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["conversation_runs.id"],
            name=op.f("fk_conversation_messages_run_id_conversation_runs"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversation_messages")),
        sa.UniqueConstraint(
            "conversation_id",
            "sequence",
            "deleted_at",
            name=op.f("uq_conversation_messages_conversation_sequence_deleted"),
        ),
    )
    op.create_index(
        op.f("ix_conversation_messages_conversation_id"),
        "conversation_messages",
        ["conversation_id"],
    )
    op.create_index(
        op.f("ix_conversation_messages_created_at"),
        "conversation_messages",
        ["created_at"],
    )
    op.create_index(
        op.f("ix_conversation_messages_deleted_at"),
        "conversation_messages",
        ["deleted_at"],
    )
    op.create_index(
        op.f("ix_conversation_messages_role"),
        "conversation_messages",
        ["role"],
    )
    op.create_index(
        op.f("ix_conversation_messages_run_id"),
        "conversation_messages",
        ["run_id"],
    )

    op.create_foreign_key(
        op.f("fk_conversation_runs_trigger_message_id_conversation_messages"),
        "conversation_runs",
        "conversation_messages",
        ["trigger_message_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_conversation_runs_assistant_message_id_conversation_messages"),
        "conversation_runs",
        "conversation_messages",
        ["assistant_message_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_conversation_runs_assistant_message_id_conversation_messages"),
        "conversation_runs",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_conversation_runs_trigger_message_id_conversation_messages"),
        "conversation_runs",
        type_="foreignkey",
    )
    op.drop_table("conversation_messages")
    op.drop_table("conversation_runs")
    op.drop_table("conversation_sessions")
