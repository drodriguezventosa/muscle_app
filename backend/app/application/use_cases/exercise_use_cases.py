"""Query use cases for exercises (public, read-only)."""

from app.domain.entities.exercise import Exercise
from app.domain.ports.repositories import ExerciseRepository


class GetExercise:
    """Return a single exercise by id, or None if it does not exist."""

    def __init__(self, exercises: ExerciseRepository) -> None:
        self._exercises = exercises

    async def execute(self, exercise_id: int) -> Exercise | None:
        return await self._exercises.get_by_id(exercise_id)
