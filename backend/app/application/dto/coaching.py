"""DTOs for the coaching area (progress input and the computed dashboard)."""

from dataclasses import dataclass
from datetime import date

from app.domain.entities.coaching import LoggedSession, Student
from app.domain.value_objects.enums import Difficulty, Goal


@dataclass(frozen=True, slots=True)
class ProgressUpdate:
    """What a student pushes: sessions, body weight and training attributes.

    Every field is optional because the app collects them on different screens
    (the workout logger, the nutrition calculator), and a partial update must
    never wipe what is already stored.
    """

    sessions: tuple[LoggedSession, ...] = ()
    weight_kg: float | None = None
    height_cm: int | None = None
    age: int | None = None
    goal: Goal | None = None
    level: Difficulty | None = None

    @property
    def has_profile_data(self) -> bool:
        return any((self.height_cm, self.age, self.goal, self.level))


@dataclass(frozen=True, slots=True)
class SeriesPoint:
    """One (day, value) pair of a chart series."""

    on: date
    value: float


@dataclass(frozen=True, slots=True)
class ExerciseProgression:
    """How one exercise evolved, in estimated 1RM."""

    exercise_id: int
    exercise_name: str
    points: tuple[SeriesPoint, ...]

    @property
    def gain_pct(self) -> float:
        """Percentage gained between the first and the last point."""
        if len(self.points) < 2 or self.points[0].value <= 0:
            return 0.0
        first, last = self.points[0].value, self.points[-1].value
        return round((last - first) / first * 100, 1)


@dataclass(frozen=True, slots=True)
class WeeklyAdherence:
    """Sessions trained in the week starting on `week_start` (a Monday)."""

    week_start: date
    sessions: int


@dataclass(frozen=True, slots=True)
class StudentDashboard:
    """Everything the trainer's charts need about one student."""

    student: Student
    body_weight: tuple[SeriesPoint, ...]
    strength: tuple[ExerciseProgression, ...]
    adherence: tuple[WeeklyAdherence, ...]
    total_sessions: int

    @property
    def weight_change_kg(self) -> float | None:
        """Kilos gained (+) or lost (-) across the recorded measurements."""
        if len(self.body_weight) < 2:
            return None
        return round(self.body_weight[-1].value - self.body_weight[0].value, 1)
