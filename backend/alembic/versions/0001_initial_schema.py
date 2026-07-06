"""Initial schema: muscles, exercises and their relation, plus pgvector.

Revision ID: 0001
Revises:
Create Date: 2026-07-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

from app.domain.value_objects.enums import Difficulty, Equipment, MuscleGroup, MuscleRole
from app.infrastructure.persistence.models.base import EMBEDDING_DIM

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # pgvector extension must exist before creating vector columns.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "muscles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column(
            "muscle_group",
            sa.Enum(MuscleGroup, native_enum=False, length=20),
            nullable=False,
        ),
        sa.Column("svg_id", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("svg_id"),
    )
    op.create_index("ix_muscles_svg_id", "muscles", ["svg_id"])

    op.create_table(
        "exercises",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "equipment",
            sa.Enum(Equipment, native_enum=False, length=20),
            nullable=False,
        ),
        sa.Column(
            "difficulty",
            sa.Enum(Difficulty, native_enum=False, length=20),
            nullable=False,
        ),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "exercise_muscles",
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("muscle_id", sa.Integer(), nullable=False),
        sa.Column(
            "role",
            sa.Enum(MuscleRole, native_enum=False, length=20),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["muscle_id"], ["muscles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("exercise_id", "muscle_id"),
    )


def downgrade() -> None:
    op.drop_table("exercise_muscles")
    op.drop_table("exercises")
    op.drop_index("ix_muscles_svg_id", table_name="muscles")
    op.drop_table("muscles")
