"""Coaching entities: what a trainer sees about the students they follow.

Pure data plus the small calculations that belong to the concepts themselves
(estimated 1RM, BMI). Aggregation into chart series happens in the use cases.
"""

from dataclasses import dataclass
from datetime import date

from app.domain.value_objects.enums import Difficulty, Goal


@dataclass(frozen=True)
class BodyMetric:
    """One body-weight measurement on a given day."""

    measured_on: date
    weight_kg: float


@dataclass(frozen=True)
class WorkoutLog:
    """One logged set of an exercise: what was lifted, and whether it was completed."""

    logged_on: date
    exercise_id: int
    exercise_name: str
    weight_kg: float
    reps: int
    completed: bool

    @property
    def estimated_1rm(self) -> float:
        """One-rep max estimated with the Epley formula: `w * (1 + reps/30)`.

        Chosen because it only needs the weight and the repetitions, which is
        exactly what the workout logger records. Bodyweight work (0 kg) has no
        meaningful 1RM, so it reports 0.
        """
        if self.weight_kg <= 0 or self.reps <= 0:
            return 0.0
        return round(self.weight_kg * (1 + self.reps / 30), 1)


@dataclass(frozen=True)
class Student:
    """A person a trainer follows, with the headline numbers for the roster."""

    id: int
    name: str
    goal: Goal | None
    level: Difficulty | None
    age: int | None
    height_cm: int | None
    weight_kg: float | None
    sessions_last_30d: int
    last_session_on: date | None

    @property
    def bmi(self) -> float | None:
        """Body mass index, or None when height or weight is unknown."""
        if not self.height_cm or not self.weight_kg:
            return None
        metres = self.height_cm / 100
        return round(self.weight_kg / (metres * metres), 1)


@dataclass(frozen=True)
class StudentDetail:
    """A student plus the full history the dashboard charts."""

    student: Student
    body_metrics: tuple[BodyMetric, ...]
    logs: tuple[WorkoutLog, ...]


@dataclass(frozen=True)
class LoggedSession:
    """A session the student reports from the workout logger."""

    exercise_id: int
    logged_on: date
    weight_kg: float
    reps: int
    completed: bool
    #: Sets actually performed. None when the logger did not ask for them (the
    #: free workout page tracks the weight only).
    sets: int | None = None
