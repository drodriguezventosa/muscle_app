"""FastAPI dependency providers wiring adapters into use cases.

Routers depend on these so they never construct infrastructure directly; tests
can override `get_session` to point at a test database.
"""

from functools import lru_cache
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.auth_use_cases import AuthenticateUser, GetAuthenticatedUser
from app.application.use_cases.coaching_use_cases import (
    GetOwnProgress,
    GetStudentDashboard,
    ListStudents,
    SyncProgress,
)
from app.application.use_cases.exercise_use_cases import GetExercise, SearchExercises
from app.application.use_cases.muscle_use_cases import (
    GetMuscle,
    ListActiveMuscles,
    ListMuscleExercises,
    ListMuscles,
)
from app.application.use_cases.nutrition_use_cases import (
    AnalyzeMealPhoto,
    CalculateNutrition,
    ListFoods,
    RecommendMeals,
)
from app.application.use_cases.plan_use_cases import (
    ListOwnPlan,
    ListStudentPlan,
    ReportPlanItem,
    ScheduleExercise,
    UnscheduleExercise,
)
from app.application.use_cases.recommend_exercises import RecommendExercises
from app.application.use_cases.workout_use_cases import GenerateWorkout
from app.core.config import get_settings
from app.domain.entities.user import User
from app.domain.ports.auth import InvalidTokenError
from app.domain.ports.cache import CachePort
from app.infrastructure.ai.factory import build_embedding, build_llm, build_vision
from app.infrastructure.cache.factory import build_cache
from app.infrastructure.persistence.database import get_session
from app.infrastructure.persistence.repositories.coaching_repository import (
    SqlAlchemyCoachingRepository,
)
from app.infrastructure.persistence.repositories.exercise_repository import (
    SqlAlchemyExerciseRepository,
)
from app.infrastructure.persistence.repositories.food_repository import (
    SqlAlchemyFoodRepository,
)
from app.infrastructure.persistence.repositories.muscle_repository import (
    SqlAlchemyMuscleRepository,
)
from app.infrastructure.persistence.repositories.plan_repository import (
    SqlAlchemyTrainingPlanRepository,
)
from app.infrastructure.persistence.repositories.user_repository import SqlAlchemyUserRepository
from app.infrastructure.security.hashing import Argon2Hasher
from app.infrastructure.security.tokens import JwtTokenService

# auto_error=False so a missing header yields our own 401 shape, not FastAPI's.
_bearer_scheme = HTTPBearer(auto_error=False)


def get_locale(lang: Literal["es", "en"] = Query("es")) -> str:
    """Requested content locale from the `lang` query param (default Spanish)."""
    return lang


@lru_cache
def get_cache() -> CachePort:
    """Process-wide cache singleton (so an in-memory cache is shared across requests)."""
    return build_cache(get_settings())


SessionDep = Annotated[AsyncSession, Depends(get_session)]
LocaleDep = Annotated[str, Depends(get_locale)]


def provide_list_muscles(session: SessionDep, locale: LocaleDep) -> ListMuscles:
    return ListMuscles(SqlAlchemyMuscleRepository(session, locale))


def provide_muscle(session: SessionDep, locale: LocaleDep) -> GetMuscle:
    return GetMuscle(SqlAlchemyMuscleRepository(session, locale))


def provide_active_muscles(session: SessionDep, locale: LocaleDep) -> ListActiveMuscles:
    return ListActiveMuscles(SqlAlchemyMuscleRepository(session, locale))


def provide_muscle_exercises(session: SessionDep, locale: LocaleDep) -> ListMuscleExercises:
    return ListMuscleExercises(
        SqlAlchemyMuscleRepository(session, locale),
        SqlAlchemyExerciseRepository(session, locale),
    )


def provide_exercise(session: SessionDep, locale: LocaleDep) -> GetExercise:
    return GetExercise(SqlAlchemyExerciseRepository(session, locale))


def provide_search_exercises(session: SessionDep, locale: LocaleDep) -> SearchExercises:
    return SearchExercises(SqlAlchemyExerciseRepository(session, locale))


def provide_generate_workout(session: SessionDep, locale: LocaleDep) -> GenerateWorkout:
    return GenerateWorkout(
        SqlAlchemyMuscleRepository(session, locale),
        SqlAlchemyExerciseRepository(session, locale),
        locale,
    )


