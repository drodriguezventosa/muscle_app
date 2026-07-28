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


async def test_the_seed_writes_the_days_a_narrower_window_left_empty(
    session: AsyncSession,
) -> None:
    """Regression: the deployed calendar stayed at the single week it was seeded with.

    Both the plan and the history bailed out when their table already had rows,
    so widening the window (a week of demo data became the whole year) reached
    production as a no-op — the same trap the food catalog fell into. Seeding a
    narrow window and then a wider one is exactly that deploy.
    """
    from sqlalchemy import func
    from sqlalchemy import select as sa_select

    from app.infrastructure.persistence.models.coaching import WorkoutLogModel
    from app.infrastructure.persistence.models.plan import PlanItemModel

    async def counts() -> tuple[int, int]:
        return (
            int(await session.scalar(sa_select(func.count()).select_from(PlanItemModel)) or 0),
            int(await session.scalar(sa_select(func.count()).select_from(WorkoutLogModel)) or 0),
        )

    await seed(session, weeks=1)
    narrow_plan, narrow_logs = await counts()
    assert narrow_plan and narrow_logs

    await seed(session, weeks=4)
    wide_plan, wide_logs = await counts()

    assert wide_plan > narrow_plan
    assert wide_logs > narrow_logs
    # Widening does not duplicate what the narrow window already wrote.
    stacked = await session.scalar(
        sa_select(func.count()).select_from(
            sa_select(PlanItemModel.student_id)
            .group_by(
                PlanItemModel.student_id,
                PlanItemModel.exercise_id,
                PlanItemModel.scheduled_on,
            )
            .having(func.count() > 1)
            .subquery()
        )
    )
    assert stacked == 0


async def test_the_seed_leaves_a_day_the_trainer_edited_alone(session: AsyncSession) -> None:
    # The trainer writes this same table from the app, so a re-seed must not
    # resurrect a prescription they removed from a day they already worked on.
    from sqlalchemy import delete, func
    from sqlalchemy import select as sa_select

    from app.infrastructure.persistence.models.plan import PlanItemModel

    await seed(session, weeks=SEED_WEEKS)
    day = await session.scalar(sa_select(func.min(PlanItemModel.scheduled_on)))
    student_id = await session.scalar(
        sa_select(PlanItemModel.student_id).where(PlanItemModel.scheduled_on == day).limit(1)
    )
    doomed = await session.scalar(
        sa_select(PlanItemModel.id)
        .where(PlanItemModel.scheduled_on == day, PlanItemModel.student_id == student_id)
        .limit(1)
    )
    await session.execute(delete(PlanItemModel).where(PlanItemModel.id == doomed))
    await session.commit()
    before = await session.scalar(
        sa_select(func.count())
        .select_from(PlanItemModel)
        .where(PlanItemModel.scheduled_on == day, PlanItemModel.student_id == student_id)
    )

    await seed(session, weeks=SEED_WEEKS)

    after = await session.scalar(
        sa_select(func.count())
        .select_from(PlanItemModel)
        .where(PlanItemModel.scheduled_on == day, PlanItemModel.student_id == student_id)
    )
    assert after == before


async def test_the_seed_keeps_a_session_the_student_reported(session: AsyncSession) -> None:
    # A student's own logged session shares the (exercise, day) key with a seeded
    # one; the seed must never rewrite what they actually lifted.
    from sqlalchemy import func, update
    from sqlalchemy import select as sa_select

    from app.infrastructure.persistence.models.coaching import WorkoutLogModel

    await seed(session, weeks=SEED_WEEKS)
    log_id = await session.scalar(sa_select(func.min(WorkoutLogModel.id)))
    await session.execute(
        update(WorkoutLogModel).where(WorkoutLogModel.id == log_id).values(weight_kg=123.5, reps=7)
    )
    await session.commit()

    await seed(session, weeks=SEED_WEEKS)

    kept = await session.scalar(
        sa_select(WorkoutLogModel.weight_kg).where(WorkoutLogModel.id == log_id)
    )
    assert kept == 123.5


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
