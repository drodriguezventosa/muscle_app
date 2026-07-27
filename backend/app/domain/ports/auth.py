"""Ports for authentication: user lookup, password hashing and tokens.

Concrete adapters live in `app.infrastructure.security` and
`app.infrastructure.persistence`. Keeping hashing and tokens behind ports means
the algorithm (Argon2 today) or the token format can change without touching
the use cases.
"""

from abc import ABC, abstractmethod

from app.domain.entities.user import User


class InvalidCredentialsError(Exception):
    """Email unknown or password mismatch.

    Deliberately one error for both cases: telling them apart would let an
    attacker enumerate registered emails (OWASP A07).
    """


class InvalidTokenError(Exception):
    """The token is malformed, expired or signed with another key."""


class UserRepository(ABC):
    """Read access to the user directory."""

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Return the user with this email, or None."""

    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None:
        """Return the user with this id, or None."""

    @abstractmethod
    async def get_password_hash(self, user_id: int) -> str | None:
        """Return the stored password hash, or None if the user is gone.

        Separate from the entity on purpose: the hash never travels with `User`.
        """


class PasswordHasher(ABC):
    """Hashes and verifies passwords."""

    @abstractmethod
    def hash(self, password: str) -> str:
        """Return a self-describing hash (algorithm + parameters + salt)."""

    @abstractmethod
    def verify(self, password: str, hashed: str) -> bool:
        """Return True if the password matches the hash, never raising."""


class TokenService(ABC):
    """Issues and reads the access tokens that identify a signed-in user."""

    @abstractmethod
    def issue(self, user: User) -> tuple[str, int]:
        """Return (token, seconds until it expires)."""

    @abstractmethod
    def read_subject(self, token: str) -> int:
        """Return the user id inside the token, or raise InvalidTokenError."""
