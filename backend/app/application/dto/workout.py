"""DTOs for the workout generator (input attributes and computed result)."""

from dataclasses import dataclass

from app.domain.entities.workout import WorkoutTemplate
from app.domain.value_objects.enums import Difficulty, Equipment, Goal


@dataclass(frozen=True, slots=True)
class WorkoutRequest:
    """Minimal user attributes used to build a basic routine.

    `experience` maps to the difficulty of exercises the user is offered; height
    and weight feed the BMI shown as context. No data is persisted (no login).
    """

    goal: Goal
    experience: Difficulty
    height_cm: float
    weight_kg: float
    sex: str | None = None
    age: int | None = None
    equipment: list[Equipment] | None = None


@dataclass(frozen=True, slots=True)
class GeneratedWorkout:
    """A generated routine plus the BMI context computed from the attributes."""

    template: WorkoutTemplate
    bmi: float
    bmi_category: str
