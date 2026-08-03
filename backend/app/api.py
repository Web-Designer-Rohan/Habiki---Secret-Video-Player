"""API entry point.

Route handlers now live in backend/app/routers/; this module aggregates them
and re-exports the request payloads for backward compatibility (tests import
UnlockPayload from here).
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from .core import VERSION
from .payloads import (
    AnimeEditPayload,
    ConfigPayload,
    FavoritePayload,
    PasswordPayload,
    ProgressPayload,
    SettingsPayload,
    UnlockPayload,
    success,
)
from .routers import api_router

router: APIRouter = api_router


@router.get("/api/v1/health")
def health(request: Request):
    return success({"status": "ok", "database": request.app.state.settings.database_path.exists()})


@router.get("/api/v1/version")
def version(request: Request):
    return success({"name": "Hibiki", "version": VERSION})


__all__ = [
    "router",
    "UnlockPayload",
    "PasswordPayload",
    "ProgressPayload",
    "FavoritePayload",
    "SettingsPayload",
    "ConfigPayload",
    "AnimeEditPayload",
]
