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


class _FakeFoodRepo:
    def __init__(self, foods: list[object]) -> None:
        self._foods = foods

    async def list_all(self) -> list[object]:
        return self._foods

    async def search_similar(self, embedding: list[float], limit: int) -> list[object]:
        return self._foods[:limit]


async def test_list_foods_returns_catalog() -> None:
    from app.application.use_cases.nutrition_use_cases import ListFoods
    from app.domain.entities.food import Food

    food = Food(id=1, name="Egg", category="protein", kcal=155, protein_g=13, carbs_g=1.1, fat_g=11)
    result = await ListFoods(_FakeFoodRepo([food])).execute()  # type: ignore[arg-type]
    assert result[0].name == "Egg"
    assert result[0].category == "protein"


async def test_recommend_meals_grounds_reply_on_retrieved_foods() -> None:
    from app.application.use_cases.nutrition_use_cases import RecommendMeals
    from app.domain.entities.food import Food
    from app.infrastructure.ai.embeddings import FakeEmbedding
    from app.infrastructure.ai.llm import StubLLM

    foods = [
        Food(
            id=1,
            name="Chicken breast",
            category="protein",
            kcal=165,
            protein_g=31,
            carbs_g=0,
            fat_g=4,
        )
    ]
    rec = await RecommendMeals(FakeEmbedding(384), _FakeFoodRepo(foods), StubLLM()).execute(
        "protein"
    )
    assert rec.foods[0].name == "Chicken breast"
    assert "no es consejo" in rec.reply.lower()


async def test_recommend_meals_empty_message_returns_no_foods() -> None:
    from app.application.use_cases.nutrition_use_cases import RecommendMeals
    from app.infrastructure.ai.embeddings import FakeEmbedding
    from app.infrastructure.ai.llm import StubLLM

    rec = await RecommendMeals(FakeEmbedding(384), _FakeFoodRepo([]), StubLLM()).execute("   ")
    assert rec.foods == ()
