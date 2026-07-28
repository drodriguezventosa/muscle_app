"""Public exercise endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.deps import provide_exercise, provide_search_exercises
from app.api.v1.schemas.exercise import ExerciseRead
from app.application.use_cases.exercise_use_cases import GetExercise, SearchExercises
from app.domain.entities.exercise import Exercise

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get(
    "",
    response_model=list[ExerciseRead],
    summary="Search the exercise catalog by name",
)
async def search_exercises(
    use_case: Annotated[SearchExercises, Depends(provide_search_exercises)],
    search: Annotated[str | None, Query(alias="q", max_length=80)] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> list[Exercise]:
    return await use_case.execute(search, limit)


@router.get("/{exercise_id}", response_model=ExerciseRead, summary="Get an exercise by id")
async def get_exercise(
    exercise_id: int,
    use_case: Annotated[GetExercise, Depends(provide_exercise)],
) -> Exercise:
    exercise = await use_case.execute(exercise_id)
    if exercise is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
    return exercise
