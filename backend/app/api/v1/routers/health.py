"""Liveness and readiness probes (required by Cloud Run and Docker healthchecks)."""

from fastapi import APIRouter

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