def provide_calculate_nutrition() -> CalculateNutrition:
    return CalculateNutrition()


def provide_list_foods(session: SessionDep, locale: LocaleDep) -> ListFoods:
    return ListFoods(SqlAlchemyFoodRepository(session, locale))


def provide_analyze_meal_photo() -> AnalyzeMealPhoto:
    settings = get_settings()
    return AnalyzeMealPhoto(build_vision(settings), settings.vision_max_image_bytes)


def provide_recommend_meals(session: SessionDep, locale: LocaleDep) -> RecommendMeals:
    settings = get_settings()
    return RecommendMeals(
        build_embedding(settings),
        SqlAlchemyFoodRepository(session, locale),
        build_llm(settings),
        cache=get_cache(),
        cache_ttl_seconds=settings.cache_ttl_seconds,
    )


def provide_recommend_exercises(session: SessionDep, locale: LocaleDep) -> RecommendExercises:
    settings = get_settings()
    return RecommendExercises(
        build_embedding(settings),
        SqlAlchemyExerciseRepository(session, locale),
        build_llm(settings),
        cache=get_cache(),
        cache_ttl_seconds=settings.cache_ttl_seconds,
    )


def provide_authenticate_user(session: SessionDep) -> AuthenticateUser:
    settings = get_settings()
    return AuthenticateUser(
        SqlAlchemyUserRepository(session),
        Argon2Hasher(),
        JwtTokenService(settings.jwt_secret, settings.jwt_expire_minutes),
    )


def provide_list_students(session: SessionDep) -> ListStudents:
    return ListStudents(SqlAlchemyCoachingRepository(session))


def provide_student_dashboard(session: SessionDep, locale: LocaleDep) -> GetStudentDashboard:
    return GetStudentDashboard(SqlAlchemyCoachingRepository(session, locale))


def provide_get_own_progress(session: SessionDep, locale: LocaleDep) -> GetOwnProgress:
    return GetOwnProgress(SqlAlchemyCoachingRepository(session, locale))


def provide_sync_progress(session: SessionDep) -> SyncProgress:
    return SyncProgress(SqlAlchemyCoachingRepository(session))


def provide_list_student_plan(session: SessionDep, locale: LocaleDep) -> ListStudentPlan:
    return ListStudentPlan(
        SqlAlchemyTrainingPlanRepository(session, locale),
        SqlAlchemyCoachingRepository(session, locale),
    )


def provide_list_own_plan(session: SessionDep, locale: LocaleDep) -> ListOwnPlan:
    return ListOwnPlan(SqlAlchemyTrainingPlanRepository(session, locale))


def provide_schedule_exercise(session: SessionDep, locale: LocaleDep) -> ScheduleExercise:
    return ScheduleExercise(
        SqlAlchemyTrainingPlanRepository(session, locale),
        SqlAlchemyCoachingRepository(session, locale),
    )


def provide_unschedule_exercise(session: SessionDep) -> UnscheduleExercise:
    return UnscheduleExercise(
        SqlAlchemyTrainingPlanRepository(session),
        SqlAlchemyCoachingRepository(session),
    )


def provide_report_plan_item(session: SessionDep, locale: LocaleDep) -> ReportPlanItem:
    return ReportPlanItem(
        SqlAlchemyTrainingPlanRepository(session, locale),
        SqlAlchemyCoachingRepository(session, locale),
    )


async def get_current_user(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> User:
    """Resolve the bearer token into a user, or 401.

    The role is re-read from the database on every request, so a tampered or
    stale token cannot grant privileges it no longer has.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    settings = get_settings()
    use_case = GetAuthenticatedUser(
        SqlAlchemyUserRepository(session),
        JwtTokenService(settings.jwt_secret, settings.jwt_expire_minutes),
    )
    try:
        return await use_case.execute(credentials.credentials)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_trainer(user: CurrentUser) -> User:
    """Guard for the trainer-only endpoints (OWASP A01: deny by default)."""
    if not user.is_trainer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Trainer role required")
    return user


TrainerUser = Annotated[User, Depends(require_trainer)]
