"""Response schemas for muscle endpoints."""

from pydantic import BaseModel, ConfigDict

from app.domain.value_objects.enums import MuscleGroup


class MuscleRead(BaseModel):
    """A muscle as exposed by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    muscle_group: MuscleGroup
    svg_id: str
    description: str
