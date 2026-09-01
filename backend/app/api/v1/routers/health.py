"""Liveness and readiness probes (required by Cloud Run and Docker healthchecks)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.deps import get_cache
from app.domain.ports.cache import CachePort

router = APIRouter(tags=["health"])


# GET + HEAD: uptime monitors (e.g. UptimeRobot) ping with HEAD by default, so
# the probes must answer HEAD too — otherwise they'd 405 and read as "down".
@router.api_route("/health", methods=["GET", "HEAD"], summary="Liveness probe")
async def health() -> dict[str, str]:
    """Return 200 if the process is alive."""
    return {"status": "ok"}


@router.api_route("/ready", methods=["GET", "HEAD"], summary="Readiness probe")
async def ready() -> dict[str, str]:
    """Return 200 when the app is ready to serve traffic.

    Deliberately does **not** query the database, and the uptime monitor must
    keep pointing at `/health` rather than here. Neon's free plan allows 100
    CU-hours a month and suspends the compute for the rest of the period once
    they are spent; it also scales to zero after 5 minutes of inactivity, which
    cannot be disabled. A probe that touched the database every 5 minutes would
    therefore hold the compute awake 24/7 — about 180 CU-hours a month — and buy
    a ~1 s resume at the price of the database being down for the back half of
    every month. The stale connections a suspend leaves behind are already
    handled by `pool_pre_ping` on the engine.

    If a real dependency check is ever needed (a deploy gate, say), give it its
    own path and call it on demand, never on a schedule.
    """
    return {"status": "ready"}


@router.api_route("/health/cache", methods=["GET", "HEAD"], summary="Cache keep-alive probe")
async def health_cache(cache: Annotated[CachePort, Depends(get_cache)]) -> dict[str, str]:
    """Touch the cache so a managed Redis (Upstash) registers traffic.

    Upstash archives free-tier databases after a few weeks without commands, so
    the keep-alive workflow pings this endpoint alongside `/health`. Unlike the
    database (see `/ready`), touching Redis on a schedule costs nothing: the
    free tier is billed per command and the ping spends ~9K of the 500K monthly
    allowance. With the in-memory cache (dev/tests) this is a harmless no-op.

    Always returns 200 — the cache port is best-effort by contract, and this
    probe exists to generate traffic, not to gate anything. The body reports
    whether the round-trip actually worked so the workflow logs show it.
    """
    await cache.set("health:keepalive", "pong", ttl_seconds=3600)
    value = await cache.get("health:keepalive")
    return {"status": "ok", "cache": "ok" if value == "pong" else "unavailable"}
