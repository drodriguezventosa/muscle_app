"""DTO returned by the nutrition calculation use case."""

from dataclasses import dataclass

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
