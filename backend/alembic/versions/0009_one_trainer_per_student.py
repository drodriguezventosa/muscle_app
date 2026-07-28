"""One trainer per student, and what each trainer offers.

`trainer_students` was unique on the pair, which let a student collect coaches.
The rule is one trainer per student (and many students per trainer), so the
uniqueness moves to the student alone: hiring another trainer replaces the link.

`trainer_profiles` holds the offer shown on the trainer cards — specialty,
rating, price and a bio in both languages — which until now lived as hard-coded
data in the frontend.

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Keep the oldest link per student before the constraint can bite.
    op.execute(
        """
        DELETE FROM trainer_students
        WHERE id NOT IN (SELECT MIN(id) FROM trainer_students GROUP BY student_id)
        """
    )
    op.drop_constraint("uq_trainer_student", "trainer_students", type_="unique")
    op.create_unique_constraint("uq_trainer_student", "trainer_students", ["student_id"])

    op.create_table(
        "trainer_profiles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "specialty",
            sa.Enum("fat_loss", "hypertrophy", "strength", name="goal", native_enum=False),
            nullable=False,
        ),
        sa.Column("rating", sa.Float(), nullable=False),
        sa.Column("price_per_month", sa.Integer(), nullable=False),
        sa.Column("bio", sa.String(length=240), nullable=True),
        sa.Column("bio_en", sa.String(length=240), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("trainer_profiles")
    op.drop_constraint("uq_trainer_student", "trainer_students", type_="unique")
    op.create_unique_constraint(
        "uq_trainer_student", "trainer_students", ["trainer_id", "student_id"]
    )
