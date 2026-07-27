"""Password hashing adapter (Argon2id).

Argon2id is the current OWASP recommendation for password storage: memory-hard,
so GPU cracking is expensive. The library encodes algorithm, parameters and salt
inside the hash string, which makes future parameter changes transparent.
"""

from argon2 import PasswordHasher as Argon2PasswordHasher
from argon2.exceptions import Argon2Error

from app.domain.ports.auth import PasswordHasher


class Argon2Hasher(PasswordHasher):
    def __init__(self) -> None:
        self._hasher = Argon2PasswordHasher()

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, hashed: str) -> bool:
        # Any failure (mismatch, malformed hash) is just "not verified": the
        # caller must not be able to tell the cases apart.
        try:
            return self._hasher.verify(hashed, password)
        except (Argon2Error, ValueError, TypeError):
            return False
