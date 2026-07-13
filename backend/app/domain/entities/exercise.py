"""Exercise domain entity and its relation to the muscles it works."""

from dataclasses import dataclass, field

from app.domain.value_objects.enums import Difficulty, Equipment, MuscleRole


@dataclass(frozen=True, slots=True)
class TargetedMuscle:
    """Links an exercise to a muscle, stating whether it is a primary mover."""

    muscle_id: int
    role: MuscleRole


@dataclass(frozen=True, slots=True)
class Exercise:
    """An exercise that trains one or more muscles.

    `targeted_muscles` captures which muscles the exercise works and how. `id`
    is None until the exercise is persisted.
    """

    name: str
    description: str
    equipment: Equipment
    difficulty: Difficulty
    targeted_muscles: tuple[TargetedMuscle, ...] = field(default_factory=tuple)
    # Demonstration video for the requested locale (YouTube URL), if available.
    video_url: str | None = None
    # Ordered how-to steps for the requested locale. Used as a fallback so every
    # exercise has an example even when no demonstration video exists.
    steps: tuple[str, ...] = field(default_factory=tuple)
    id: int | None = None

    def works_muscle(self, muscle_id: int) -> bool:
        """Return True if this exercise targets the given muscle (any role)."""
        return any(tm.muscle_id == muscle_id for tm in self.targeted_muscles)
