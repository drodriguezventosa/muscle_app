"""Tests for settings parsing, notably CORS origins from the environment."""

import pytest

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
