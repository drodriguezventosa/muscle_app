"""Port for the coaching data: rosters, student history and progress writes."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import date

from app.domain.entities.coaching import LoggedSession, Student, StudentDetail, Trainer
from app.domain.value_objects.enums import Difficulty, Goal


class CoachingRepository(ABC):
    """Reads a trainer's students and records a student's own progress.

    The roster is part of the contract on purpose: `get_student` takes the
    trainer id so the "is this student mine?" check cannot be forgotten by a
    caller (OWASP A01, deny by default).
    """

    @abstractmethod
    async def list_students(self, trainer_id: int) -> list[Student]:
        """Return the students this trainer follows, with their headline numbers."""

    @abstractmethod
    async def get_student(self, trainer_id: int, student_id: int) -> StudentDetail | None:
        """Return the full history of one of this trainer's students, or None.

        None also covers "exists but is not yours", so the API cannot be used to
        probe which student ids exist.
        """

    @abstractmethod
    async def get_own_detail(self, user_id: int) -> StudentDetail | None:
        """Return the signed-in user's own history, or None if they have no profile."""

    @abstractmethod
    async def list_trainers(self) -> list[Trainer]:
        """Return every trainer on offer, with their profile and student count."""

    @abstractmethod
    async def get_trainer_of(self, student_id: int) -> Trainer | None:
        """Return the student's trainer, or None if they have not hired one."""

    @abstractmethod
    async def assign_trainer(self, student_id: int, trainer_id: int) -> Trainer | None:
        """Link the student to that trainer, replacing any earlier one.

        Returns the trainer, or None if the id is not a trainer. A student has
        at most one: hiring again is a change, not a second subscription.
        """

    @abstractmethod
    async def unassign_trainer(self, student_id: int) -> None:
        """Drop the student's trainer link, if there is one."""

    @abstractmethod
    async def upsert_sessions(self, user_id: int, sessions: Sequence[LoggedSession]) -> int:
        """Store these sessions, replacing same-day entries for the same exercise.

        Returns how many were written. Never deletes history the client did not
        send: the browser may only hold a slice of it.
        """

    @abstractmethod
    async def record_weight(self, user_id: int, measured_on: date, weight_kg: float) -> None:
        """Store the body weight for that day, overwriting an earlier value."""

    @abstractmethod
    async def upsert_profile(
        self,
        user_id: int,
        *,
        age: int | None = None,
        height_cm: int | None = None,
        goal: Goal | None = None,
        level: Difficulty | None = None,
    ) -> None:
        """Merge these attributes into the student profile, leaving the rest as is."""
