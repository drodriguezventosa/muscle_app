"""Response schemas for exercise endpoints."""

from pydantic import BaseModel, ConfigDict

from app.domain.value_objects.enums import Difficulty, Equipment, MuscleRole


class TargetedMuscleRead(BaseModel):
    """A muscle worked by an exercise, with the role it plays."""

    model_config = ConfigDict(from_attributes=True)

    muscle_id: int
    role: MuscleRole


class ExerciseRead(BaseModel):
    """An exercise as exposed by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    equipment: Equipment
    difficulty: Difficulty
    video_url: str | None = None
    steps: list[str] = []
    targeted_muscles: list[TargetedMuscleRead]
