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


class ActivityLevel(StrEnum):
    """Physical activity level, used to scale BMR into daily energy needs."""

    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"


class NutritionGoal(StrEnum):
    """Dietary goal driving the calorie adjustment over maintenance."""

    LOSE_FAT = "lose_fat"
    MAINTAIN = "maintain"
    GAIN_MUSCLE = "gain_muscle"


class DietTag(StrEnum):
    """Dietary suitability tags for foods (for filtering/RAG)."""

    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    HIGH_PROTEIN = "high_protein"
