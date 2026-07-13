"""SQLAlchemy implementation of the ExerciseRepository port."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.exercise import Exercise, TargetedMuscle
from app.domain.ports.repositories import ExerciseRepository
from app.domain.value_objects.enums import Difficulty, Equipment
from app.infrastructure.persistence.models.exercise import ExerciseModel, ExerciseMuscleModel
from app.infrastructure.persistence.repositories.localize import pick


def to_exercise_entity(model: ExerciseModel, locale: str) -> Exercise:
    """Map an exercise ORM row to a domain entity for the requested locale.

    Shared so other repositories (e.g. workouts) can embed exercises too.
    """
    video = model.video_url
    if locale == "en" and model.video_url_en:
        video = model.video_url_en
    steps = model.steps
    if locale == "en" and model.steps_en:
        steps = model.steps_en
    return Exercise(
        id=model.id,
        name=pick(model.name, model.name_en, locale),
        description=pick(model.description, model.description_en, locale),
        equipment=model.equipment,
        difficulty=model.difficulty,
        video_url=video,
        steps=tuple(steps or ()),
        targeted_muscles=tuple(
            TargetedMuscle(muscle_id=link.muscle_id, role=link.role) for link in model.muscles
        ),
    )


class SqlAlchemyExerciseRepository(ExerciseRepository):
    def __init__(self, session: AsyncSession, locale: str = "es") -> None:
        self._session = session
        self._locale = locale

    def _to_entity(self, model: ExerciseModel) -> Exercise:
        return to_exercise_entity(model, self._locale)

    async def get_by_id(self, exercise_id: int) -> Exercise | None:
        model = await self._session.get(ExerciseModel, exercise_id)
        return self._to_entity(model) if model else None

    async def list_for_muscle(
        self,
        muscle_id: int,
        equipment: list[Equipment] | None = None,
        difficulty: list[Difficulty] | None = None,
    ) -> list[Exercise]:
        stmt = (
            select(ExerciseModel)
            .join(ExerciseMuscleModel, ExerciseMuscleModel.exercise_id == ExerciseModel.id)
            .where(ExerciseMuscleModel.muscle_id == muscle_id)
            .order_by(ExerciseModel.name)
        )
        if equipment:
            stmt = stmt.where(ExerciseModel.equipment.in_(equipment))
        if difficulty:
            stmt = stmt.where(ExerciseModel.difficulty.in_(difficulty))
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
