"""Repository ports (interfaces) the application layer depends on.

Concrete implementations live in `app.infrastructure`. The domain never knows
which database or ORM backs these.
"""

from abc import ABC, abstractmethod

from app.domain.entities.exercise import Exercise
from app.domain.entities.muscle import Muscle


class MuscleRepository(ABC):
    """Read access to the muscle catalog."""

    @abstractmethod
    async def list_all(self) -> list[Muscle]:
        """Return every muscle, ordered for stable display."""

    @abstractmethod
    async def get_by_id(self, muscle_id: int) -> Muscle | None:
        """Return the muscle with this id, or None if it does not exist."""

    @abstractmethod
    async def get_by_svg_id(self, svg_id: str) -> Muscle | None:
        """Return the muscle mapped to this SVG shape id, or None."""


class ExerciseRepository(ABC):
    """Read access to the exercise catalog."""

    @abstractmethod
    async def get_by_id(self, exercise_id: int) -> Exercise | None:
        """Return the exercise with this id, or None if it does not exist."""

    @abstractmethod
    async def list_for_muscle(self, muscle_id: int) -> list[Exercise]:
        """Return exercises that target the given muscle (primary or secondary)."""
