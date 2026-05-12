"""extend users for management

Revision ID: 20260512_0007
Revises: 20260505_0006
Create Date: 2026-05-12 14:10:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260512_0007"
down_revision: str | None = "20260505_0006"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        "UPDATE users SET role = 'member' "
        "WHERE role IS NULL OR role = ''"
    )
    op.execute(
        "UPDATE users SET is_active = true WHERE is_active IS NULL"
    )

    op.drop_constraint("uq_users_username", "users", type_="unique")
    op.drop_constraint("uq_users_email", "users", type_="unique")

    op.create_index(
        "ux_users_username_active",
        "users",
        ["username"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ux_users_email_active",
        "users",
        ["email"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)
    op.create_index(
        op.f("ix_users_is_active"),
        "users",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        op.f("ix_users_last_login_at"),
        "users",
        ["last_login_at"],
        unique=False,
    )

    op.create_check_constraint(
        op.f("ck_users_email_non_empty"),
        "users",
        "email <> ''",
    )
    op.create_check_constraint(
        op.f("ck_users_password_hash_non_empty"),
        "users",
        "password_hash <> ''",
    )
    op.create_check_constraint(
        op.f("ck_users_role_non_empty"),
        "users",
        "role <> ''",
    )
    op.create_check_constraint(
        op.f("ck_users_role_supported"),
        "users",
        "role IN ('admin', 'member')",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_users_role_supported"), "users", type_="check")
    op.drop_constraint(op.f("ck_users_role_non_empty"), "users", type_="check")
    op.drop_constraint(
        op.f("ck_users_password_hash_non_empty"),
        "users",
        type_="check",
    )
    op.drop_constraint(op.f("ck_users_email_non_empty"), "users", type_="check")

    op.drop_index(op.f("ix_users_last_login_at"), table_name="users")
    op.drop_index(op.f("ix_users_is_active"), table_name="users")
    op.drop_index(op.f("ix_users_role"), table_name="users")
    op.drop_index("ux_users_email_active", table_name="users")
    op.drop_index("ux_users_username_active", table_name="users")

    op.create_unique_constraint(
        op.f("uq_users_email"),
        "users",
        ["email"],
    )
    op.create_unique_constraint(
        op.f("uq_users_username"),
        "users",
        ["username"],
    )
    op.drop_column("users", "last_login_at")
