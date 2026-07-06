"""Aggregates feature routers served under the /api/v1 prefix.

Health/readiness probes are mounted at the root in `app.main`, not here, so
that orchestrators (Cloud Run, Docker) can reach them without the version prefix.
"""

from fastapi import APIRouter

from app.api.v1.routers import chat, exercises, muscles

api_router = APIRouter()
api_router.include_router(muscles.router)
api_router.include_router(exercises.router)
api_router.include_router(chat.router)
