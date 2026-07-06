"""Public exercise endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import provide_exercise
from app.api.v1.schemas.exercise import ExerciseRead
from app.application.use_cases.exercise_use_cases import GetExercise
from app.domain.entities.exercise import Exercise

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("/{exercise_id}", response_model=ExerciseRead, summary="Get an exercise by id")
async def get_exercise(
    exercise_id: int,
    use_case: Annotated[GetExercise, Depends(provide_exercise)],
) -> Exercise:
    exercise = await use_case.execute(exercise_id)
    if exercise is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
    return exercise
