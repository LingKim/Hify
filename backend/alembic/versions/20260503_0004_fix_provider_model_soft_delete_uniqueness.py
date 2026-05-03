"""fix provider model uniqueness for soft delete

Revision ID: 20260503_0004
Revises: 20260503_0003
Create Date: 2026-05-03 14:05:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260503_0004"
down_revision: str | None = "20260503_0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_provider_models_provider_instance_id_model_name",
        "provider_models",
        type_="unique",
    )
    op.create_index(
        "ux_provider_models_provider_instance_id_model_name_active",
        "provider_models",
        ["provider_instance_id", "model_name"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "ux_provider_models_provider_instance_id_model_name_active",
        table_name="provider_models",
    )
    op.create_unique_constraint(
        "uq_provider_models_provider_instance_id_model_name",
        "provider_models",
        ["provider_instance_id", "model_name"],
    )
