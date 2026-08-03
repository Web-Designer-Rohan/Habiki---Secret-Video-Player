"""Dashboard routes (unlocked mode only): status, library management,
metadata editing, scanning, database maintenance, configuration."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from ..auth import require_unlocked
from ..maintenance import prune_dangling_references
from ..payloads import AnimeEditPayload, ConfigPayload, success
from .common import load_library

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(_: Annotated[bool, Depends(require_unlocked)]):
    return success({"available": True})


@router.get("/status")
def dashboard_status(request: Request, _: Annotated[bool, Depends(require_unlocked)]):
    settings = request.app.state.settings
    library = request.app.state.media.scanner.library()
    entries = library.get("entries", [])
    episodes = sum(len(season.get("episodes", [])) for entry in entries for season in entry.get("seasons", []))
    episodes += sum(len(entry.get("episodes", [])) for entry in entries)
    counts = {entry_type: sum(1 for entry in entries if entry.get("type") == entry_type)
              for entry_type in ("anime", "movies", "tutorials", "other")}
    return success({
        **counts,
        "episodes": episodes,
        "posters": sum(1 for entry in entries if entry.get("poster")),
        "banners": sum(1 for entry in entries if entry.get("banner")),
        "database_size": settings.database_path.stat().st_size if settings.database_path.exists() else 0,
    })


@router.patch("/anime/{anime_id}")
def edit_anime(anime_id: str, payload: AnimeEditPayload, request: Request, _: Annotated[bool, Depends(require_unlocked)]):
    """Persist metadata edits to the title's ``info.json`` (filesystem source of truth)."""
    media = request.app.state.media
    fields = payload.model_dump(exclude_unset=True)
    library = media.update_metadata(anime_id, fields)
    for entry in library.get("entries", []):
        if entry.get("id") == anime_id:
            return success(entry)
    raise HTTPException(status_code=404, detail="Anime not found")


@router.post("/database/refresh")
def refresh_database(request: Request, _: Annotated[bool, Depends(require_unlocked)]):
    library = request.app.state.media.scanner.library()
    with request.app.state.database.connect() as db:
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        violations = db.execute("PRAGMA foreign_key_check").fetchall()
        repairs = prune_dangling_references(db, library)
    return success({
        "integrity": integrity,
        "foreign_key_violations": len(violations),
        "pruned": len(repairs),
        "repairs": repairs,
    })


@router.post("/library/scan")
def scan(request: Request, _: Annotated[bool, Depends(require_unlocked)]):
    """Start a background library scan; poll /dashboard/scan/status for progress."""
    return success(request.app.state.media.scan_async())


@router.get("/scan/status")
def scan_status(request: Request, _: Annotated[bool, Depends(require_unlocked)]):
    return success(request.app.state.media.scan_status())


@router.get("/config")
def get_config(request: Request, _: Annotated[bool, Depends(require_unlocked)]):
    return success({"media_root": request.app.state.settings.media_root})


@router.get("/library")
def dashboard_library(request: Request, _: Annotated[bool, Depends(require_unlocked)]):
    """Raw library metadata (with paths) for local management only."""
    return success(load_library(request))


@router.post("/config")
def update_config(payload: ConfigPayload, request: Request, _: Annotated[bool, Depends(require_unlocked)]):
    settings = request.app.state.settings
    media_root = payload.media_root.strip()
    if media_root in (".", "..") or "\x00" in media_root:
        raise HTTPException(status_code=422, detail="Invalid media root")
    settings.media_root = media_root
    settings.save()
    settings.media_dir.mkdir(parents=True, exist_ok=True)
    request.app.state.media.scan_async()
    return success({"media_root": settings.media_root})


@router.post("/thumbnails")
def thumbnails(_: Annotated[bool, Depends(require_unlocked)]):
    return success({"generated": 0, "message": "Run scripts/generate_thumbnails.py after adding media; generated thumbnails are discovered by the scanner."})
