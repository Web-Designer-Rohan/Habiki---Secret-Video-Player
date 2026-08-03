"""Shared helpers for the API routers."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse

from ..core import read_json
from ..media import MediaService
from ..payloads import success

__all__ = ["success", "media_file", "indexed_episode", "get_anime_entry", "load_library"]


def media_file(media: MediaService, path: str) -> FileResponse:
    candidate = media.validated_path(path)
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="Media file not found")
    return FileResponse(candidate, media_type=media.media_type(path))


def get_anime_entry(request: Request, anime_id: str) -> dict[str, Any]:
    for entry in request.app.state.media.library().get("entries", []):
        if entry["id"] == anime_id:
            return entry
    raise HTTPException(status_code=404, detail="Anime not found")


def indexed_episode(request: Request, episode_id: str) -> dict[str, Any]:
    """Return an indexed episode or a clean 404 for entries without local media.

    Metadata-only entries (created before media was scanned in) have no video
    path; they are reported as not available instead of failing with an
    internal error.
    """
    episode = request.app.state.media.find_episode(episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    if not episode.get("video_path"):
        raise HTTPException(status_code=404, detail="Episode media is not available locally")
    return episode


def load_library(request: Request) -> dict[str, Any]:
    return read_json(request.app.state.settings.library_path, {"version": 2, "entries": []})
