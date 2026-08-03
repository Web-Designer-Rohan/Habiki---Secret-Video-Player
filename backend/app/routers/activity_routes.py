"""Activity routes: continue watching, favorites, watch history."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from ..auth import require_unlocked
from ..payloads import FavoritePayload, success
from ..repositories import ActivityRepository

router = APIRouter(prefix="/api/v1", tags=["activity"])


@router.get("/continue")
def continue_watching(request: Request, _: Annotated[bool, Depends(require_unlocked)]):
    with request.app.state.database.connect() as db:
        return success(ActivityRepository(db).continue_watching())


@router.delete("/continue/{episode_id}")
def delete_continue(episode_id: str, request: Request, _: Annotated[bool, Depends(require_unlocked)]):
    with request.app.state.database.connect() as db:
        ActivityRepository(db).remove_progress(episode_id)
    return success({"deleted": True})


@router.get("/favorites")
def favorites(request: Request, _: Annotated[bool, Depends(require_unlocked)]):
    with request.app.state.database.connect() as db:
        return success(ActivityRepository(db).favorites())


@router.post("/favorites/{anime_id}")
def add_favorite(anime_id: str, request: Request, _: Annotated[bool, Depends(require_unlocked)], payload: FavoritePayload | None = None):
    with request.app.state.database.connect() as db:
        ActivityRepository(db).set_favorite(anime_id, payload.enabled if payload else True)
    return success({"anime_id": anime_id, "favorite": payload.enabled if payload else True})


@router.delete("/favorites/{anime_id}")
def remove_favorite(anime_id: str, request: Request, _: Annotated[bool, Depends(require_unlocked)]):
    with request.app.state.database.connect() as db:
        ActivityRepository(db).set_favorite(anime_id, False)
    return success({"anime_id": anime_id, "favorite": False})


@router.get("/history")
def history(request: Request, _: Annotated[bool, Depends(require_unlocked)]):
    with request.app.state.database.connect() as db:
        return success(ActivityRepository(db).history())


@router.delete("/history")
def clear_history(request: Request, _: Annotated[bool, Depends(require_unlocked)]):
    with request.app.state.database.connect() as db:
        ActivityRepository(db).clear_history()
    return success({"cleared": True})
