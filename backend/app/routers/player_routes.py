"""Player routes: source manifest, media files, subtitles, progress."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, Response

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
        "thumbnail": f"/api/v1/player/thumbnail/{episode_id}",
        "subtitles": [f"/api/v1/player/subtitle/{episode_id}/{index}" for index, _ in enumerate(episode.get("subtitle_paths", []))],
    })


@router.get("/file/{episode_id}")
def player_file(episode_id: str, request: Request):
    episode = indexed_episode(request, episode_id)
    return media_file(request.app.state.media, episode["video_path"])


@router.get("/thumbnail/{episode_id}")
def player_thumbnail(episode_id: str, request: Request):
    candidate = request.app.state.media.thumbnail_path(episode_id)
    if candidate is None:
        # Keep the player useful for media without a thumbnail or title poster.
        # The fallback is generated locally and never depends on a network asset.
        placeholder = """<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 16 9\"><rect width=\"16\" height=\"9\" fill=\"#181818\"/><path d=\"M7.5 3.5 11 5.75 7.5 8z\" fill=\"#c51f3a\"/></svg>"""
        return Response(placeholder, media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=86400"})
    media_type = {
        ".webp": "image/webp",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }[candidate.suffix.lower()]
    return FileResponse(candidate, media_type=media_type, headers={"Cache-Control": "public, max-age=86400"})


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
