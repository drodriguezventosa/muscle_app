"""Query use cases for the muscle explorer (public, read-only)."""

from app.domain.entities.exercise import Exercise
from app.domain.entities.muscle import Muscle
from app.domain.ports.repositories import ExerciseRepository, MuscleRepository


class ListMuscles:
    """Return every muscle for the interactive body map."""

    def __init__(self, muscles: MuscleRepository) -> None:
        self._muscles = muscles

    async def execute(self) -> list[Muscle]:
        return await self._muscles.list_all()


class GetMuscle:
    """Return a single muscle by its SVG id, or None if it does not exist."""

    def __init__(self, muscles: MuscleRepository) -> None:
        self._muscles = muscles

    async def execute(self, svg_id: str) -> Muscle | None:
        return await self._muscles.get_by_svg_id(svg_id)


class ListMuscleExercises:
    """Return the exercises that train the muscle identified by its SVG id.

    Returns None when the muscle does not exist so the API can answer 404,
    distinguishing "unknown muscle" from "muscle with no exercises" (empty list).
    """

    def __init__(self, muscles: MuscleRepository, exercises: ExerciseRepository) -> None:
        self._muscles = muscles
        self._exercises = exercises

    async def execute(self, svg_id: str) -> list[Exercise] | None:
        muscle = await self._muscles.get_by_svg_id(svg_id)
        if muscle is None or muscle.id is None:
            return None
        return await self._exercises.list_for_muscle(muscle.id)
