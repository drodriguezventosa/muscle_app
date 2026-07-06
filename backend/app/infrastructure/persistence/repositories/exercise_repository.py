"""SQLAlchemy implementation of the ExerciseRepository port."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.exercise import Exercise, TargetedMuscle
from app.domain.ports.repositories import ExerciseRepository
from app.infrastructure.persistence.models.exercise import ExerciseModel, ExerciseMuscleModel


def _to_entity(model: ExerciseModel) -> Exercise:
    return Exercise(
        id=model.id,
        name=model.name,
        description=model.description,
        equipment=model.equipment,
        difficulty=model.difficulty,
        targeted_muscles=tuple(
            TargetedMuscle(muscle_id=link.muscle_id, role=link.role) for link in model.muscles
        ),
    )


class SqlAlchemyExerciseRepository(ExerciseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, exercise_id: int) -> Exercise | None:
        model = await self._session.get(ExerciseModel, exercise_id)
        return _to_entity(model) if model else None

    async def list_for_muscle(self, muscle_id: int) -> list[Exercise]:
        stmt = (
            select(ExerciseModel)
            .join(ExerciseMuscleModel, ExerciseMuscleModel.exercise_id == ExerciseModel.id)
            .where(ExerciseMuscleModel.muscle_id == muscle_id)
            .order_by(ExerciseModel.name)
        )
        result = await self._session.scalars(stmt)
        return [_to_entity(m) for m in result.unique()]
