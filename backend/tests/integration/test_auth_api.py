"""Integration tests for the sign-in endpoints against a real database."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.infrastructure.persistence.seed import DEMO_USERS, seed

TRAINER_EMAIL = "entrenador@demo.muscleapp"
CLIENT_EMAIL = "alumno@demo.muscleapp"


async def _login(api_client: AsyncClient, email: str) -> str:
    response = await api_client.post(
        "/api/v1/auth/login", json={"email": email, "password": get_settings().demo_password}
    )
    assert response.status_code == 200, response.text
    return str(response.json()["access_token"])


async def test_seed_creates_the_demo_accounts_once(session: AsyncSession) -> None:
    from app.infrastructure.persistence.seed import _seed_users

    await seed(session)
    # Re-running must not duplicate them (the seed is idempotent).
    assert await _seed_users(session, get_settings().demo_password) == 0
    assert {email for _, email, _ in DEMO_USERS} == {TRAINER_EMAIL, CLIENT_EMAIL}


async def test_login_returns_a_token_and_the_user(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    await seed(session)
    response = await api_client.post(
        "/api/v1/auth/login",
        json={"email": TRAINER_EMAIL, "password": get_settings().demo_password},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"  # noqa: S105 - OAuth2 token type
    assert body["user"]["role"] == "trainer"
    assert "password" not in response.text.lower()  # never leak credentials back


async def test_login_with_a_wrong_password_is_401(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    await seed(session)
    response = await api_client.post(
        "/api/v1/auth/login", json={"email": TRAINER_EMAIL, "password": "not-the-password"}
    )
    assert response.status_code == 401
    # Same wording as an unknown email, so accounts cannot be enumerated.
    assert response.json()["detail"] == "Invalid email or password"


async def test_login_with_an_unknown_email_is_401_with_the_same_message(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    await seed(session)
    response = await api_client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@demo.muscleapp", "password": get_settings().demo_password},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


async def test_me_requires_a_token_and_returns_the_user(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    await seed(session)
    assert (await api_client.get("/api/v1/auth/me")).status_code == 401

    token = await _login(api_client, CLIENT_EMAIL)
    response = await api_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == CLIENT_EMAIL
    assert response.json()["role"] == "client"


async def test_a_garbage_token_is_401(api_client: AsyncClient, session: AsyncSession) -> None:
    await seed(session)
    response = await api_client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401
