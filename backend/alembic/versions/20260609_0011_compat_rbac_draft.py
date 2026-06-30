"""compatibility marker for local RBAC draft migration

Revision ID: 20260609_0011
Revises: 20260523_0010
Create Date: 2026-06-09 00:00:00
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "20260609_0011"
down_revision: str | None = "20260523_0010"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Keep local databases that ran an early RBAC draft on the main chain."""


def downgrade() -> None:
    """No-op compatibility marker."""
