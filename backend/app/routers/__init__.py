"""API router aggregation.

Each router file owns one concern (auth, library, player, activity,
settings, dashboard). Register new routers here.
"""

from __future__ import annotations

from fastapi import APIRouter

from .activity_routes import router as activity_router
from .auth_routes import router as auth_router
from .dashboard_routes import router as dashboard_router
from .library_routes import router as library_router
from .player_routes import router as player_router
from .settings_routes import router as settings_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(library_router)
api_router.include_router(player_router)
api_router.include_router(activity_router)
api_router.include_router(settings_router)
api_router.include_router(dashboard_router)

__all__ = ["api_router"]
