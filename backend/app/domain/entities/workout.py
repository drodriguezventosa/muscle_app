"""Workout template domain entities (public, read-only routines by goal)."""

from dataclasses import dataclass, field

from app.domain.entities.exercise import Exercise
from app.domain.value_objects.enums import Difficulty, Goal


@dataclass(frozen=True, slots=True)
class WorkoutItem:
    """One exercise within a workout, with its prescription.

    `reps` is free text ("8-12", "5", "30s") so it can express ranges and
    time-based holds. `exercise` embeds the full catalog entry so the UI can show
    its name, video and steps without extra lookups.
    """

    exercise: Exercise
    sets: int
    reps: str
    rest_seconds: int


@dataclass(frozen=True, slots=True)
class WorkoutTemplate:
    """A ready-made routine targeting a training goal. `id` is None until saved."""

    goal: Goal
    name: str
    description: str
    difficulty: Difficulty
    items: tuple[WorkoutItem, ...] = field(default_factory=tuple)
    id: int | None = None
