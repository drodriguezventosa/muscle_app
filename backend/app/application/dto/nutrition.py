"""DTOs returned by the nutrition use cases."""

from dataclasses import dataclass, field

from app.domain.entities.food import Food
from app.domain.value_objects.enums import NutritionGoal


@dataclass(frozen=True, slots=True)
class NutritionTargets:
    """Estimated daily energy and macronutrient targets (orientation only)."""

    bmr: int  # basal metabolic rate (kcal)
    tdee: int  # total daily energy expenditure (kcal)
    calories: int  # target intake for the goal (kcal)
    protein_g: int
    carbs_g: int
    fat_g: int
    bmi: float
    bmi_category: str  # key: underweight | normal | overweight | obese
    goal: NutritionGoal  # effective goal (may differ from requested, see warning)
    # Optional i18n key when a safeguard adjusted the result, else None.
    warning: str | None = None


@dataclass(frozen=True, slots=True)
class MealRecommendation:
    """A nutrition chatbot reply plus the foods it is grounded on."""

    reply: str
    foods: tuple[Food, ...] = field(default_factory=tuple)
