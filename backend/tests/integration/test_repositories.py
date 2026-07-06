"""Integration tests for the SQLAlchemy repositories and the seed."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.value_objects.enums import MuscleRole
from app.infrastructure.persistence.repositories.exercise_repository import (
    SqlAlchemyExerciseRepository,
)
from app.infrastructure.persistence.repositories.muscle_repository import (
    SqlAlchemyMuscleRepository,
)
from app.infrastructure.persistence.seed import seed


async def test_seed_is_idempotent(session: AsyncSession) -> None:
    assert await seed(session) is True
    assert await seed(session) is False  # second run inserts nothing


async def test_muscle_repository_reads(session: AsyncSession) -> None:
    await seed(session)
    repo = SqlAlchemyMuscleRepository(session)

    all_muscles = await repo.list_all()
    assert len(all_muscles) == 10

    chest = await repo.get_by_svg_id("chest")
    assert chest is not None
    assert chest.name == "Pectoralis major"

    assert await repo.get_by_svg_id("does-not-exist") is None
    assert await repo.get_by_id(chest.id or 0) is not None


async def test_exercise_repository_lists_for_muscle(session: AsyncSession) -> None:
    await seed(session)
    muscles = SqlAlchemyMuscleRepository(session)
    exercises = SqlAlchemyExerciseRepository(session)

    chest = await muscles.get_by_svg_id("chest")
    assert chest is not None and chest.id is not None

    chest_exercises = await exercises.list_for_muscle(chest.id)
    names = {e.name for e in chest_exercises}
    assert "Push-up" in names
    assert "Barbell bench press" in names

    push_up = next(e for e in chest_exercises if e.name == "Push-up")
    assert push_up.works_muscle(chest.id)
    primary = [tm for tm in push_up.targeted_muscles if tm.role is MuscleRole.PRIMARY]
    assert any(tm.muscle_id == chest.id for tm in primary)
