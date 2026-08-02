from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import HTTPException

from .core import Settings
from .scanner import LibraryScanner


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

    def validated_path(self, path: str) -> Path:
        candidate = Path(path).expanduser().resolve()
        if not any(candidate == root or root in candidate.parents for root in self.settings.library_roots()):
            raise HTTPException(status_code=404, detail="Media file is outside the configured library paths")
        return candidate
