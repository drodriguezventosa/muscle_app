"""Port for the training plan: scheduling exercises and reading them back."""

from abc import ABC, abstractmethod
from datetime import date

from app.domain.entities.plan import PlanItem


class TrainingPlanRepository(ABC):
    """Stores what a trainer scheduled, joined with what the student logged."""

    @abstractmethod
    async def list_for_student(
        self, student_id: int, trainer_id: int, start: date, end: date
    ) -> list[PlanItem]:
        """Return what this trainer scheduled for this student, both days included.

        Keyed by the pair and not by the student alone: each trainer keeps their
        own calendar, so a student who changes trainer sees the new one's plan
        and the previous one's stays with them.
        """

    @abstractmethod
    async def get(self, item_id: int) -> PlanItem | None:
        """Return one item, or None. Carries both ids so callers can check ownership."""

    @abstractmethod
    async def add(
        self,
        *,
        trainer_id: int,
        student_id: int,
        exercise_id: int,
        scheduled_on: date,
        target_sets: int,
        target_reps: int,
        target_weight_kg: float | None,
        notes: str | None,
    ) -> PlanItem | None:
        """Schedule an exercise. Returns None if that exercise is not in the catalog.

        Re-scheduling the same exercise on the same day updates the targets
        instead of stacking duplicates.
        """

    @abstractmethod
    async def remove(self, item_id: int) -> bool:
        """Delete an item. Returns False if it was already gone."""
