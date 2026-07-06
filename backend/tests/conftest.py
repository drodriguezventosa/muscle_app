"""Shared pytest fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
    """Isolated test settings (no external dependencies)."""
    return Settings(app_env="test", cors_origins=["http://testserver"])


@pytest.fixture
def client(settings: Settings) -> TestClient:
    """FastAPI test client built from a fresh app instance."""
    return TestClient(create_app(settings))
