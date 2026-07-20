"""Public nutrition endpoints (orientation only — not dietary/medical advice)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from app.api.v1.deps import (
    provide_calculate_nutrition,
    provide_list_foods,
    provide_recommend_meals,
)
from app.api.v1.schemas.nutrition import (
    FoodRead,
    MealRequest,
    MealResponse,
    NutritionRequest,
    NutritionTargetsRead,
)
from app.application.dto.nutrition import NutritionTargets
from app.application.use_cases.nutrition_use_cases import (
    CalculateNutrition,
    ListFoods,
    RecommendMeals,
)
from app.core.rate_limit import RATE_LIMIT, limiter
from app.domain.entities.food import Food

router = APIRouter(prefix="/nutrition", tags=["nutrition"])

# The food catalog changes rarely — let browsers/CDNs cache it.
_CATALOG_CACHE = "public, max-age=300, stale-while-revalidate=86400"


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


@router.get("/foods", response_model=list[FoodRead], summary="List the food catalog")
async def list_foods(
    response: Response,
    use_case: Annotated[ListFoods, Depends(provide_list_foods)],
) -> list[Food]:
    response.headers["Cache-Control"] = _CATALOG_CACHE
    return await use_case.execute()


@router.post(
    "/recommendations",
    response_model=MealResponse,
    summary="Suggest meals from a free-text request (RAG over the food catalog)",
)
@limiter.limit(RATE_LIMIT)
async def recommend_meals(
    request: Request,  # required by slowapi to identify the client
    payload: MealRequest,
    use_case: Annotated[RecommendMeals, Depends(provide_recommend_meals)],
) -> MealResponse:
    rec = await use_case.execute(payload.message)
    return MealResponse(reply=rec.reply, foods=list(rec.foods))
