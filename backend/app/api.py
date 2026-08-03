from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .auth import current_user, require_mochi
from .core import AuthenticationError
from .media import MediaService
from .repositories import ActivityRepository, UserRepository
from .scanner import IMAGE_EXTENSIONS


class LoginPayload(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)


class UserPayload(BaseModel):
    username: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9._-]+$")
    password: str = Field(min_length=12, max_length=256)
    role: str = Field(default="e-mochi", pattern=r"^(mochi|e-mochi)$")


class ProgressPayload(BaseModel):
    episode_id: str = Field(min_length=1, max_length=200)
    anime_id: str = Field(min_length=1, max_length=200)
    season_number: int = Field(ge=1)
    episode_number: int = Field(ge=1)
    playback_position: float = Field(ge=0)
    completed: bool = False


class FavoritePayload(BaseModel):
    enabled: bool = True


class SettingsPayload(BaseModel):
    values: dict[str, str] = Field(default_factory=dict)


class ConfigPayload(BaseModel):
    library_paths: list[str] = Field(default_factory=list)
    language: str = Field(default="hi", pattern=r"^(hi|en|ja)$")


class AnimeEditPayload(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    poster: str | None = Field(default=None, max_length=500)
    banner: str | None = Field(default=None, max_length=500)


class EpisodeEditPayload(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)


class LocalizationPayload(BaseModel):
    values: dict[str, str]


def success(data: Any) -> dict[str, Any]:
    return {"success": True, "data": data}


def media_file(media: MediaService, path: str) -> FileResponse:
    candidate = media.validated_path(path)
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="Media file not found")
    return FileResponse(candidate, media_type=media.media_type(path))


router = APIRouter(prefix="/api/v1")


@router.post("/auth/login")
def login(payload: LoginPayload, request: Request, response: Response):
    try:
        session_id = request.app.state.auth.login(payload.username, payload.password)
    except AuthenticationError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    response.set_cookie(
        request.app.state.auth.cookie_name,
        session_id,
        httponly=True,
        samesite="strict",
        max_age=request.app.state.settings.session_days * 86400,
    )
    return success({"authenticated": True})


@router.post("/auth/logout")
def logout(request: Request, response: Response):
    request.app.state.auth.logout(request.cookies.get(request.app.state.auth.cookie_name))
    response.delete_cookie(request.app.state.auth.cookie_name)
    return success({"authenticated": False})


@router.get("/auth/session")
def session(user: Annotated[dict, Depends(current_user)]):
    return success({"id": user["id"], "username": user["username"], "role": user["role"]})


@router.get("/users/me")
def me(user: Annotated[dict, Depends(current_user)]):
    return success({"id": user["id"], "username": user["username"], "role": user["role"]})


@router.get("/users")
def users(request: Request, _: Annotated[dict, Depends(require_mochi)]):
    with request.app.state.database.connect() as db:
        return success(UserRepository(db).list())


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(payload: UserPayload, request: Request, _: Annotated[dict, Depends(require_mochi)]):
    from .auth import PasswordHasher
    with request.app.state.database.connect() as db:
        try:
            user = UserRepository(db).create(payload.username, PasswordHasher.hash(payload.password), payload.role)
        except sqlite3.IntegrityError as error:
            raise HTTPException(status_code=409, detail="Username is already in use") from error
    user.pop("password_hash", None)
    return success(user)


