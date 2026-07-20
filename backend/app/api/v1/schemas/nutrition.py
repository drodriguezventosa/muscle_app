"""Pydantic schemas for the nutrition endpoints."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.value_objects.enums import ActivityLevel, NutritionGoal


class NutritionRequest(BaseModel):
    """Body attributes for the calorie/macro estimate. Sent in the POST body
    (not the query string) so personal data stays out of URLs."""

    sex: Literal["male", "female", "other"] | None = None
    age: int = Field(ge=14, le=100)
    height_cm: float = Field(ge=120, le=230)
    weight_kg: float = Field(ge=30, le=300)
    activity: ActivityLevel
    goal: NutritionGoal


class NutritionTargetsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bmr: int
    tdee: int
    calories: int
    protein_g: int
    carbs_g: int
    fat_g: int
    bmi: float
    bmi_category: str
    goal: NutritionGoal
    warning: str | None = None
