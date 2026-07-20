"""Nutrition use cases. Deterministic energy/macro estimation (no external calls).

Formulas are standard and orientation-only (Mifflin-St Jeor BMR + activity
factor). Safeguards avoid unsafe advice: no calorie deficit for an underweight
person, and a hard minimum-calorie floor.
"""

from app.application.dto.nutrition import NutritionTargets
from app.domain.entities.food import Food
from app.domain.ports.repositories import FoodRepository
from app.domain.value_objects.enums import ActivityLevel, NutritionGoal

# Activity multipliers over BMR (standard Mifflin-St Jeor companions).
_ACTIVITY_FACTOR: dict[ActivityLevel, float] = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHT: 1.375,
    ActivityLevel.MODERATE: 1.55,
    ActivityLevel.ACTIVE: 1.725,
    ActivityLevel.VERY_ACTIVE: 1.9,
}
# Calorie adjustment over maintenance per goal.
_GOAL_FACTOR: dict[NutritionGoal, float] = {
    NutritionGoal.LOSE_FAT: 0.80,  # ~20% deficit
    NutritionGoal.MAINTAIN: 1.0,
    NutritionGoal.GAIN_MUSCLE: 1.10,  # ~10% surplus
}
# Protein grams per kg of bodyweight per goal (higher in a deficit to spare muscle).
_PROTEIN_PER_KG: dict[NutritionGoal, float] = {
    NutritionGoal.LOSE_FAT: 2.0,
    NutritionGoal.MAINTAIN: 1.6,
    NutritionGoal.GAIN_MUSCLE: 1.8,
}
# Sex offset for the Mifflin-St Jeor equation; unknown/other uses the mean.
_SEX_OFFSET: dict[str, int] = {"male": 5, "female": -161}
_OTHER_OFFSET = -78

MIN_CALORIES = 1200  # absolute floor; below this needs professional supervision
_FAT_KCAL_SHARE = 0.25  # 25% of calories from fat


def _bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "underweight"
    if bmi < 25:
        return "normal"
    if bmi < 30:
        return "overweight"
    return "obese"


class CalculateNutrition:
    """Estimate daily calories and macros from body attributes, activity and goal."""

    def execute(
        self,
        *,
        sex: str | None,
        age: int,
        height_cm: float,
        weight_kg: float,
        activity: ActivityLevel,
        goal: NutritionGoal,
    ) -> NutritionTargets:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age
        bmr += _SEX_OFFSET.get(sex or "", _OTHER_OFFSET)
        tdee = bmr * _ACTIVITY_FACTOR[activity]

        height_m = height_cm / 100
        bmi = weight_kg / (height_m * height_m)

        warning: str | None = None
        effective_goal = goal
        # Safeguard: don't push a deficit on someone already underweight.
        if bmi < 18.5 and goal == NutritionGoal.LOSE_FAT:
            effective_goal = NutritionGoal.MAINTAIN
            warning = "underweight_no_deficit"

        calories = tdee * _GOAL_FACTOR[effective_goal]
        if calories < MIN_CALORIES:
            calories = MIN_CALORIES
            warning = warning or "min_calories_floor"

        protein_g = _PROTEIN_PER_KG[effective_goal] * weight_kg
        fat_g = calories * _FAT_KCAL_SHARE / 9
        carbs_kcal = calories - protein_g * 4 - fat_g * 9
        carbs_g = max(carbs_kcal, 0) / 4

        return NutritionTargets(
            bmr=round(bmr),
            tdee=round(tdee),
            calories=round(calories),
            protein_g=round(protein_g),
            carbs_g=round(carbs_g),
            fat_g=round(fat_g),
            bmi=round(bmi, 1),
            bmi_category=_bmi_category(bmi),
            goal=effective_goal,
            warning=warning,
        )


class ListFoods:
    """Return the whole food catalog (localized by the repository)."""

    def __init__(self, foods: FoodRepository) -> None:
        self._foods = foods

    async def execute(self) -> list[Food]:
        return await self._foods.list_all()
