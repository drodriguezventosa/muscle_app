"""Add how-to steps (ES + EN) to exercises.

Steps are shown as a fallback so every exercise has an example even when no
demonstration video exists.

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("exercises", sa.Column("steps", sa.JSON(), nullable=True))
    op.add_column("exercises", sa.Column("steps_en", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("exercises", "steps_en")
    op.drop_column("exercises", "steps")