@router.delete("/users/{user_id}")
def delete_user(user_id: int, request: Request, current: Annotated[dict, Depends(require_mochi)]):
    if user_id == current["id"]:
        raise HTTPException(status_code=400, detail="The active administrator cannot be deleted")
    with request.app.state.database.connect() as db:
        deleted = UserRepository(db).delete(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return success({"deleted": True})


@router.get("/library")
def library(request: Request):
    return success(request.app.state.media.library())


@router.get("/library/search")
def search_library(request: Request, query: str = "", filter: str = "all", sort: str = "default"):
    """Search by title, episode, season, or tutorial; filter series/tutorials; sort."""
    if filter not in {"all", "series", "tutorials"} or sort not in {"default", "title", "recent"}:
        raise HTTPException(status_code=422, detail="Unsupported filter or sort value")
    from .media import filter_library
    return success(filter_library(request.app.state.media.library(), query=query, filter_by=filter, sort_by=sort))


@router.get("/library/{anime_id}")
def anime(anime_id: str, request: Request):
    for entry in request.app.state.media.library().get("anime", []):
        if entry["id"] == anime_id:
            return success(entry)
    raise HTTPException(status_code=404, detail="Anime not found")


@router.get("/library/{anime_id}/seasons")
def seasons(anime_id: str, request: Request):
    return success(anime(anime_id, request)["data"].get("seasons", []))


@router.get("/library/{anime_id}/episodes")
def episodes(anime_id: str, request: Request):
    season_list = seasons(anime_id, request)["data"]
    return success([episode for season in season_list for episode in season.get("episodes", [])])


@router.get("/library/{anime_id}/poster")
def poster(anime_id: str, request: Request):
    """Serve an indexed poster image after root validation (D-015)."""
    candidate = request.app.state.media.poster_path(anime_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Poster not available")
    return FileResponse(candidate, media_type="image/webp" if candidate.suffix.lower() == ".webp" else "image/jpeg",
                        headers={"Cache-Control": "public, max-age=86400"})


@router.get("/banners")
def banners(request: Request):
    """List application banners (decorative, no authentication)."""
    return success({"banners": request.app.state.media.banner_list(request.app.state.settings.project_root / "assets")})


def indexed_episode(request: Request, episode_id: str) -> dict:
    """Return an indexed episode or a clean 404 for placeholders without local media.

    Placeholder episodes (metadata-only entries created when media is not yet
    imported) have no video path; they are reported as not available instead of
    failing with an internal error.
    """
    episode = request.app.state.media.find_episode(episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    if not episode.get("video_path"):
        raise HTTPException(status_code=404, detail="Episode media is not available locally")
    return episode


@router.get("/player/source/{episode_id}")
def player_source(episode_id: str, request: Request):
    episode = indexed_episode(request, episode_id)
    return success({
        "episode_id": episode_id,
        "url": f"/api/v1/player/file/{episode_id}",
        "subtitles": [f"/api/v1/player/subtitle/{episode_id}/{index}" for index, _ in enumerate(episode.get("subtitle_paths", []))],
    })


@router.get("/player/file/{episode_id}")
def player_file(episode_id: str, request: Request):
    episode = indexed_episode(request, episode_id)
    return media_file(request.app.state.media, episode["video_path"])


@router.get("/player/subtitle/{episode_id}/{subtitle_index}")
def player_subtitle(episode_id: str, subtitle_index: int, request: Request):
    episode = request.app.state.media.find_episode(episode_id)
    if not episode or subtitle_index < 0 or subtitle_index >= len(episode.get("subtitle_paths", [])):
        raise HTTPException(status_code=404, detail="Subtitle not found")
    return media_file(request.app.state.media, episode["subtitle_paths"][subtitle_index])


@router.post("/player/progress")
def save_progress(payload: ProgressPayload, request: Request, user: Annotated[dict, Depends(current_user)]):
    with request.app.state.database.connect() as db:
        ActivityRepository(db).save_progress(user["id"], payload.model_dump())
    return success({"saved": True})


@router.get("/player/progress/{episode_id}")
def progress(episode_id: str, request: Request, user: Annotated[dict, Depends(current_user)]):
    with request.app.state.database.connect() as db:
        value = ActivityRepository(db).progress(user["id"], episode_id)
    return success(value or {"playback_position": 0})


@router.get("/continue")
def continue_watching(request: Request, user: Annotated[dict, Depends(current_user)]):
    with request.app.state.database.connect() as db:
        return success(ActivityRepository(db).continue_watching(user["id"]))


@router.delete("/continue/{episode_id}")
def delete_continue(episode_id: str, request: Request, user: Annotated[dict, Depends(current_user)]):
    with request.app.state.database.connect() as db:
        ActivityRepository(db).remove_progress(user["id"], episode_id)
    return success({"deleted": True})


@router.get("/favorites")
def favorites(request: Request, user: Annotated[dict, Depends(current_user)]):
    with request.app.state.database.connect() as db:
        return success(ActivityRepository(db).favorites(user["id"]))


@router.post("/favorites/{anime_id}")
def add_favorite(anime_id: str, request: Request, payload: FavoritePayload | None = None, user: Annotated[dict, Depends(current_user)] = None):
    with request.app.state.database.connect() as db:
        ActivityRepository(db).set_favorite(user["id"], anime_id, payload.enabled if payload else True)
    return success({"anime_id": anime_id, "favorite": payload.enabled if payload else True})


@router.delete("/favorites/{anime_id}")
def remove_favorite(anime_id: str, request: Request, user: Annotated[dict, Depends(current_user)]):
    with request.app.state.database.connect() as db:
        ActivityRepository(db).set_favorite(user["id"], anime_id, False)
    return success({"anime_id": anime_id, "favorite": False})


@router.get("/history")
def history(request: Request, user: Annotated[dict, Depends(current_user)]):
    with request.app.state.database.connect() as db:
        return success(ActivityRepository(db).history(user["id"]))


@router.delete("/history")
def clear_history(request: Request, user: Annotated[dict, Depends(current_user)]):
    with request.app.state.database.connect() as db:
        ActivityRepository(db).clear_history(user["id"])
    return success({"cleared": True})


@router.get("/settings")
def get_settings(request: Request, user: Annotated[dict, Depends(current_user)]):
    with request.app.state.database.connect() as db:
        return success(ActivityRepository(db).setting_values(user["id"]))


@router.put("/settings")
def update_settings(payload: SettingsPayload, request: Request, user: Annotated[dict, Depends(current_user)]):
    with request.app.state.database.connect() as db:
        ActivityRepository(db).save_settings(user["id"], payload.values)
    return success(payload.values)


@router.get("/languages")
def languages():
    return success([{"code": "hi", "name": "हिन्दी"}, {"code": "en", "name": "English"}, {"code": "ja", "name": "日本語"}])


@router.post("/language")
def language(payload: SettingsPayload, request: Request, user: Annotated[dict, Depends(current_user)]):
    selected = payload.values.get("language", "hi")
    if selected not in {"hi", "en", "ja"}:
        raise HTTPException(status_code=422, detail="Unsupported language")
    values = {"language": selected}
    with request.app.state.database.connect() as db:
        ActivityRepository(db).save_settings(user["id"], values)
    return success(values)


@router.get("/dashboard")
def dashboard(_: Annotated[dict, Depends(require_mochi)]):
    return success({"available": True})


@router.get("/dashboard/status")
def dashboard_status(request: Request, _: Annotated[dict, Depends(require_mochi)]):
    settings = request.app.state.settings
    library = request.app.state.media.scanner.library()
    anime = library.get("anime", [])
    series = [entry for entry in anime if entry.get("seasons")]
    tutorials = [entry for entry in anime if not entry.get("seasons")]
    episodes = sum(len(season.get("episodes", [])) for entry in anime for season in entry.get("seasons", []))
    with request.app.state.database.connect() as db:
        users = UserRepository(db).count()
    banner_dir = settings.project_root / "assets" / "banners"
    return success({
        "series": len(series),
        "tutorials": len(tutorials),
        "episodes": episodes,
        "users": users,
        "posters": sum(1 for entry in anime if entry.get("poster")),
        "banners": len(list(banner_dir.glob("*.jpg"))) if banner_dir.is_dir() else 0,
        "database_size": settings.database_path.stat().st_size if settings.database_path.exists() else 0,
    })


def resolve_admin_asset_path(request: Request, value: str, anime_folder: str | None) -> str:
    """Resolve an admin-supplied poster/banner path and validate it stays in the library."""
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        base = Path(anime_folder) if anime_folder else request.app.state.settings.media_dir
        candidate = base / candidate
    candidate = candidate.resolve()
    roots = request.app.state.settings.library_roots()
    if not any(candidate == root or root in candidate.parents for root in roots):
        raise HTTPException(status_code=422, detail="Path is outside the configured library folders")
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="Referenced image file not found")
    if candidate.suffix.lower() not in IMAGE_EXTENSIONS:
        raise HTTPException(status_code=422, detail="Unsupported image format")
    return str(candidate)


def save_library(request: Request, library: dict) -> None:
    from .core import write_json
    write_json(request.app.state.settings.library_path, library)


@router.patch("/dashboard/anime/{anime_id}")
def edit_anime(anime_id: str, payload: AnimeEditPayload, request: Request, _: Annotated[dict, Depends(require_mochi)]):
    from .core import read_json
    library = read_json(request.app.state.settings.library_path, {"version": 1, "anime": []})
    for entry in library.get("anime", []):
        if entry.get("id") != anime_id:
            continue
        if payload.title is not None:
            entry["title"] = payload.title
        if payload.description is not None:
            entry["description"] = payload.description
        if payload.poster is not None:
            entry["poster"] = resolve_admin_asset_path(request, payload.poster, entry.get("path")) if payload.poster.strip() else None
        if payload.banner is not None:
            entry["banner"] = resolve_admin_asset_path(request, payload.banner, entry.get("path")) if payload.banner.strip() else None
        save_library(request, library)
        return success(entry)
    raise HTTPException(status_code=404, detail="Anime not found")


@router.patch("/dashboard/episode/{episode_id}")
def edit_episode(episode_id: str, payload: EpisodeEditPayload, request: Request, _: Annotated[dict, Depends(require_mochi)]):
    from .core import read_json
    library = read_json(request.app.state.settings.library_path, {"version": 1, "anime": []})
    for entry in library.get("anime", []):
        for season in entry.get("seasons", []):
            for episode in season.get("episodes", []):
                if episode.get("id") == episode_id:
                    if payload.title is not None:
                        episode["title"] = payload.title
                    save_library(request, library)
                    return success(episode)
    raise HTTPException(status_code=404, detail="Episode not found")


@router.get("/dashboard/localization/{code}")
def get_localization(code: str, request: Request, _: Annotated[dict, Depends(require_mochi)]):
    if code not in {"hi", "en", "ja"}:
        raise HTTPException(status_code=422, detail="Unsupported language")
    from .core import read_json
    path = request.app.state.settings.data_dir / "localization" / f"{code}.json"
    return success(read_json(path, {}))


@router.put("/dashboard/localization/{code}")
def put_localization(code: str, payload: LocalizationPayload, request: Request, _: Annotated[dict, Depends(require_mochi)]):
    if code not in {"hi", "en", "ja"}:
        raise HTTPException(status_code=422, detail="Unsupported language")
    from .core import read_json, write_json
    path = request.app.state.settings.data_dir / "localization" / f"{code}.json"
    current = read_json(path, {})
    current.update(payload.values)
    write_json(path, current)
    return success({"code": code, "keys": len(current)})


@router.post("/dashboard/database/refresh")
def refresh_database(request: Request, _: Annotated[dict, Depends(require_mochi)]):
    from .maintenance import prune_dangling_references
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


@router.post("/dashboard/library/scan")
def scan(request: Request, _: Annotated[dict, Depends(require_mochi)]):
    return success(request.app.state.media.scan())


@router.post("/dashboard/library/reload")
def reload_library(request: Request, _: Annotated[dict, Depends(require_mochi)]):
    return success(request.app.state.media.scan())


@router.get("/dashboard/config")
def get_config(request: Request, _: Annotated[dict, Depends(require_mochi)]):
    settings = request.app.state.settings
    return success({"library_paths": settings.library_paths, "language": settings.default_language})


@router.get("/dashboard/library")
def dashboard_library(request: Request, _: Annotated[dict, Depends(require_mochi)]):
    """Raw library metadata (with paths) for administrator management only."""
    from .core import read_json
    return success(read_json(request.app.state.settings.library_path, {"version": 1, "anime": []}))


@router.post("/dashboard/config")
def update_config(payload: ConfigPayload, request: Request, _: Annotated[dict, Depends(require_mochi)]):
    settings = request.app.state.settings
    settings.library_paths = payload.library_paths
    settings.default_language = payload.language
    settings.save()
    return success({"library_paths": settings.library_paths, "language": settings.default_language})


@router.post("/dashboard/thumbnails")
def thumbnails(_: Annotated[dict, Depends(require_mochi)]):
    return success({"generated": 0, "message": "Run scripts/generate_thumbnails.py after adding media; generated thumbnails are discovered by the scanner."})


@router.get("/health")
def health(request: Request):
    return success({"status": "ok", "database": request.app.state.settings.database_path.exists()})


@router.get("/version")
def version(request: Request):
    return success({"name": "Hibiki", "version": request.app.state.settings.version})
