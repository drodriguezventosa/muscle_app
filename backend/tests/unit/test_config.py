"""Tests for settings parsing, notably CORS origins from the environment."""

import pytest
from sqlalchemy import make_url

from app.core.config import Settings


def test_cors_origins_defaults() -> None:
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.cors_origins == ["http://localhost:5173"]


def test_cors_origins_from_comma_separated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reproduces the real deploy scenario: a plain comma-separated string.
    monkeypatch.setenv("CORS_ORIGINS", "http://a.com, http://b.com")
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.cors_origins == ["http://a.com", "http://b.com"]


def test_cors_origins_accepts_a_list() -> None:
    settings = Settings(_env_file=None, cors_origins=["http://x.com"])  # type: ignore[call-arg]
    assert settings.cors_origins == ["http://x.com"]


def test_database_url_encodes_special_characters() -> None:
    # Managed providers (Neon) issue passwords with @ / . - etc.; the DSN must
    # round-trip them, not break the URL.
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        postgres_user="alex",
        postgres_password="np-g.A@b/c:1",  # noqa: S106  (fake test password)
        postgres_host="ep-x.neon.tech",
        postgres_db="neondb",
    )
    url = make_url(settings.database_url)
    assert url.password == "np-g.A@b/c:1"  # noqa: S105  (fake test password)
    assert url.host == "ep-x.neon.tech"
    assert url.database == "neondb"
    assert url.drivername == "postgresql+asyncpg"
