"""Request/response schemas for the workout generator."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.api.v1.schemas.exercise import ExerciseRead
from app.domain.value_objects.enums import Difficulty, Equipment, Goal


class WorkoutGenerateRequest(BaseModel):
    """Minimal attributes to build a basic routine. Sent in the body (not the
    query string) to keep personal data out of URLs."""

    goal: Goal
    experience: Difficulty
    height_cm: float = Field(gt=50, lt=260)
    weight_kg: float = Field(gt=20, lt=400)
    sex: Literal["male", "female", "other"] | None = None
    age: int | None = Field(default=None, ge=10, le=100)
    equipment: list[Equipment] | None = None


class WorkoutItemRead(BaseModel):
    """One exercise in the routine with its prescription."""

    model_config = ConfigDict(from_attributes=True)

    exercise: ExerciseRead
    sets: int
    reps: str
    rest_seconds: int


class WorkoutRead(BaseModel):
    """A generated routine plus the BMI context."""

    goal: Goal
    name: str
    description: str
    difficulty: Difficulty
    bmi: float
    bmi_category: str
    items: list[WorkoutItemRead]
