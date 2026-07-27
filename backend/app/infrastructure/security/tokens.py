"""Access-token adapter (JWT, HS256).

Stateless on purpose: no session table to keep in sync on a free-tier host. The
trade-off is that a token stays valid until it expires, hence the short TTL.
"""

from datetime import UTC, datetime, timedelta

import jwt

from app.domain.entities.user import User
from app.domain.ports.auth import InvalidTokenError, TokenService

_ALGORITHM = "HS256"


class JwtTokenService(TokenService):
    def __init__(self, secret: str, expire_minutes: int) -> None:
        self._secret = secret
        self._expire_minutes = expire_minutes

    def issue(self, user: User) -> tuple[str, int]:
        expires_in = self._expire_minutes * 60
        now = datetime.now(UTC)
        payload = {
            "sub": str(user.id),
            "role": user.role.value,  # convenience for the client, never trusted
            "iat": now,
            "exp": now + timedelta(minutes=self._expire_minutes),
        }
        return jwt.encode(payload, self._secret, algorithm=_ALGORITHM), expires_in

    def read_subject(self, token: str) -> int:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[_ALGORITHM])
            return int(payload["sub"])
        except (jwt.PyJWTError, KeyError, TypeError, ValueError) as exc:
            # The role in the payload is ignored: authorization is resolved from
            # the database on every request, so a tampered token gains nothing.
            raise InvalidTokenError("invalid or expired token") from exc
