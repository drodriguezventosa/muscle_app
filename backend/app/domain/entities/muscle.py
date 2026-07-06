"""Muscle domain entity."""

from dataclasses import dataclass

from app.domain.value_objects.enums import MuscleGroup


@dataclass(frozen=True, slots=True)
class Muscle:
    """A single muscle shown in the interactive body explorer.

    `svg_id` links the entity to the corresponding shape in the frontend SVG,
    so the UI can highlight it. `id` is None until the muscle is persisted.
    """

    name: str
    muscle_group: MuscleGroup
    svg_id: str
    description: str
    id: int | None = None
