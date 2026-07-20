"""Unit tests for the nutrition calculation use case (deterministic, no DB)."""

from app.application.use_cases.nutrition_use_cases import MIN_CALORIES, CalculateNutrition
from app.domain.value_objects.enums import ActivityLevel, NutritionGoal


def _calc(**kwargs: object) -> object:
    defaults: dict[str, object] = {
        "sex": "male",
        "age": 30,
        "height_cm": 180.0,
        "weight_kg": 80.0,
        "activity": ActivityLevel.MODERATE,
        "goal": NutritionGoal.MAINTAIN,
    }
    defaults.update(kwargs)
    return CalculateNutrition().execute(**defaults)  # type: ignore[arg-type]


def test_bmr_and_tdee_match_mifflin_st_jeor() -> None:
    t = _calc()
    # 10*80 + 6.25*180 - 5*30 + 5 = 1780; TDEE = 1780 * 1.55 = 2759
    assert t.bmr == 1780
    assert t.tdee == 2759
    assert t.bmi == 24.7


def test_goal_adjusts_calories_over_maintenance() -> None:
    maintain = _calc(goal=NutritionGoal.MAINTAIN).calories
    lose = _calc(goal=NutritionGoal.LOSE_FAT).calories
    gain = _calc(goal=NutritionGoal.GAIN_MUSCLE).calories
    assert lose < maintain < gain


def test_macros_are_consistent_with_calories() -> None:
    t = _calc()
    # kcal from macros should be within rounding of the calorie target
    kcal = t.protein_g * 4 + t.carbs_g * 4 + t.fat_g * 9
    assert abs(kcal - t.calories) <= 15


def test_underweight_does_not_get_a_deficit() -> None:
    t = _calc(weight_kg=50.0, height_cm=180.0, goal=NutritionGoal.LOSE_FAT)
    assert t.bmi_category == "underweight"
    assert t.goal == NutritionGoal.MAINTAIN  # deficit overridden
    assert t.warning == "underweight_no_deficit"


def test_calories_never_below_the_floor() -> None:
    t = _calc(
        weight_kg=40.0,
        height_cm=150.0,
        age=70,
        activity=ActivityLevel.SEDENTARY,
        goal=NutritionGoal.LOSE_FAT,
    )
    assert t.calories >= MIN_CALORIES
