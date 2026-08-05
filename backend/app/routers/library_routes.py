"""Public library routes: browsing, search, posters, banners."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse


def image_media_type(path):
    return {
        ".webp": "image/webp",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }[path.suffix.lower()]

from ..media import VALID_CATEGORIES, VALID_SORTS, filter_library
from ..payloads import success
from .common import get_anime_entry

router = APIRouter(prefix="/api/v1", tags=["library"])


@router.get("/library")
def library(request: Request, query: str = "", category: str = "all", sort: str = "default"):
    """Browse the library with optional search, category, and sort parameters."""
    if category not in VALID_CATEGORIES or sort not in VALID_SORTS:
        raise HTTPException(status_code=422, detail="Unsupported category or sort value")
    return success(filter_library(request.app.state.media.library(), query=query, category=category, sort_by=sort))


@router.get("/library/search")
def search_library(request: Request, query: str = "", category: str = "all", sort: str = "default"):
    """Alias of GET /library kept for compatibility."""
    if category not in VALID_CATEGORIES or sort not in VALID_SORTS:
        raise HTTPException(status_code=422, detail="Unsupported category or sort value")
    return success(filter_library(request.app.state.media.library(), query=query, category=category, sort_by=sort))


@router.get("/library/{anime_id}")
def anime(anime_id: str, request: Request):
    return success(get_anime_entry(request, anime_id))


@router.get("/library/{anime_id}/seasons")
def seasons(anime_id: str, request: Request):
    return success(get_anime_entry(request, anime_id).get("seasons", []))


@router.get("/library/{anime_id}/episodes")
def episodes(anime_id: str, request: Request):
    entry = get_anime_entry(request, anime_id)
    season_list = entry.get("seasons", [])
    return success([episode for season in season_list for episode in season.get("episodes", [])]
                   + entry.get("episodes", []))


@router.get("/library/{anime_id}/poster")
def poster(anime_id: str, request: Request):
    """Serve an indexed poster image after root validation (D-015)."""
    candidate = request.app.state.media.poster_path(anime_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Poster not available")
    return FileResponse(candidate, media_type=image_media_type(candidate),
                        headers={"Cache-Control": "public, max-age=86400"})


@router.get("/library/{anime_id}/banner")
def banner(anime_id: str, request: Request):
    """Serve an indexed banner image after root validation."""
    candidate = request.app.state.media.banner_path(anime_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Banner not available")
    return FileResponse(candidate, media_type=image_media_type(candidate),
                        headers={"Cache-Control": "public, max-age=86400"})


@router.get("/banners")
def banners(request: Request):
    """List application banners (decorative, no authentication)."""
    return success({"banners": request.app.state.media.banner_list(request.app.state.settings.project_root / "assets")})
