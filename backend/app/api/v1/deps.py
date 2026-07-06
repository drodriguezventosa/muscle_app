"""FastAPI dependency providers wiring adapters into use cases.

Routers depend on these so they never construct infrastructure directly; tests
can override `get_session` to point at a test database.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.exercise_use_cases import GetExercise
from app.application.use_cases.muscle_use_cases import (
    GetMuscle,
    ListMuscleExercises,
    ListMuscles,
)
from app.infrastructure.persistence.database import get_session
from app.infrastructure.persistence.repositories.exercise_repository import (
    SqlAlchemyExerciseRepository,
)
from app.infrastructure.persistence.repositories.muscle_repository import (
    SqlAlchemyMuscleRepository,
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def provide_list_muscles(session: SessionDep) -> ListMuscles:
    return ListMuscles(SqlAlchemyMuscleRepository(session))


def provide_muscle(session: SessionDep) -> GetMuscle:
    return GetMuscle(SqlAlchemyMuscleRepository(session))


def provide_muscle_exercises(session: SessionDep) -> ListMuscleExercises:
    return ListMuscleExercises(
        SqlAlchemyMuscleRepository(session),
        SqlAlchemyExerciseRepository(session),
    )


def provide_exercise(session: SessionDep) -> GetExercise:
    return GetExercise(SqlAlchemyExerciseRepository(session))
