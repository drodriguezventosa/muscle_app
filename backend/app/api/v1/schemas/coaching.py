"""Request/response models for the coaching area."""

from datetime import date, timedelta

from pydantic import BaseModel, Field, field_validator

from app.domain.value_objects.enums import Difficulty, Goal

# Bounded so a crafted payload cannot turn a sync into a bulk write (OWASP A04).
MAX_SESSIONS_PER_SYNC = 500
# Anything older is not history the app could have produced.
MAX_LOG_AGE_DAYS = 366 * 3


class StudentRead(BaseModel):
    """A student as shown on the trainer's roster."""

    id: int
    name: str
    goal: Goal | None
    level: Difficulty | None
    age: int | None
    height_cm: int | None
    weight_kg: float | None
    bmi: float | None
    sessions_last_30d: int
    last_session_on: date | None


class TrainerRead(BaseModel):
    """A trainer as shown on the cards a student picks from."""

    id: int
    name: str
    specialty: Goal
    rating: float
    price_per_month: int
    bio: str | None
    students: int


class HireTrainerRequest(BaseModel):
    """Which trainer the student takes on. At most one at a time."""

    trainer_id: int = Field(gt=0)


class SeriesPointRead(BaseModel):
    """One point of a chart series."""

    on: date
    value: float


class ExerciseProgressionRead(BaseModel):
    """Estimated 1RM over time for one exercise."""

    exercise_id: int
    exercise_name: str
    points: list[SeriesPointRead]
    gain_pct: float


class WeeklyAdherenceRead(BaseModel):
    """Sessions trained in the week starting on `week_start`."""

    week_start: date
    sessions: int


class StudentDashboardRead(BaseModel):
    """Everything the evolution charts need about one student."""

    student: StudentRead
    body_weight: list[SeriesPointRead]
    strength: list[ExerciseProgressionRead]
    adherence: list[WeeklyAdherenceRead]
    total_sessions: int
    weight_change_kg: float | None


class LoggedSessionWrite(BaseModel):
    """One session the browser recorded, as sent back to the server."""

    exercise_id: int = Field(gt=0)
    logged_on: date
    # 0 kg is valid: that is how bodyweight work is logged.
    weight_kg: float = Field(ge=0, le=500)
    reps: int = Field(ge=0, le=100)
    #: Optional: the free workout logger records the weight, not the set count.
    sets: int | None = Field(default=None, ge=0, le=20)
    completed: bool = True

    @field_validator("logged_on")
    @classmethod
    def _reject_implausible_dates(cls, value: date) -> date:
        # One day of slack: a client in a timezone ahead of the server is
        # already on tomorrow's date, and that is not a suspicious payload.
        today = date.today() + timedelta(days=1)
        if value > today:
            raise ValueError("logged_on cannot be in the future")
        if (today - value).days > MAX_LOG_AGE_DAYS:
            raise ValueError("logged_on is too old")
        return value


class SyncProgressRequest(BaseModel):
    """A student pushing their local progress and attributes.

    Every field is optional because the app gathers them on different screens;
    what is not sent is left untouched.
    """

    sessions: list[LoggedSessionWrite] = Field(
        default_factory=list, max_length=MAX_SESSIONS_PER_SYNC
    )
    weight_kg: float | None = Field(default=None, gt=20, lt=400)
    height_cm: int | None = Field(default=None, gt=100, lt=260)
    age: int | None = Field(default=None, gt=12, lt=110)
    goal: Goal | None = None
    level: Difficulty | None = None


class SyncProgressResponse(BaseModel):
    """How many sessions were stored."""

    synced: int
