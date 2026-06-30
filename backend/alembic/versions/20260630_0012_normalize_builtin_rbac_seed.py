"""normalize builtin rbac seed

Revision ID: 20260630_0012
Revises: 20260630_0011
Create Date: 2026-06-30 12:10:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260630_0012"
down_revision: str | None = "20260630_0011"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE roles
        SET
            name = '管理员',
            description = '系统管理员，拥有全部平台权限',
            status = 'enabled',
            is_system = true
        WHERE code = 'admin'
          AND deleted_at IS NULL
        """
    )
    op.execute(
        """
        UPDATE roles
        SET
            name = '普通用户',
            description = '普通成员，默认只能使用对话能力',
            status = 'enabled',
            is_system = true
        WHERE code = 'member'
          AND deleted_at IS NULL
        """
    )
    op.execute(
        """
        UPDATE permissions
        SET is_system = true
        WHERE code IN (
            'provider.read',
            'provider.manage',
            'agent.read',
            'agent.manage',
            'tool.read',
            'tool.manage',
            'knowledge.read',
            'knowledge.manage',
            'conversation.use',
            'conversation.read',
            'conversation.manage',
            'user.read',
            'user.manage',
            'rbac.read',
            'rbac.manage'
        )
          AND deleted_at IS NULL
        """
    )


def downgrade() -> None:
    """Seed normalization is intentionally not reversed."""
