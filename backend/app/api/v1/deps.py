"""FastAPI dependency providers wiring adapters into use cases.

Routers depend on these so they never construct infrastructure directly; tests
can override `get_session` to point at a test database.
"""

from typing import Annotated, Literal

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.exercise_use_cases import GetExercise
from app.application.use_cases.muscle_use_cases import (
    GetMuscle,
    ListMuscleExercises,
    ListMuscles,
)
from app.application.use_cases.recommend_exercises import RecommendExercises
from app.core.config import get_settings
from app.infrastructure.ai.factory import build_embedding, build_llm
from app.infrastructure.persistence.database import get_session
from app.infrastructure.persistence.repositories.exercise_repository import (
    SqlAlchemyExerciseRepository,
)
from app.infrastructure.persistence.repositories.muscle_repository import (
    SqlAlchemyMuscleRepository,
)


def get_locale(lang: Literal["es", "en"] = Query("es")) -> str:
    """Requested content locale from the `lang` query param (default Spanish)."""
    return lang


SessionDep = Annotated[AsyncSession, Depends(get_session)]
LocaleDep = Annotated[str, Depends(get_locale)]


def provide_list_muscles(session: SessionDep, locale: LocaleDep) -> ListMuscles:
    return ListMuscles(SqlAlchemyMuscleRepository(session, locale))


def provide_muscle(session: SessionDep, locale: LocaleDep) -> GetMuscle:
    return GetMuscle(SqlAlchemyMuscleRepository(session, locale))


def provide_muscle_exercises(session: SessionDep, locale: LocaleDep) -> ListMuscleExercises:
    return ListMuscleExercises(
        SqlAlchemyMuscleRepository(session, locale),
        SqlAlchemyExerciseRepository(session, locale),
    )


def provide_exercise(session: SessionDep, locale: LocaleDep) -> GetExercise:
    return GetExercise(SqlAlchemyExerciseRepository(session, locale))


def provide_recommend_exercises(session: SessionDep, locale: LocaleDep) -> RecommendExercises:
    settings = get_settings()
    return RecommendExercises(
        build_embedding(settings),
        SqlAlchemyExerciseRepository(session, locale),
        build_llm(settings),
    )
