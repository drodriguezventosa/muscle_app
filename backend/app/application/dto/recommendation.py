"""DTO returned by the recommendation use case."""

from dataclasses import dataclass, field

from app.domain.entities.exercise import Exercise


@dataclass(frozen=True, slots=True)
class Recommendation:
    """A chatbot reply plus the exercises the recommendation is grounded on."""

    reply: str
    exercises: tuple[Exercise, ...] = field(default_factory=tuple)
