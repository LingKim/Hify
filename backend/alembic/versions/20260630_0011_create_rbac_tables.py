"""create rbac tables

Revision ID: 20260630_0011
Revises: 20260609_0011
Create Date: 2026-06-30 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260630_0011"
down_revision: str | None = "20260609_0011"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


ROLES = [
    ("admin", "管理员", "系统管理员，拥有全部平台权限"),
    ("member", "普通用户", "普通成员，默认只能使用对话能力"),
]

PERMISSIONS = [
    ("provider.read", "查看模型提供商", "provider", "read"),
    ("provider.manage", "管理模型提供商", "provider", "manage"),
    ("agent.read", "查看 Agent 配置", "agent", "read"),
    ("agent.manage", "管理 Agent 配置", "agent", "manage"),
    ("tool.read", "查看工具", "tool", "read"),
    ("tool.manage", "管理工具", "tool", "manage"),
    ("knowledge.read", "查看知识库", "knowledge", "read"),
    ("knowledge.manage", "管理知识库", "knowledge", "manage"),
    ("conversation.use", "使用 Web 对话", "conversation", "use"),
    ("conversation.read", "查看本人会话", "conversation", "read"),
    ("conversation.manage", "管理会话日志", "conversation", "manage"),
    ("user.read", "查看用户", "user", "read"),
    ("user.manage", "管理用户", "user", "manage"),
    ("rbac.read", "查看角色权限", "rbac", "read"),
    ("rbac.manage", "管理角色权限", "rbac", "manage"),
]


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
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "roles" in existing_tables:
        _ensure_existing_rbac_schema()
        _seed_roles()
        _seed_permissions()
        _seed_role_permissions()
        _migrate_user_roles()
        _drop_legacy_user_role()
        return

    op.create_table(
        "roles",
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default=sa.text("'enabled'"),
            nullable=False,
        ),
        sa.Column(
            "is_system",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        *_audit_columns(),
        sa.CheckConstraint("code <> ''", name=op.f("ck_roles_code_non_empty")),
        sa.CheckConstraint("name <> ''", name=op.f("ck_roles_name_non_empty")),
        sa.CheckConstraint(
            "status IN ('enabled', 'disabled')",
            name=op.f("ck_roles_status_allowed"),
        ),
        sa.CheckConstraint(
            "version >= 1",
            name=op.f("ck_roles_version_positive"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roles")),
    )
    op.create_index(op.f("ix_roles_deleted_at"), "roles", ["deleted_at"])
    op.create_index(op.f("ix_roles_is_system"), "roles", ["is_system"])
    op.create_index(op.f("ix_roles_status"), "roles", ["status"])
    op.create_index(
        "ux_roles_code_active",
        "roles",
        ["code"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "permissions",
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("module", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_system",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        *_audit_columns(),
        sa.CheckConstraint(
            "code <> ''",
            name=op.f("ck_permissions_code_non_empty"),
        ),
        sa.CheckConstraint(
            "name <> ''",
            name=op.f("ck_permissions_name_non_empty"),
        ),
        sa.CheckConstraint(
            "module <> ''",
            name=op.f("ck_permissions_module_non_empty"),
        ),
        sa.CheckConstraint(
            "action <> ''",
            name=op.f("ck_permissions_action_non_empty"),
        ),
        sa.CheckConstraint(
            "version >= 1",
            name=op.f("ck_permissions_version_positive"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_permissions")),
    )
    op.create_index(
        op.f("ix_permissions_action"),
        "permissions",
        ["action"],
    )
    op.create_index(
        op.f("ix_permissions_deleted_at"),
        "permissions",
        ["deleted_at"],
    )
    op.create_index(
        op.f("ix_permissions_is_system"),
        "permissions",
        ["is_system"],
    )
    op.create_index(
        op.f("ix_permissions_module"),
        "permissions",
        ["module"],
    )
    op.create_index(
        "ux_permissions_code_active",
        "permissions",
        ["code"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "user_role_bindings",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("role_id", sa.BigInteger(), nullable=False),
        *_audit_columns(),
        sa.CheckConstraint(
            "version >= 1",
            name=op.f("ck_user_role_bindings_version_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            name=op.f("fk_user_role_bindings_role_id_roles"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_role_bindings_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_role_bindings")),
    )
    op.create_index(
        op.f("ix_user_role_bindings_deleted_at"),
        "user_role_bindings",
        ["deleted_at"],
    )
    op.create_index(
        op.f("ix_user_role_bindings_role_id"),
        "user_role_bindings",
        ["role_id"],
    )
    op.create_index(
        op.f("ix_user_role_bindings_user_id"),
        "user_role_bindings",
        ["user_id"],
    )
    op.create_index(
        "ux_user_role_bindings_user_role_active",
        "user_role_bindings",
        ["user_id", "role_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "role_permission_bindings",
        sa.Column("role_id", sa.BigInteger(), nullable=False),
        sa.Column("permission_id", sa.BigInteger(), nullable=False),
        *_audit_columns(),
        sa.CheckConstraint(
            "version >= 1",
            name=op.f("ck_role_permission_bindings_version_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
            name=op.f("fk_role_permission_bindings_permission_id_permissions"),
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            name=op.f("fk_role_permission_bindings_role_id_roles"),
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_role_permission_bindings"),
        ),
    )
    op.create_index(
        op.f("ix_role_permission_bindings_deleted_at"),
        "role_permission_bindings",
        ["deleted_at"],
    )
    op.create_index(
        op.f("ix_role_permission_bindings_permission_id"),
        "role_permission_bindings",
        ["permission_id"],
    )
    op.create_index(
        op.f("ix_role_permission_bindings_role_id"),
        "role_permission_bindings",
        ["role_id"],
    )
    op.create_index(
        "ux_role_permission_bindings_role_permission_active",
        "role_permission_bindings",
        ["role_id", "permission_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    _seed_roles()
    _seed_permissions()
    _seed_role_permissions()
    _migrate_user_roles()
    _drop_legacy_user_role()


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=32),
            server_default=sa.text("'member'"),
            nullable=False,
        ),
    )
    op.execute(
        """
        UPDATE users
        SET role = 'admin'
        WHERE EXISTS (
            SELECT 1
            FROM user_role_bindings urb
            JOIN roles r ON r.id = urb.role_id
            WHERE urb.user_id = users.id
              AND urb.deleted_at IS NULL
              AND r.deleted_at IS NULL
              AND r.code = 'admin'
        )
        """
    )
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)
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

    op.drop_table("role_permission_bindings")
    op.drop_table("user_role_bindings")
    op.drop_table("permissions")
    op.drop_table("roles")


def _seed_roles() -> None:
    connection = op.get_bind()
    for code, name, description in ROLES:
        connection.execute(
            sa.text(
                """
                INSERT INTO roles (code, name, description, status, is_system)
                SELECT
                    CAST(:code AS varchar),
                    CAST(:name AS varchar),
                    CAST(:description AS text),
                    'enabled',
                    true
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM roles
                    WHERE code = CAST(:code AS varchar)
                      AND deleted_at IS NULL
                )
                """
            ),
            {
                "code": code,
                "name": name,
                "description": description,
            },
        )


def _ensure_existing_rbac_schema() -> None:
    if not _column_exists("roles", "status"):
        op.add_column(
            "roles",
            sa.Column(
                "status",
                sa.String(length=32),
                server_default=sa.text("'enabled'"),
                nullable=False,
            ),
        )
    if not _column_exists("permissions", "is_system"):
        op.add_column(
            "permissions",
            sa.Column(
                "is_system",
                sa.Boolean(),
                server_default=sa.text("true"),
                nullable=False,
            ),
        )


def _seed_permissions() -> None:
    connection = op.get_bind()
    for code, name, module, action in PERMISSIONS:
        connection.execute(
            sa.text(
                """
                INSERT INTO permissions (
                    code,
                    name,
                    module,
                    action,
                    description,
                    is_system
                )
                SELECT
                    CAST(:code AS varchar),
                    CAST(:name AS varchar),
                    CAST(:module AS varchar),
                    CAST(:action AS varchar),
                    CAST(:name AS text),
                    true
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM permissions
                    WHERE code = CAST(:code AS varchar)
                      AND deleted_at IS NULL
                )
                """
            ),
            {
                "code": code,
                "name": name,
                "module": module,
                "action": action,
            },
        )


def _seed_role_permissions() -> None:
    op.execute(
        """
        INSERT INTO role_permission_bindings (role_id, permission_id)
        SELECT roles.id, permissions.id
        FROM roles
        CROSS JOIN permissions
        WHERE roles.code = 'admin'
          AND roles.deleted_at IS NULL
          AND permissions.deleted_at IS NULL
          AND NOT EXISTS (
              SELECT 1
              FROM role_permission_bindings rpb
              WHERE rpb.role_id = roles.id
                AND rpb.permission_id = permissions.id
                AND rpb.deleted_at IS NULL
          )
        """
    )
    op.execute(
        """
        INSERT INTO role_permission_bindings (role_id, permission_id)
        SELECT roles.id, permissions.id
        FROM roles
        JOIN permissions
          ON permissions.code IN ('conversation.use', 'conversation.read')
        WHERE roles.code = 'member'
          AND roles.deleted_at IS NULL
          AND permissions.deleted_at IS NULL
          AND NOT EXISTS (
              SELECT 1
              FROM role_permission_bindings rpb
              WHERE rpb.role_id = roles.id
                AND rpb.permission_id = permissions.id
                AND rpb.deleted_at IS NULL
          )
        """
    )


def _migrate_user_roles() -> None:
    if not _column_exists("users", "role"):
        return
    op.execute(
        """
        INSERT INTO user_role_bindings (user_id, role_id)
        SELECT users.id, roles.id
        FROM users
        JOIN roles ON roles.code = 'admin'
        WHERE users.role = 'admin'
          AND roles.deleted_at IS NULL
          AND NOT EXISTS (
              SELECT 1
              FROM user_role_bindings urb
              WHERE urb.user_id = users.id
                AND urb.role_id = roles.id
                AND urb.deleted_at IS NULL
          )
        """
    )
    op.execute(
        """
        INSERT INTO user_role_bindings (user_id, role_id)
        SELECT users.id, roles.id
        FROM users
        JOIN roles ON roles.code = 'member'
        WHERE users.role <> 'admin'
          AND roles.deleted_at IS NULL
          AND NOT EXISTS (
              SELECT 1
              FROM user_role_bindings urb
              WHERE urb.user_id = users.id
                AND urb.role_id = roles.id
                AND urb.deleted_at IS NULL
          )
        """
    )


def _drop_legacy_user_role() -> None:
    if not _column_exists("users", "role"):
        return
    if _check_constraint_exists("users", op.f("ck_users_role_supported")):
        op.drop_constraint(
            op.f("ck_users_role_supported"),
            "users",
            type_="check",
        )
    if _check_constraint_exists("users", op.f("ck_users_role_non_empty")):
        op.drop_constraint(
            op.f("ck_users_role_non_empty"),
            "users",
            type_="check",
        )
    if _index_exists("users", op.f("ix_users_role")):
        op.drop_index(op.f("ix_users_role"), table_name="users")
    op.drop_column("users", "role")


def _column_exists(table_name: str, column_name: str) -> bool:
    columns = sa.inspect(op.get_bind()).get_columns(table_name)
    return any(column["name"] == column_name for column in columns)


def _index_exists(table_name: str, index_name: str) -> bool:
    indexes = sa.inspect(op.get_bind()).get_indexes(table_name)
    return any(index["name"] == index_name for index in indexes)


def _check_constraint_exists(table_name: str, constraint_name: str) -> bool:
    constraints = sa.inspect(op.get_bind()).get_check_constraints(table_name)
    return any(
        constraint["name"] == constraint_name for constraint in constraints
    )
