"""Record how many sets were performed, not just the weight and the reps.

Nullable: the free workout logger only asks for the weight, and the rows
written before the training calendar existed have no set count either.

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("workout_logs", sa.Column("sets", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("workout_logs", "sets")
