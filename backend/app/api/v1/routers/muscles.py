"""Public muscle explorer endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.deps import (
    provide_active_muscles,
    provide_list_muscles,
    provide_muscle,
    provide_muscle_exercises,
)
from app.api.v1.schemas.exercise import ExerciseRead
from app.api.v1.schemas.muscle import MuscleRead
from app.application.use_cases.muscle_use_cases import (
    GetMuscle,
    ListActiveMuscles,
    ListMuscleExercises,
    ListMuscles,
)
from app.domain.entities.exercise import Exercise
from app.domain.entities.muscle import Muscle
from app.domain.value_objects.enums import Difficulty, Equipment

router = APIRouter(prefix="/muscles", tags=["muscles"])

EquipmentFilter = Annotated[list[Equipment] | None, Query(description="Filter by equipment")]
DifficultyFilter = Annotated[list[Difficulty] | None, Query(description="Filter by difficulty")]


@router.get("", response_model=list[MuscleRead], summary="List all muscles")
async def list_muscles(
    use_case: Annotated[ListMuscles, Depends(provide_list_muscles)],
) -> list[Muscle]:
    return await use_case.execute()


@router.get(
    "/active",
    response_model=list[MuscleRead],
    summary="List muscles that have exercises matching the filters",
)
async def list_active_muscles(
    use_case: Annotated[ListActiveMuscles, Depends(provide_active_muscles)],
    equipment: EquipmentFilter = None,
    difficulty: DifficultyFilter = None,
) -> list[Muscle]:
    return await use_case.execute(equipment, difficulty)


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
    equipment: EquipmentFilter = None,
    difficulty: DifficultyFilter = None,
) -> list[Exercise]:
    exercises = await use_case.execute(svg_id, equipment, difficulty)
    if exercises is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Muscle not found")
    return exercises
