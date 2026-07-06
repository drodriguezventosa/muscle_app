"""Request/response schemas for the recommendation chatbot."""

from pydantic import BaseModel, Field

from app.api.v1.schemas.exercise import ExerciseRead
from app.domain.value_objects.enums import Difficulty, Equipment


class ChatRequest(BaseModel):
    """A free-text training request with optional structured filters."""

    message: str = Field(min_length=1, max_length=500)
    equipment: Equipment | None = None
    difficulty: Difficulty | None = None


class ChatResponse(BaseModel):
    """The assistant reply plus the exercises it is grounded on."""

    reply: str
    exercises: list[ExerciseRead]
