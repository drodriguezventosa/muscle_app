"""Tests for the liveness/readiness probes and baseline hardening."""

from fastapi.testclient import TestClient

from app.api.v1.deps import get_cache
from app.domain.ports.cache import CachePort


class _DownCache(CachePort):
    """Cache whose backend is unreachable: every operation degrades to a miss."""

    async def get(self, key: str) -> str | None:
        return None

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        return None


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_ready(client: TestClient) -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_health_accepts_head(client: TestClient) -> None:
    # Uptime monitors ping with HEAD; it must return 200, not 405.
    response = client.head("/health")
    assert response.status_code == 200


def test_health_cache_round_trip(client: TestClient) -> None:
    # The keep-alive workflow hits this so Upstash sees traffic; with the
    # in-memory cache used in tests the set/get round-trip must succeed.
    response = client.get("/health/cache")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "cache": "ok"}


def test_health_cache_accepts_head(client: TestClient) -> None:
    response = client.head("/health/cache")
    assert response.status_code == 200


def test_health_cache_degrades_when_cache_down(client: TestClient) -> None:
    # A dead Redis must never fail the probe: still 200, reported in the body.
    client.app.dependency_overrides[get_cache] = _DownCache  # type: ignore[attr-defined]
    try:
        response = client.get("/health/cache")
    finally:
        client.app.dependency_overrides.pop(get_cache)  # type: ignore[attr-defined]
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "cache": "unavailable"}


def test_security_headers_present(client: TestClient) -> None:
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in response.headers
