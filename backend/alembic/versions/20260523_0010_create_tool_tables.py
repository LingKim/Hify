"""create tool tables

Revision ID: 20260523_0010
Revises: 20260513_0009
Create Date: 2026-05-23 16:40:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260523_0010"
down_revision: str | None = "20260513_0009"
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
        "tools",
        sa.Column("owner_user_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default=sa.text("'draft'"),
            nullable=False,
        ),
        sa.Column(
            "tool_type",
            sa.String(length=32),
            server_default=sa.text("'http'"),
            nullable=False,
        ),
        sa.Column(
            "source_type",
            sa.String(length=32),
            server_default=sa.text("'manual'"),
            nullable=False,
        ),
        sa.Column("http_method", sa.String(length=16), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column(
            "timeout_seconds",
            sa.Integer(),
            server_default=sa.text("15"),
            nullable=False,
        ),
        sa.Column("headers_template_json", sa.JSON(), nullable=True),
        sa.Column("query_template_json", sa.JSON(), nullable=True),
        sa.Column("body_template_json", sa.JSON(), nullable=True),
        sa.Column(
            "content_type",
            sa.String(length=128),
            server_default=sa.text("'application/json'"),
            nullable=False,
        ),
        sa.Column("openapi_source_json", sa.JSON(), nullable=True),
        sa.Column("last_test_status", sa.String(length=32), nullable=True),
        sa.Column("last_test_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_test_latency_ms", sa.Integer(), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        *_audit_columns(),
        sa.CheckConstraint(
            "name <> ''",
            name=op.f("ck_tools_name_non_empty"),
        ),
        sa.CheckConstraint(
            "status <> ''",
            name=op.f("ck_tools_status_non_empty"),
        ),
        sa.CheckConstraint(
            "tool_type = 'http'",
            name=op.f("ck_tools_type_http"),
        ),
        sa.CheckConstraint(
            "source_type IN ('manual', 'openapi')",
            name=op.f("ck_tools_source_type_allowed"),
        ),
        sa.CheckConstraint(
            "http_method IN ('GET', 'POST', 'PUT', 'PATCH', 'DELETE')",
            name=op.f("ck_tools_http_method_allowed"),
        ),
        sa.CheckConstraint(
            "url <> ''",
            name=op.f("ck_tools_url_non_empty"),
        ),
        sa.CheckConstraint(
            "timeout_seconds > 0",
            name=op.f("ck_tools_timeout_positive"),
        ),
        sa.CheckConstraint(
            "timeout_seconds <= 60",
            name=op.f("ck_tools_timeout_max"),
        ),
        sa.CheckConstraint(
            "last_test_latency_ms >= 0",
            name=op.f("ck_tools_last_test_latency_non_negative"),
        ),
        sa.CheckConstraint(
            "version >= 1",
            name=op.f("ck_tools_version_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_user_id"],
            ["users.id"],
            name=op.f("fk_tools_owner_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tools")),
    )
    op.create_index(op.f("ix_tools_deleted_at"), "tools", ["deleted_at"])
    op.create_index(
        op.f("ix_tools_owner_user_id"),
        "tools",
        ["owner_user_id"],
    )
    op.create_index(op.f("ix_tools_source_type"), "tools", ["source_type"])
    op.create_index(op.f("ix_tools_status"), "tools", ["status"])
    op.create_index(op.f("ix_tools_tool_type"), "tools", ["tool_type"])
    op.create_index(op.f("ix_tools_updated_at"), "tools", ["updated_at"])
    op.create_index(
        "ux_tools_owner_user_id_name_active",
        "tools",
        ["owner_user_id", "name"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "tool_auth_secrets",
        sa.Column("tool_id", sa.BigInteger(), nullable=False),
        sa.Column("auth_type", sa.String(length=32), nullable=False),
        sa.Column("secret_ciphertext", sa.Text(), nullable=True),
        sa.Column("secret_masked", sa.String(length=255), nullable=True),
        sa.Column("secret_fingerprint", sa.String(length=128), nullable=True),
        sa.Column(
            "encryption_key_version",
            sa.String(length=32),
            server_default=sa.text("'v1'"),
            nullable=False,
        ),
        sa.Column("last_rotated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        *_audit_columns(),
        sa.CheckConstraint(
            "auth_type IN ('none', 'bearer', 'api_key_header', "
            "'api_key_query')",
            name=op.f("ck_tool_auth_secrets_auth_type_allowed"),
        ),
        sa.CheckConstraint(
            "auth_type = 'none' OR secret_ciphertext IS NOT NULL",
            name=op.f("ck_tool_auth_secrets_ciphertext_required"),
        ),
        sa.CheckConstraint(
            "version >= 1",
            name=op.f("ck_tool_auth_secrets_version_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["tool_id"],
            ["tools.id"],
            name=op.f("fk_tool_auth_secrets_tool_id_tools"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tool_auth_secrets")),
    )
    op.create_index(
        op.f("ix_tool_auth_secrets_deleted_at"),
        "tool_auth_secrets",
        ["deleted_at"],
    )
    op.create_index(
        op.f("ix_tool_auth_secrets_tool_id"),
        "tool_auth_secrets",
        ["tool_id"],
    )
    op.create_index(
        "ux_tool_auth_secrets_tool_id_active",
        "tool_auth_secrets",
        ["tool_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "tool_parameters",
        sa.Column("tool_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("param_location", sa.String(length=32), nullable=False),
        sa.Column("schema_type", sa.String(length=32), nullable=False),
        sa.Column(
            "is_required",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("default_value_json", sa.JSON(), nullable=True),
        sa.Column("enum_values_json", sa.JSON(), nullable=True),
        sa.Column("schema_json", sa.JSON(), nullable=True),
        sa.Column(
            "sort_order",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        *_audit_columns(),
        sa.CheckConstraint(
            "name <> ''",
            name=op.f("ck_tool_parameters_name_non_empty"),
        ),
        sa.CheckConstraint(
            "param_location IN ('path', 'query', 'header', 'body')",
            name=op.f("ck_tool_parameters_location_allowed"),
        ),
        sa.CheckConstraint(
            "schema_type IN ('string', 'number', 'integer', 'boolean', "
            "'object', 'array')",
            name=op.f("ck_tool_parameters_schema_type_allowed"),
        ),
        sa.CheckConstraint(
            "sort_order >= 0",
            name=op.f("ck_tool_parameters_sort_order_non_negative"),
        ),
        sa.CheckConstraint(
            "version >= 1",
            name=op.f("ck_tool_parameters_version_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["tool_id"],
            ["tools.id"],
            name=op.f("fk_tool_parameters_tool_id_tools"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tool_parameters")),
    )
    op.create_index(
        op.f("ix_tool_parameters_deleted_at"),
        "tool_parameters",
        ["deleted_at"],
    )
    op.create_index(
        op.f("ix_tool_parameters_param_location"),
        "tool_parameters",
        ["param_location"],
    )
    op.create_index(
        op.f("ix_tool_parameters_tool_id"),
        "tool_parameters",
        ["tool_id"],
    )
    op.create_index(
        "ux_tool_parameters_tool_id_name_location_active",
        "tool_parameters",
        ["tool_id", "name", "param_location"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "tool_execution_logs",
        sa.Column("tool_id", sa.BigInteger(), nullable=False),
        sa.Column("executor_user_id", sa.BigInteger(), nullable=True),
        sa.Column("conversation_id", sa.BigInteger(), nullable=True),
        sa.Column("run_id", sa.BigInteger(), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("request_method", sa.String(length=16), nullable=False),
        sa.Column("request_url", sa.String(length=2048), nullable=False),
        sa.Column("request_headers_json", sa.JSON(), nullable=True),
        sa.Column("request_body_preview", sa.Text(), nullable=True),
        sa.Column("response_status_code", sa.Integer(), nullable=True),
        sa.Column("response_headers_json", sa.JSON(), nullable=True),
        sa.Column("response_body_preview", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        *_audit_columns(),
        sa.CheckConstraint(
            "source IN ('test', 'conversation')",
            name=op.f("ck_tool_execution_logs_source_allowed"),
        ),
        sa.CheckConstraint(
            "status IN ('success', 'failed', 'timeout')",
            name=op.f("ck_tool_execution_logs_status_allowed"),
        ),
        sa.CheckConstraint(
            "request_method <> ''",
            name=op.f("ck_tool_execution_logs_method_non_empty"),
        ),
        sa.CheckConstraint(
            "request_url <> ''",
            name=op.f("ck_tool_execution_logs_url_non_empty"),
        ),
        sa.CheckConstraint(
            "response_status_code IS NULL OR "
            "(response_status_code >= 100 AND response_status_code <= 599)",
            name=op.f("ck_tool_execution_logs_response_status_range"),
        ),
        sa.CheckConstraint(
            "latency_ms >= 0",
            name=op.f("ck_tool_execution_logs_latency_non_negative"),
        ),
        sa.CheckConstraint(
            "version >= 1",
            name=op.f("ck_tool_execution_logs_version_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["executor_user_id"],
            ["users.id"],
            name=op.f("fk_tool_execution_logs_executor_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["tool_id"],
            ["tools.id"],
            name=op.f("fk_tool_execution_logs_tool_id_tools"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tool_execution_logs")),
    )
    op.create_index(
        op.f("ix_tool_execution_logs_conversation_id"),
        "tool_execution_logs",
        ["conversation_id"],
    )
    op.create_index(
        op.f("ix_tool_execution_logs_created_at"),
        "tool_execution_logs",
        ["created_at"],
    )
    op.create_index(
        op.f("ix_tool_execution_logs_executor_user_id"),
        "tool_execution_logs",
        ["executor_user_id"],
    )
    op.create_index(
        op.f("ix_tool_execution_logs_run_id"),
        "tool_execution_logs",
        ["run_id"],
    )
    op.create_index(
        op.f("ix_tool_execution_logs_source"),
        "tool_execution_logs",
        ["source"],
    )
    op.create_index(
        op.f("ix_tool_execution_logs_status"),
        "tool_execution_logs",
        ["status"],
    )
    op.create_index(
        op.f("ix_tool_execution_logs_tool_id"),
        "tool_execution_logs",
        ["tool_id"],
    )

    op.execute(
        """
        DELETE FROM agent_tool_bindings
        WHERE NOT EXISTS (
            SELECT 1 FROM tools WHERE tools.id = agent_tool_bindings.tool_id
        )
        """
    )
    op.create_foreign_key(
        op.f("fk_agent_tool_bindings_tool_id_tools"),
        "agent_tool_bindings",
        "tools",
        ["tool_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_agent_tool_bindings_tool_id_tools"),
        "agent_tool_bindings",
        type_="foreignkey",
    )
    op.drop_table("tool_execution_logs")
    op.drop_table("tool_parameters")
    op.drop_table("tool_auth_secrets")
    op.drop_table("tools")
