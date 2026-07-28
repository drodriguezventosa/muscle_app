"""ORM model for the training plan (what a trainer schedules for a student)."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import Base


class PlanItemModel(Base):
    """One exercise scheduled for one day.

    Only the prescription lives here. Whether it was done is read from
    `workout_logs` for the same user, exercise and day, so "what was lifted" is
    stored once and the dashboard sees assigned work like any other session.
    """

    __tablename__ = "plan_items"
    __table_args__ = (
        # Re-scheduling the same exercise that day edits the targets.
        UniqueConstraint("student_id", "exercise_id", "scheduled_on", name="uq_plan_item_day"),
        Index("ix_plan_items_student_date", "student_id", "scheduled_on"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    trainer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id", ondelete="CASCADE"))
    scheduled_on: Mapped[date] = mapped_column(Date)
    target_sets: Mapped[int] = mapped_column(default=3)
    target_reps: Mapped[int] = mapped_column(default=10)
    # Null means the trainer left the load open (bodyweight, or "as it comes").
    target_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
