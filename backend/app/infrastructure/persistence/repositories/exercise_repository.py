"""SQLAlchemy implementation of the ExerciseRepository port."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.exercise import Exercise, TargetedMuscle
from app.domain.ports.repositories import ExerciseRepository
from app.domain.value_objects.enums import Difficulty, Equipment
from app.infrastructure.persistence.models.exercise import ExerciseModel, ExerciseMuscleModel
from app.infrastructure.persistence.repositories.localize import pick


class SqlAlchemyExerciseRepository(ExerciseRepository):
    def __init__(self, session: AsyncSession, locale: str = "es") -> None:
        self._session = session
        self._locale = locale

    def _to_entity(self, model: ExerciseModel) -> Exercise:
        return Exercise(
            id=model.id,
            name=pick(model.name, model.name_en, self._locale),
            description=pick(model.description, model.description_en, self._locale),
            equipment=model.equipment,
            difficulty=model.difficulty,
            targeted_muscles=tuple(
                TargetedMuscle(muscle_id=link.muscle_id, role=link.role) for link in model.muscles
            ),
        )

    async def get_by_id(self, exercise_id: int) -> Exercise | None:
        model = await self._session.get(ExerciseModel, exercise_id)
        return self._to_entity(model) if model else None

    async def list_for_muscle(self, muscle_id: int) -> list[Exercise]:
        stmt = (
            select(ExerciseModel)
            .join(ExerciseMuscleModel, ExerciseMuscleModel.exercise_id == ExerciseModel.id)
            .where(ExerciseMuscleModel.muscle_id == muscle_id)
            .order_by(ExerciseModel.name)
        )
        result = await self._session.scalars(stmt)
        return [self._to_entity(m) for m in result.unique()]

    async def search_similar(
        self,
        embedding: list[float],
        limit: int,
        equipment: Equipment | None = None,
        difficulty: Difficulty | None = None,
    ) -> list[Exercise]:
        stmt = select(ExerciseModel).where(ExerciseModel.embedding.is_not(None))
        if equipment is not None:
            stmt = stmt.where(ExerciseModel.equipment == equipment)
        if difficulty is not None:
            stmt = stmt.where(ExerciseModel.difficulty == difficulty)
        # pgvector cosine distance: smaller is more similar.
        stmt = stmt.order_by(ExerciseModel.embedding.cosine_distance(embedding)).limit(limit)
        result = await self._session.scalars(stmt)
        return [self._to_entity(m) for m in result.unique()]
