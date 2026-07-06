"""Public muscle explorer endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import provide_list_muscles, provide_muscle, provide_muscle_exercises
from app.api.v1.schemas.exercise import ExerciseRead
from app.api.v1.schemas.muscle import MuscleRead
from app.application.use_cases.muscle_use_cases import GetMuscle, ListMuscleExercises, ListMuscles
from app.domain.entities.exercise import Exercise
from app.domain.entities.muscle import Muscle

router = APIRouter(prefix="/muscles", tags=["muscles"])


@router.get("", response_model=list[MuscleRead], summary="List all muscles")
async def list_muscles(
    use_case: Annotated[ListMuscles, Depends(provide_list_muscles)],
) -> list[Muscle]:
    return await use_case.execute()


@router.get("/{svg_id}", response_model=MuscleRead, summary="Get a muscle by SVG id")
async def get_muscle(
    svg_id: str,
    use_case: Annotated[GetMuscle, Depends(provide_muscle)],
) -> Muscle:
    muscle = await use_case.execute(svg_id)
    if muscle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Muscle not found")
    return muscle


@router.get(
    "/{svg_id}/exercises",
    response_model=list[ExerciseRead],
    summary="List exercises that train a muscle",
)
async def list_muscle_exercises(
    svg_id: str,
    use_case: Annotated[ListMuscleExercises, Depends(provide_muscle_exercises)],
) -> list[Exercise]:
    exercises = await use_case.execute(svg_id)
    if exercises is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Muscle not found")
    return exercises
