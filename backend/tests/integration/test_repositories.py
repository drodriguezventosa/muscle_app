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


async def test_muscle_repository_reads_default_spanish(session: AsyncSession) -> None:
    await seed(session)
    repo = SqlAlchemyMuscleRepository(session)  # default locale: es

    all_muscles = await repo.list_all()
    assert len(all_muscles) == 10

    chest = await repo.get_by_svg_id("chest")
    assert chest is not None
    assert chest.name == "Pectoral mayor"

    assert await repo.get_by_svg_id("does-not-exist") is None
    assert await repo.get_by_id(chest.id or 0) is not None


async def test_muscle_repository_resolves_english(session: AsyncSession) -> None:
    await seed(session)
    repo = SqlAlchemyMuscleRepository(session, locale="en")
    chest = await repo.get_by_svg_id("chest")
    assert chest is not None
    assert chest.name == "Pectoralis major"


async def test_exercise_repository_lists_for_muscle(session: AsyncSession) -> None:
    await seed(session)
    muscles = SqlAlchemyMuscleRepository(session)
    exercises_es = SqlAlchemyExerciseRepository(session)
    exercises_en = SqlAlchemyExerciseRepository(session, locale="en")

    chest = await muscles.get_by_svg_id("chest")
    assert chest is not None and chest.id is not None

    names_es = {e.name for e in await exercises_es.list_for_muscle(chest.id)}
    assert "Flexiones" in names_es
    assert "Press de banca con barra" in names_es

    names_en = {e.name for e in await exercises_en.list_for_muscle(chest.id)}
    assert "Push-up" in names_en

    push_up = next(e for e in await exercises_es.list_for_muscle(chest.id) if e.name == "Flexiones")
    assert push_up.works_muscle(chest.id)
    primary = [tm for tm in push_up.targeted_muscles if tm.role is MuscleRole.PRIMARY]
    assert any(tm.muscle_id == chest.id for tm in primary)
