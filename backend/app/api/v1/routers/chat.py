"""Public recommendation chatbot endpoint (rate-limited)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.v1.deps import provide_recommend_exercises
from app.api.v1.schemas.chat import ChatRequest, ChatResponse
from app.application.use_cases.recommend_exercises import RecommendExercises
from app.core.rate_limit import RATE_LIMIT, limiter

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "/recommendations",
    response_model=ChatResponse,
    summary="Recommend exercises from a free-text request",
)
@limiter.limit(RATE_LIMIT)
async def recommend(
    request: Request,  # required by slowapi to identify the client
    payload: ChatRequest,
    use_case: Annotated[RecommendExercises, Depends(provide_recommend_exercises)],
) -> ChatResponse:
    recommendation = await use_case.execute(payload.message, payload.equipment, payload.difficulty)
    return ChatResponse(reply=recommendation.reply, exercises=list(recommendation.exercises))
