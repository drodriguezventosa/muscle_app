"""Domain value objects expressed as enumerations.

These are stable, closed sets used across the domain. They carry no behavior
beyond their membership and are safe to expose in the API layer.
"""

from enum import StrEnum


class MuscleGroup(StrEnum):
    """High-level grouping used to organize muscles in the body explorer."""

    CHEST = "chest"
    BACK = "back"
    SHOULDERS = "shoulders"
    ARMS = "arms"
    CORE = "core"
    LEGS = "legs"
    GLUTES = "glutes"


class Equipment(StrEnum):
    """Equipment a given exercise requires."""

    BODYWEIGHT = "bodyweight"
    DUMBBELL = "dumbbell"
    BARBELL = "barbell"
    MACHINE = "machine"
    CABLE = "cable"
    KETTLEBELL = "kettlebell"
    BAND = "band"


class Difficulty(StrEnum):
    """Relative difficulty of an exercise."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class MuscleRole(StrEnum):
    """Whether an exercise targets a muscle as a primary or secondary mover."""

    PRIMARY = "primary"
    SECONDARY = "secondary"


class Goal(StrEnum):
    """Training goal a workout template is designed for."""

    FAT_LOSS = "fat_loss"
    HYPERTROPHY = "hypertrophy"
    STRENGTH = "strength"
