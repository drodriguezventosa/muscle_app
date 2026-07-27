"""Authentication use cases for the coaching area."""

from dataclasses import dataclass

from app.domain.entities.user import User
from app.domain.ports.auth import (
    InvalidCredentialsError,
    InvalidTokenError,
    PasswordHasher,
    TokenService,
    UserRepository,
)

# Verified when the email is unknown so that a failed login takes the same time
# whether or not the account exists (no timing-based user enumeration). It is a
# real Argon2 hash of a random string, never a usable password.
_DUMMY_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHRzb21lc2FsdA$"
    "0Uu2u1ZQ8dQyKQ0m5cVJ0HcCkI8CzZ0mYQyH4Yl0aVg"
)


@dataclass(frozen=True, slots=True)
class Session:
    """A signed-in user plus the token the client must send back."""

    user: User
    access_token: str
    expires_in: int


class AuthenticateUser:
    """Exchange email + password for an access token."""

    def __init__(self, users: UserRepository, hasher: PasswordHasher, tokens: TokenService) -> None:
        self._users = users
        self._hasher = hasher
        self._tokens = tokens

    async def execute(self, email: str, password: str) -> Session:
        user = await self._users.get_by_email(email)
        stored = await self._users.get_password_hash(user.id) if user else None

        # Always run a verification, even without a user, to keep the timing flat.
        if not self._hasher.verify(password, stored or _DUMMY_HASH) or user is None:
            raise InvalidCredentialsError("email or password is not valid")

        token, expires_in = self._tokens.issue(user)
        return Session(user=user, access_token=token, expires_in=expires_in)


class GetAuthenticatedUser:
    """Resolve the user behind an access token.

    The role is read from the database, never from the token payload, so a
    tampered or stale token cannot escalate privileges.
    """

    def __init__(self, users: UserRepository, tokens: TokenService) -> None:
        self._users = users
        self._tokens = tokens

    async def execute(self, token: str) -> User:
        user_id = self._tokens.read_subject(token)
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise InvalidTokenError("user no longer exists")
        return user
