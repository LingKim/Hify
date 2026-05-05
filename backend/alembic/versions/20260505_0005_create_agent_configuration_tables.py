"""create agent configuration tables

Revision ID: 20260505_0005
Revises: 20260503_0004
Create Date: 2026-05-05 10:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260505_0005"
down_revision: str | None = "20260503_0004"
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
        "agents",
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default=sa.text("'draft'"),
            nullable=False,
        ),
        sa.Column(
            "orchestration_mode",
            sa.String(length=32),
            server_default=sa.text("'agent'"),
            nullable=False,
        ),
        sa.Column("provider_instance_id", sa.BigInteger(), nullable=True),
        sa.Column("provider_model_id", sa.BigInteger(), nullable=True),
        sa.Column("system_prompt", sa.Text(), nullable=True),
        sa.Column("opening_message", sa.Text(), nullable=True),
        sa.Column("model_config_json", sa.JSON(), nullable=True),
        sa.Column("runtime_config_json", sa.JSON(), nullable=True),
        sa.Column("workflow_ref_json", sa.JSON(), nullable=True),
        sa.Column("tags_json", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        *_audit_columns(),
        sa.CheckConstraint(
            "name <> ''",
            name=op.f("ck_agents_name_non_empty"),
        ),
        sa.CheckConstraint(
            "status <> ''",
            name=op.f("ck_agents_status_non_empty"),
        ),
        sa.CheckConstraint(
            "orchestration_mode <> ''",
            name=op.f("ck_agents_orchestration_mode_non_empty"),
        ),
        sa.CheckConstraint(
            "version >= 1",
            name=op.f("ck_agents_version_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["provider_model_id"],
            ["provider_models.id"],
            name=op.f("fk_agents_provider_model_id_provider_models"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agents")),
    )
    op.create_index(
        op.f("ix_agents_deleted_at"),
        "agents",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agents_orchestration_mode"),
        "agents",
        ["orchestration_mode"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agents_provider_model_id"),
        "agents",
        ["provider_model_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agents_status"),
        "agents",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ux_agents_name_active",
        "agents",
        ["name"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "agent_tool_bindings",
        sa.Column("agent_id", sa.BigInteger(), nullable=False),
        sa.Column("tool_id", sa.BigInteger(), nullable=False),
        sa.Column("binding_name", sa.String(length=128), nullable=True),
        sa.Column(
            "is_enabled",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "sort_order",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("config_json", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        *_audit_columns(),
        sa.CheckConstraint(
            "tool_id > 0",
            name=op.f("ck_agent_tool_bindings_tool_id_positive"),
        ),
        sa.CheckConstraint(
            "sort_order >= 0",
            name=op.f("ck_agent_tool_bindings_sort_order_non_negative"),
        ),
        sa.CheckConstraint(
            "version >= 1",
            name=op.f("ck_agent_tool_bindings_version_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            name=op.f("fk_agent_tool_bindings_agent_id_agents"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_tool_bindings")),
    )
    op.create_index(
        op.f("ix_agent_tool_bindings_agent_id"),
        "agent_tool_bindings",
        ["agent_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_tool_bindings_deleted_at"),
        "agent_tool_bindings",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_tool_bindings_tool_id"),
        "agent_tool_bindings",
        ["tool_id"],
        unique=False,
    )
    op.create_index(
        "ux_agent_tool_bindings_agent_id_tool_id_active",
        "agent_tool_bindings",
        ["agent_id", "tool_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "agent_knowledge_bindings",
        sa.Column("agent_id", sa.BigInteger(), nullable=False),
        sa.Column("knowledge_base_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "is_enabled",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "sort_order",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("retrieval_config_json", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        *_audit_columns(),
        sa.CheckConstraint(
            "knowledge_base_id > 0",
            name=op.f(
                "ck_agent_knowledge_bindings_knowledge_base_id_positive"
            ),
        ),
        sa.CheckConstraint(
            "sort_order >= 0",
            name=op.f("ck_agent_knowledge_bindings_sort_order_non_negative"),
        ),
        sa.CheckConstraint(
            "version >= 1",
            name=op.f("ck_agent_knowledge_bindings_version_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            name=op.f("fk_agent_knowledge_bindings_agent_id_agents"),
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_agent_knowledge_bindings"),
        ),
    )
    op.create_index(
        op.f("ix_agent_knowledge_bindings_agent_id"),
        "agent_knowledge_bindings",
        ["agent_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_knowledge_bindings_deleted_at"),
        "agent_knowledge_bindings",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_knowledge_bindings_knowledge_base_id"),
        "agent_knowledge_bindings",
        ["knowledge_base_id"],
        unique=False,
    )
    op.create_index(
        "ux_agent_knowledge_bindings_agent_id_knowledge_base_id_active",
        "agent_knowledge_bindings",
        ["agent_id", "knowledge_base_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "ux_agent_knowledge_bindings_agent_id_knowledge_base_id_active",
        table_name="agent_knowledge_bindings",
    )
    op.drop_index(
        op.f("ix_agent_knowledge_bindings_knowledge_base_id"),
        table_name="agent_knowledge_bindings",
    )
    op.drop_index(
        op.f("ix_agent_knowledge_bindings_deleted_at"),
        table_name="agent_knowledge_bindings",
    )
    op.drop_index(
        op.f("ix_agent_knowledge_bindings_agent_id"),
        table_name="agent_knowledge_bindings",
    )
    op.drop_table("agent_knowledge_bindings")

    op.drop_index(
        "ux_agent_tool_bindings_agent_id_tool_id_active",
        table_name="agent_tool_bindings",
    )
    op.drop_index(
        op.f("ix_agent_tool_bindings_tool_id"),
        table_name="agent_tool_bindings",
    )
    op.drop_index(
        op.f("ix_agent_tool_bindings_deleted_at"),
        table_name="agent_tool_bindings",
    )
    op.drop_index(
        op.f("ix_agent_tool_bindings_agent_id"),
        table_name="agent_tool_bindings",
    )
    op.drop_table("agent_tool_bindings")

    op.drop_index("ux_agents_name_active", table_name="agents")
    op.drop_index(op.f("ix_agents_status"), table_name="agents")
    op.drop_index(op.f("ix_agents_provider_model_id"), table_name="agents")
    op.drop_index(op.f("ix_agents_orchestration_mode"), table_name="agents")
    op.drop_index(op.f("ix_agents_deleted_at"), table_name="agents")
    op.drop_table("agents")
