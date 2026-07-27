"""Sign-in endpoints for the coaching area (rate-limited)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.v1.deps import CurrentUser, provide_authenticate_user
from app.api.v1.schemas.auth import LoginRequest, SessionRead, UserRead
from app.application.use_cases.auth_use_cases import AuthenticateUser
from app.core.rate_limit import limiter
from app.domain.ports.auth import InvalidCredentialsError

router = APIRouter(prefix="/auth", tags=["auth"])

# Tighter than the general limit: brute-forcing a password is the attack this
# endpoint invites (OWASP A07).
_LOGIN_RATE_LIMIT = "10/minute"


@router.post("/login", response_model=SessionRead, summary="Sign in and get an access token")
@limiter.limit(_LOGIN_RATE_LIMIT)
async def login(
    request: Request,  # required by slowapi to identify the client
    payload: LoginRequest,
    use_case: Annotated[AuthenticateUser, Depends(provide_authenticate_user)],
) -> SessionRead:
    try:
        session = await use_case.execute(payload.email, payload.password)
    except InvalidCredentialsError as exc:
        # One message for both "unknown email" and "wrong password": telling them
        # apart would let an attacker enumerate accounts.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return SessionRead(
        access_token=session.access_token,
        expires_in=session.expires_in,
        user=UserRead.model_validate(session.user),
    )


@router.get("/me", response_model=UserRead, summary="Who the current token belongs to")
async def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
