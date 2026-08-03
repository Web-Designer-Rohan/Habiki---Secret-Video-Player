"""Player routes: source manifest, media files, subtitles, progress."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from ..auth import require_unlocked
from ..payloads import ProgressPayload, success
from ..repositories import ActivityRepository
from .common import indexed_episode, media_file

router = APIRouter(prefix="/api/v1/player", tags=["player"])


@router.get("/source/{episode_id}")
def player_source(episode_id: str, request: Request):
    episode = indexed_episode(request, episode_id)
    return success({
        "episode_id": episode_id,
        "url": f"/api/v1/player/file/{episode_id}",
        "subtitles": [f"/api/v1/player/subtitle/{episode_id}/{index}" for index, _ in enumerate(episode.get("subtitle_paths", []))],
    })


@router.get("/file/{episode_id}")
def player_file(episode_id: str, request: Request):
    episode = indexed_episode(request, episode_id)
    return media_file(request.app.state.media, episode["video_path"])


@router.get("/subtitle/{episode_id}/{subtitle_index}")
def player_subtitle(episode_id: str, subtitle_index: int, request: Request):
    episode = request.app.state.media.find_episode(episode_id)
    if not episode or subtitle_index < 0 or subtitle_index >= len(episode.get("subtitle_paths", [])):
        raise HTTPException(status_code=404, detail="Subtitle not found")
    return media_file(request.app.state.media, episode["subtitle_paths"][subtitle_index])


@router.post("/progress")
def save_progress(payload: ProgressPayload, request: Request, _: Annotated[bool, Depends(require_unlocked)]):
    with request.app.state.database.connect() as db:
        ActivityRepository(db).save_progress(payload.model_dump())
    return success({"saved": True})


@router.get("/progress/{episode_id}")
def progress(episode_id: str, request: Request, _: Annotated[bool, Depends(require_unlocked)]):
    with request.app.state.database.connect() as db:
        value = ActivityRepository(db).progress(episode_id)
    return success(value or {"playback_position": 0})
