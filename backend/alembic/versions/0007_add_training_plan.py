"""Add the training plan: exercises a trainer schedules for a student.

Only the prescription is stored. Whether it was done is read from
`workout_logs` for the same user, exercise and day, so what was lifted lives in
one place and assigned work feeds the dashboard like any other session.

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "plan_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trainer_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("scheduled_on", sa.Date(), nullable=False),
        sa.Column("target_sets", sa.Integer(), nullable=False),
        sa.Column("target_reps", sa.Integer(), nullable=False),
        # Null means the trainer left the load open (bodyweight, or "as it comes").
        sa.Column("target_weight_kg", sa.Float(), nullable=True),
        sa.Column("notes", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["trainer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        # Re-scheduling the same exercise that day edits the targets.
        sa.UniqueConstraint("student_id", "exercise_id", "scheduled_on", name="uq_plan_item_day"),
    )
    op.create_index(
        "ix_plan_items_student_date", "plan_items", ["student_id", "scheduled_on"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_plan_items_student_date", table_name="plan_items")
    op.drop_table("plan_items")
