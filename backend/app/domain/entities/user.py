"""Authenticated user of the coaching area (clients and trainers)."""

from dataclasses import dataclass

from app.domain.value_objects.enums import UserRole


@dataclass(frozen=True)
class User:
    """A person who can sign in. Never carries the password hash.

    Hashes stay in the persistence layer so a use case (or a response schema)
    cannot leak one by accident.
    """

    id: int
    email: str
    name: str
    role: UserRole

    @property
    def is_trainer(self) -> bool:
        return self.role is UserRole.TRAINER
