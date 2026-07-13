"""Public workout generator endpoint (rate-limited)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.v1.deps import provide_generate_workout
from app.api.v1.schemas.workout import WorkoutGenerateRequest, WorkoutItemRead, WorkoutRead
from app.application.dto.workout import WorkoutRequest
from app.application.use_cases.workout_use_cases import GenerateWorkout
from app.core.rate_limit import RATE_LIMIT, limiter

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.post(
    "/generate",
    response_model=WorkoutRead,
    summary="Generate a basic routine from a goal and minimal attributes",
)
@limiter.limit(RATE_LIMIT)
async def generate_workout(
    request: Request,  # required by slowapi to identify the client
    payload: WorkoutGenerateRequest,
    use_case: Annotated[GenerateWorkout, Depends(provide_generate_workout)],
) -> WorkoutRead:
    result = await use_case.execute(
        WorkoutRequest(
            goal=payload.goal,
            experience=payload.experience,
            height_cm=payload.height_cm,
            weight_kg=payload.weight_kg,
            sex=payload.sex,
            age=payload.age,
            equipment=payload.equipment,
        )
    )
    template = result.template
    return WorkoutRead(
        goal=template.goal,
        name=template.name,
        description=template.description,
        difficulty=template.difficulty,
        bmi=result.bmi,
        bmi_category=result.bmi_category,
        items=[WorkoutItemRead.model_validate(item) for item in template.items],
    )
