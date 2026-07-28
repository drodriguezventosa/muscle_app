"""Request/response models for the training calendar."""

from datetime import date, timedelta

from pydantic import BaseModel, Field, field_validator

from app.domain.entities.plan import PlanItemStatus

# A plan is written days or weeks ahead, not years.
MAX_SCHEDULE_AHEAD_DAYS = 366


class PlanItemRead(BaseModel):
    """A scheduled exercise, with the target and whatever was logged."""

    id: int
    exercise_id: int
    exercise_name: str
    scheduled_on: date
    target_sets: int
    target_reps: int
    target_weight_kg: float | None
    notes: str | None
    done_weight_kg: float | None
    done_reps: int | None
    done_sets: int | None
    status: PlanItemStatus


class ScheduleExerciseRequest(BaseModel):
    """What the trainer prescribes for one day."""

    exercise_id: int = Field(gt=0)
    scheduled_on: date
    target_sets: int = Field(default=3, ge=1, le=20)
    target_reps: int = Field(default=10, ge=1, le=100)
    # None leaves the load open (bodyweight, or the student's own choice).
    target_weight_kg: float | None = Field(default=None, ge=0, le=500)
    notes: str | None = Field(default=None, max_length=200)

    @field_validator("scheduled_on")
    @classmethod
    def _reject_far_dates(cls, value: date) -> date:
        today = date.today()
        if value > today + timedelta(days=MAX_SCHEDULE_AHEAD_DAYS):
            raise ValueError("scheduled_on is too far ahead")
        if value < today - timedelta(days=MAX_SCHEDULE_AHEAD_DAYS):
            raise ValueError("scheduled_on is too far back")
        return value


class ReportPlanItemRequest(BaseModel):
    """What the student actually did: the load, the reps and the sets.

    Any of the three may be under the target — that is the point. Whether the
    plan was met is derived from them server-side.
    """

    weight_kg: float = Field(ge=0, le=500)
    reps: int = Field(ge=0, le=100)
    sets: int = Field(ge=0, le=20)
