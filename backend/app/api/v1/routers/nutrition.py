"""Public nutrition endpoints (orientation only — not dietary/medical advice)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.deps import provide_calculate_nutrition
from app.api.v1.schemas.nutrition import NutritionRequest, NutritionTargetsRead
from app.application.dto.nutrition import NutritionTargets
from app.application.use_cases.nutrition_use_cases import CalculateNutrition

router = APIRouter(prefix="/nutrition", tags=["nutrition"])


@router.post(
    "/calculate",
    response_model=NutritionTargetsRead,
    summary="Estimate daily calories and macronutrient targets",
)
async def calculate(
    payload: NutritionRequest,
    use_case: Annotated[CalculateNutrition, Depends(provide_calculate_nutrition)],
) -> NutritionTargets:
    return use_case.execute(
        sex=payload.sex,
        age=payload.age,
        height_cm=payload.height_cm,
        weight_kg=payload.weight_kg,
        activity=payload.activity,
        goal=payload.goal,
    )
