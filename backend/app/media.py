from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import HTTPException

from .core import Settings
from .scanner import IMAGE_EXTENSIONS, LibraryScanner


MEDIA_TYPES = {".mp4": "video/mp4", ".vtt": "text/vtt"}


def filter_library(library_data: dict[str, Any], query: str = "", filter_by: str = "all", sort_by: str = "default") -> dict[str, Any]:
    """Search, filter, and sort the public library in one pass.

    - ``query`` matches anime titles, episode titles/numbers, season numbers, and
      tutorial titles (case-insensitive).
    - ``filter_by`` is one of "all", "series", "tutorials".
    - ``sort_by`` is "default" (manifest order), "title", or "recent"
      (reverse manifest order: newest imported entries first).

    Pure function so it can be unit tested without a server.
    """
    anime_list = list(library_data.get("anime", []))
    normalized = query.casefold().strip()

    if filter_by == "series":
        anime_list = [entry for entry in anime_list if entry.get("seasons")]
    elif filter_by == "tutorials":
        anime_list = [entry for entry in anime_list if not entry.get("seasons")]

    if normalized:
        matched: list[dict[str, Any]] = []
        for entry in anime_list:
            if normalized in entry.get("title", "").casefold():
                matched.append(entry)
                continue
            matched_seasons: list[dict[str, Any]] = []
            for season in entry.get("seasons", []):
                season_number = season.get("number")
                if normalized == str(season_number) or normalized == f"s{int(season_number):02d}":
                    matched_seasons.append(season)
                    continue
                hits = [
                    episode for episode in season.get("episodes", [])
                    if normalized in episode.get("title", "").casefold()
                    or str(episode.get("number", "")) == normalized
                ]
                if hits:
                    matched_seasons.append({**season, "episodes": hits})
            if matched_seasons:
                matched.append({**entry, "seasons": matched_seasons})
        anime_list = matched

    if sort_by == "title":
        anime_list = sorted(anime_list, key=lambda entry: entry.get("title", "").casefold())
    elif sort_by == "recent":
        anime_list = list(reversed(anime_list))

    return {**library_data, "anime": anime_list}


class MediaService:
    def __init__(self, settings: Settings, scanner: LibraryScanner):
        self.settings = settings
        self.scanner = scanner

    def library(self) -> dict[str, Any]:
        return self.public_library(self.scanner.library())

    def scan(self) -> dict[str, Any]:
        return self.public_library(self.scanner.scan())

    def find_episode(self, episode_id: str) -> dict[str, Any] | None:
        for anime_entry in self.scanner.library().get("anime", []):
            for season_entry in anime_entry.get("seasons", []):
                for episode in season_entry.get("episodes", []):
                    if episode["id"] == episode_id:
                        return episode
        return None

    @staticmethod
    def public_library(library_data: dict[str, Any]) -> dict[str, Any]:
        """Remove local filesystem paths before library metadata crosses the API boundary."""
        public_data = {key: value for key, value in library_data.items() if key != "anime"}
        public_anime = []
        for anime_entry in library_data.get("anime", []):
            anime = {key: value for key, value in anime_entry.items()
                     if key not in {"path", "poster", "banner", "seasons"}}
            anime["seasons"] = []
            for season_entry in anime_entry.get("seasons", []):
                season = {key: value for key, value in season_entry.items() if key != "episodes"}
                season["episodes"] = []
                for episode_entry in season_entry.get("episodes", []):
                    episode = {key: value for key, value in episode_entry.items()
                               if key not in {"video_path", "subtitle_paths", "thumbnail_path"}}
                    season["episodes"].append(episode)
                anime["seasons"].append(season)
            public_anime.append(anime)
        public_data["anime"] = public_anime
        return public_data

    def validated_path(self, path: str, allowed_extensions: set[str] | None = None) -> Path:
        candidate = Path(path).expanduser().resolve()
        if not any(candidate == root or root in candidate.parents for root in self.settings.library_roots()):
            raise HTTPException(status_code=404, detail="Media file is outside the configured library paths")
        extensions = allowed_extensions or set(MEDIA_TYPES)
        if candidate.suffix.lower() not in extensions:
            raise HTTPException(status_code=404, detail="Unsupported media format")
        return candidate

    def media_type(self, path: str) -> str:
        candidate = self.validated_path(path)
        return MEDIA_TYPES[candidate.suffix.lower()]

    def poster_path(self, anime_id: str) -> Path | None:
        """Return the indexed poster for an anime after root validation, or None."""
        for entry in self.scanner.library().get("anime", []):
            if entry.get("id") == anime_id:
                poster = entry.get("poster")
                if not poster:
                    return None
                try:
                    candidate = self.validated_path(poster, allowed_extensions=set(IMAGE_EXTENSIONS))
                except HTTPException:
                    return None
                return candidate if candidate.is_file() else None
        return None

    @staticmethod
    def banner_list(assets_dir: Path) -> list[dict[str, str]]:
        """List application banners as public asset URLs for the welcome screen."""
        directory = assets_dir / "banners"
        if not directory.is_dir():
            return []
        return [
            {"name": path.name, "url": f"/assets/banners/{path.name}"}
            for path in sorted(directory.glob("*.jpg"))
        ]
