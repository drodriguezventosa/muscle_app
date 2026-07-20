"""Repository ports (interfaces) the application layer depends on.

Concrete implementations live in `app.infrastructure`. The domain never knows
which database or ORM backs these.
"""

from abc import ABC, abstractmethod

from app.domain.entities.exercise import Exercise
from app.domain.entities.food import Food
from app.domain.entities.muscle import Muscle
from app.domain.value_objects.enums import Difficulty, Equipment


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

    @abstractmethod
    async def list_with_matching_exercises(
        self,
        equipment: list[Equipment] | None = None,
        difficulty: list[Difficulty] | None = None,
    ) -> list[Muscle]:
        """Return muscles that have at least one exercise matching the filters.

        With no filters, returns every muscle that has any exercise. Used to
        light up only the relevant regions on the body map.
        """


class ExerciseRepository(ABC):
    """Read access to the exercise catalog."""

    @abstractmethod
    async def get_by_id(self, exercise_id: int) -> Exercise | None:
        """Return the exercise with this id, or None if it does not exist."""

    @abstractmethod
    async def list_for_muscle(
        self,
        muscle_id: int,
        equipment: list[Equipment] | None = None,
        difficulty: list[Difficulty] | None = None,
    ) -> list[Exercise]:
        """Return exercises that target the given muscle (primary or secondary).

        Optional equipment/difficulty filters narrow the result; an empty or
        None filter means "no restriction".
        """

    @abstractmethod
    async def search_similar(
        self,
        embedding: list[float],
        limit: int,
        equipment: Equipment | None = None,
        difficulty: Difficulty | None = None,
    ) -> list[Exercise]:
        """Return exercises most similar to the query embedding.

        Exercises without an embedding are excluded. Optional structured filters
        (equipment, difficulty) narrow the search before ranking by similarity.
        """


class FoodRepository(ABC):
    """Read access to the nutrition food catalog."""

    @abstractmethod
    async def list_all(self) -> list[Food]:
        """Return the whole food catalog, ordered by name."""

    @abstractmethod
    async def search_similar(self, embedding: list[float], limit: int) -> list[Food]:
        """Return foods most similar to the query embedding (RAG meal ideas).

        Foods without an embedding are excluded.
        """
