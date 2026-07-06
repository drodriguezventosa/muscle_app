"""Add demonstration video URLs (ES + EN) to exercises.

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("exercises", sa.Column("video_url", sa.String(length=255), nullable=True))
    op.add_column("exercises", sa.Column("video_url_en", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("exercises", "video_url_en")
    op.drop_column("exercises", "video_url")
