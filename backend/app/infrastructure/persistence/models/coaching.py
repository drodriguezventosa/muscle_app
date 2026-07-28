"""ORM models for the coaching area: rosters, student profiles and history."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.value_objects.enums import Difficulty, Goal
from app.infrastructure.persistence.models.base import Base


class StudentProfileModel(Base):
    """Training attributes of a client, kept apart from their identity row.

    Everything is nullable: the app collects these bit by bit (the workout
    generator asks for height and age, the nutrition calculator for weight).
    """

    __tablename__ = "student_profiles"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    # Stored as a birth year rather than an age, so the row does not silently
    # become wrong as time passes.
    birth_year: Mapped[int | None] = mapped_column(nullable=True)
    height_cm: Mapped[int | None] = mapped_column(nullable=True)
    goal: Mapped[Goal | None] = mapped_column(
        SAEnum(Goal, native_enum=False, length=20), nullable=True
    )
    level: Mapped[Difficulty | None] = mapped_column(
        SAEnum(Difficulty, native_enum=False, length=20), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TrainerStudentModel(Base):
    """Which students a trainer follows. The roster drives every access check."""

    __tablename__ = "trainer_students"
    __table_args__ = (UniqueConstraint("trainer_id", "student_id", name="uq_trainer_student"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    trainer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WorkoutLogModel(Base):
    """One exercise performed on one day: the raw material of the charts."""

    __tablename__ = "workout_logs"
    __table_args__ = (
        # One entry per exercise and day, so re-syncing the same browser history
        # updates rows instead of duplicating them.
        UniqueConstraint("user_id", "exercise_id", "logged_on", name="uq_workout_log_day"),
        Index("ix_workout_logs_user_date", "user_id", "logged_on"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id", ondelete="CASCADE"))
    logged_on: Mapped[date] = mapped_column(Date)
    # 0 for bodyweight work, which is why this is not constrained to be positive.
    weight_kg: Mapped[float] = mapped_column(Float, default=0.0)
    reps: Mapped[int] = mapped_column(default=0)
    completed: Mapped[bool] = mapped_column(default=True)


class BodyMetricModel(Base):
    """A body-weight measurement, one per day at most."""

    __tablename__ = "body_metrics"
    __table_args__ = (UniqueConstraint("user_id", "measured_on", name="uq_body_metric_day"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    measured_on: Mapped[date] = mapped_column(Date)
    weight_kg: Mapped[float] = mapped_column(Float)
