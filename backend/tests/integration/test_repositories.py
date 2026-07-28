"""Integration tests for the SQLAlchemy repositories and the seed."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.value_objects.enums import Difficulty, Equipment, MuscleRole
from app.infrastructure.persistence.repositories.exercise_repository import (
    SqlAlchemyExerciseRepository,
)
from app.infrastructure.persistence.repositories.muscle_repository import (
    SqlAlchemyMuscleRepository,
)
from app.infrastructure.persistence.seed import seed
from tests.integration.conftest import SEED_WEEKS


async def test_seed_is_idempotent(session: AsyncSession) -> None:
    assert await seed(session, weeks=SEED_WEEKS) is True
    assert await seed(session, weeks=SEED_WEEKS) is False  # second run inserts nothing


async def test_muscle_repository_reads_default_spanish(session: AsyncSession) -> None:
    await seed(session, weeks=SEED_WEEKS)
    repo = SqlAlchemyMuscleRepository(session)  # default locale: es

    all_muscles = await repo.list_all()
    assert len(all_muscles) == 10

    chest = await repo.get_by_svg_id("chest")
    assert chest is not None
    assert chest.name == "Pectoral mayor"

    assert await repo.get_by_svg_id("does-not-exist") is None
    assert await repo.get_by_id(chest.id or 0) is not None


async def test_muscle_repository_resolves_english(session: AsyncSession) -> None:
    await seed(session, weeks=SEED_WEEKS)
    repo = SqlAlchemyMuscleRepository(session, locale="en")
    chest = await repo.get_by_svg_id("chest")
    assert chest is not None
    assert chest.name == "Pectoralis major"


async def test_exercise_repository_lists_for_muscle(session: AsyncSession) -> None:
    await seed(session, weeks=SEED_WEEKS)
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


async def test_exercise_repository_list_catalog_applies_filters(session: AsyncSession) -> None:
    # Non-vector fallback used when the embedding provider is unavailable: it must
    # return real rows (no embedding required) and honour the structured filters.
    await seed(session, weeks=SEED_WEEKS)
    repo = SqlAlchemyExerciseRepository(session)

    everything = await repo.list_catalog(limit=5)
    assert 0 < len(everything) <= 5

    filtered = await repo.list_catalog(limit=10, equipment=Equipment.BODYWEIGHT)
    assert filtered
    assert all(e.equipment == Equipment.BODYWEIGHT for e in filtered)

    by_level = await repo.list_catalog(limit=10, difficulty=Difficulty.BEGINNER)
    assert by_level
    assert all(e.difficulty == Difficulty.BEGINNER for e in by_level)


async def test_food_seed_inserts_only_the_missing_foods(session: AsyncSession) -> None:
    # Regression: the seed used to insert only when the table was empty, so newly
    # curated foods never reached an already-populated (deployed) database.
    from sqlalchemy import delete, func
    from sqlalchemy import select as sa_select

    from app.infrastructure.persistence.models.food import FoodModel
    from app.infrastructure.persistence.seed import FOODS, _seed_foods

    await seed(session, weeks=SEED_WEEKS)
    total = await session.scalar(sa_select(func.count()).select_from(FoodModel))
    assert total == len(FOODS)

    # Re-running changes nothing...
    assert await _seed_foods(session) == 0

    # ...but a food missing from a populated catalog is restored, and it comes
    # back without an embedding so the boot-time backfill vectorizes it.
    await session.execute(delete(FoodModel).where(FoodModel.name == FOODS[0][0]))
    await session.commit()
    assert await _seed_foods(session) == 1
    restored = await session.scalar(sa_select(FoodModel).where(FoodModel.name == FOODS[0][0]))
    assert restored is not None
    assert restored.embedding is None
