"""Add the users table for the coaching area sign-in.

Clients and trainers share one table and are told apart by `role`. There is no
public sign-up: the only rows are the demo accounts created by the seed.

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        # Stored lower-cased, so a plain unique index gives case-insensitive lookups.
        sa.Column("email", sa.String(length=180), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        # Argon2 encodes algorithm, parameters and salt inside the string.
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
