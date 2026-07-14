"""Unit tests for the RAG recommendation use case (fake adapters, no DB)."""

from app.application.use_cases.recommend_exercises import DISCLAIMER, RecommendExercises
from app.domain.entities.exercise import Exercise
from app.domain.ports.ai import EmbeddingPort
from app.domain.ports.repositories import ExerciseRepository
from app.domain.value_objects.enums import Difficulty, Equipment
from app.infrastructure.ai.embeddings import FakeEmbedding
from app.infrastructure.ai.llm import StubLLM
from app.infrastructure.cache.memory import InMemoryCache

EXERCISES = [
    Exercise(
        id=1,
        name="Push-up",
        description="Bodyweight chest press.",
        equipment=Equipment.BODYWEIGHT,
        difficulty=Difficulty.BEGINNER,
    )
]


class RecordingExerciseRepository(ExerciseRepository):
    def __init__(self, exercises: list[Exercise]) -> None:
        self._exercises = exercises
        self.last_call: dict[str, object] | None = None

    async def get_by_id(self, exercise_id: int) -> Exercise | None:
        return next((e for e in self._exercises if e.id == exercise_id), None)

    async def list_for_muscle(self, muscle_id: int) -> list[Exercise]:
        return []

    async def search_similar(
        self,
        embedding: list[float],
        limit: int,
        equipment: Equipment | None = None,
        difficulty: Difficulty | None = None,
    ) -> list[Exercise]:
        self.last_call = {
            "dim": len(embedding),
            "limit": limit,
            "equipment": equipment,
            "difficulty": difficulty,
        }
        return self._exercises[:limit]


def _use_case(repo: ExerciseRepository) -> RecommendExercises:
    return RecommendExercises(FakeEmbedding(384), repo, StubLLM())


async def test_returns_reply_with_disclaimer_and_exercises() -> None:
    recommendation = await _use_case(RecordingExerciseRepository(EXERCISES)).execute(
        "quiero entrenar pecho en casa"
    )
    assert recommendation.exercises[0].name == "Push-up"
    assert DISCLAIMER in recommendation.reply


async def test_empty_message_asks_for_input_and_returns_no_exercises() -> None:
    recommendation = await _use_case(RecordingExerciseRepository(EXERCISES)).execute("   ")
    assert recommendation.exercises == ()
    assert DISCLAIMER in recommendation.reply


class CountingEmbedding(EmbeddingPort):
    """Wraps FakeEmbedding and counts how many times a query is embedded."""

    def __init__(self, dim: int) -> None:
        self._inner = FakeEmbedding(dim)
        self.calls = 0

    async def embed(self, text: str) -> list[float]:
        self.calls += 1
        return await self._inner.embed(text)

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        return await self._inner.embed_many(texts)


async def test_caches_query_embedding_across_calls() -> None:
    embedding = CountingEmbedding(384)
    use_case = RecommendExercises(
        embedding, RecordingExerciseRepository(EXERCISES), StubLLM(), cache=InMemoryCache()
    )
    await use_case.execute("pecho en casa")
    await use_case.execute("pecho en casa")  # same query → served from cache
    assert embedding.calls == 1


async def test_passes_filters_and_query_embedding_to_search() -> None:
    repo = RecordingExerciseRepository(EXERCISES)
    await _use_case(repo).execute(
        "algo de fuerza", equipment=Equipment.BARBELL, difficulty=Difficulty.ADVANCED, limit=3
    )
    assert repo.last_call == {
        "dim": 384,
        "limit": 3,
        "equipment": Equipment.BARBELL,
        "difficulty": Difficulty.ADVANCED,
    }
