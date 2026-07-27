"""Unit tests for the coaching sign-in: hashing, tokens and the use cases."""

import time

import pytest

from app.application.use_cases.auth_use_cases import AuthenticateUser, GetAuthenticatedUser
from app.domain.entities.user import User
from app.domain.ports.auth import (
    InvalidCredentialsError,
    InvalidTokenError,
    UserRepository,
)
from app.domain.value_objects.enums import UserRole
from app.infrastructure.security.hashing import Argon2Hasher
from app.infrastructure.security.tokens import JwtTokenService

TRAINER = User(id=1, email="coach@demo.app", name="Ana", role=UserRole.TRAINER)
CLIENT = User(id=2, email="student@demo.app", name="Javier", role=UserRole.CLIENT)


class _FakeUserRepository(UserRepository):
    def __init__(self, users: list[User], hashes: dict[int, str]) -> None:
        self._users = users
        self._hashes = hashes

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self._users if u.email == email.strip().lower()), None)

    async def get_by_id(self, user_id: int) -> User | None:
        return next((u for u in self._users if u.id == user_id), None)

    async def get_password_hash(self, user_id: int) -> str | None:
        return self._hashes.get(user_id)


def _repo(password: str = "right-password") -> _FakeUserRepository:  # noqa: S107 - test fixture
    hasher = Argon2Hasher()
    return _FakeUserRepository(
        [TRAINER, CLIENT], {1: hasher.hash(password), 2: hasher.hash(password)}
    )


def _tokens() -> JwtTokenService:
    return JwtTokenService("test-secret", expire_minutes=60)


def test_argon2_hash_is_salted_and_verifies() -> None:
    hasher = Argon2Hasher()
    first, second = hasher.hash("hunter2"), hasher.hash("hunter2")

    assert first != second  # random salt per hash
    assert first.startswith("$argon2id$")  # memory-hard algorithm, per OWASP
    assert hasher.verify("hunter2", first)
    assert not hasher.verify("wrong", first)


def test_argon2_verify_never_raises_on_a_broken_hash() -> None:
    assert not Argon2Hasher().verify("hunter2", "not-a-hash")


def test_token_round_trip_carries_the_user_id() -> None:
    token, expires_in = _tokens().issue(TRAINER)
    assert expires_in == 3600
    assert _tokens().read_subject(token) == TRAINER.id


def test_token_signed_with_another_secret_is_rejected() -> None:
    token, _ = JwtTokenService("other-secret", 60).issue(TRAINER)
    with pytest.raises(InvalidTokenError):
        _tokens().read_subject(token)


def test_expired_token_is_rejected() -> None:
    token, _ = JwtTokenService("test-secret", expire_minutes=-1).issue(TRAINER)
    time.sleep(0.01)
    with pytest.raises(InvalidTokenError):
        _tokens().read_subject(token)


@pytest.mark.parametrize("garbage", ["", "abc", "a.b.c"])
def test_malformed_tokens_are_rejected(garbage: str) -> None:
    with pytest.raises(InvalidTokenError):
        _tokens().read_subject(garbage)


async def test_login_returns_a_session_for_valid_credentials() -> None:
    use_case = AuthenticateUser(_repo(), Argon2Hasher(), _tokens())
    session = await use_case.execute("coach@demo.app", "right-password")

    assert session.user == TRAINER
    assert session.expires_in == 3600
    assert _tokens().read_subject(session.access_token) == TRAINER.id


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("coach@demo.app", "wrong-password"),
        ("nobody@demo.app", "right-password"),  # unknown email, same error
    ],
)
async def test_login_rejects_bad_credentials_without_saying_which(
    email: str, password: str
) -> None:
    use_case = AuthenticateUser(_repo(), Argon2Hasher(), _tokens())
    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(email, password)


async def test_current_user_is_resolved_from_the_database_not_the_token() -> None:
    # The role travels in the payload for convenience, but authorization must be
    # re-read from the repository, so a stale/tampered claim buys nothing.
    token, _ = _tokens().issue(
        User(id=2, email="student@demo.app", name="x", role=UserRole.TRAINER)
    )
    user = await GetAuthenticatedUser(_repo(), _tokens()).execute(token)

    assert user == CLIENT
    assert user.is_trainer is False


async def test_token_of_a_deleted_user_is_rejected() -> None:
    token, _ = _tokens().issue(User(id=99, email="ghost@demo.app", name="x", role=UserRole.CLIENT))
    with pytest.raises(InvalidTokenError):
        await GetAuthenticatedUser(_repo(), _tokens()).execute(token)
