"""Add the coaching tables: rosters, student profiles and training history.

These turn the trainers area from a mockup into real data: who follows whom,
what each student's attributes are, the sessions they log and their body-weight
measurements. The dashboard charts read from here.

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "student_profiles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        # A birth year instead of an age, so the row does not go stale.
        sa.Column("birth_year", sa.Integer(), nullable=True),
        sa.Column("height_cm", sa.Integer(), nullable=True),
        sa.Column(
            "goal",
            sa.Enum("fat_loss", "hypertrophy", "strength", name="goal", native_enum=False),
            nullable=True,
        ),
        sa.Column(
            "level",
            sa.Enum("beginner", "intermediate", "advanced", name="difficulty", native_enum=False),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "trainer_students",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trainer_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["trainer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trainer_id", "student_id", name="uq_trainer_student"),
    )
    op.create_index(
        op.f("ix_trainer_students_trainer_id"), "trainer_students", ["trainer_id"], unique=False
    )
    op.create_index(
        op.f("ix_trainer_students_student_id"), "trainer_students", ["student_id"], unique=False
    )

    op.create_table(
        "workout_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("logged_on", sa.Date(), nullable=False),
        # 0 kg is valid: it is how bodyweight work is recorded.
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("reps", sa.Integer(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        # Re-syncing the same browser history updates rows instead of duplicating.
        sa.UniqueConstraint("user_id", "exercise_id", "logged_on", name="uq_workout_log_day"),
    )
    op.create_index(
        "ix_workout_logs_user_date", "workout_logs", ["user_id", "logged_on"], unique=False
    )

    op.create_table(
        "body_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("measured_on", sa.Date(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "measured_on", name="uq_body_metric_day"),
    )
    op.create_index(op.f("ix_body_metrics_user_id"), "body_metrics", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_body_metrics_user_id"), table_name="body_metrics")
    op.drop_table("body_metrics")
    op.drop_index("ix_workout_logs_user_date", table_name="workout_logs")
    op.drop_table("workout_logs")
    op.drop_index(op.f("ix_trainer_students_student_id"), table_name="trainer_students")
    op.drop_index(op.f("ix_trainer_students_trainer_id"), table_name="trainer_students")
    op.drop_table("trainer_students")
    op.drop_table("student_profiles")
