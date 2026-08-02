from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .core import Settings, read_json, write_json


SEASON_PATTERN = re.compile(r"(?:season|s)\s*[_-]?\s*(\d+)", re.IGNORECASE)
EPISODE_PATTERN = re.compile(r"(?:episode|ep|e)\s*[_-]?\s*(\d+)", re.IGNORECASE)
VIDEO_EXTENSIONS = {".mp4"}
SUBTITLE_EXTENSIONS = {".vtt"}
IMAGE_EXTENSIONS = {".webp", ".png", ".jpg", ".jpeg"}


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "untitled"


def number_from(pattern: re.Pattern[str], value: str, default: int = 1) -> int:
    match = pattern.search(value)
    return int(match.group(1)) if match else default


def matching_asset(directory: Path, stem: str, extensions: set[str]) -> str | None:
    for candidate in directory.iterdir():
        if candidate.is_file() and candidate.suffix.lower() in extensions and candidate.stem.lower() == stem.lower():
            return str(candidate)
    return None


class LibraryScanner:
    def __init__(self, settings: Settings, logger):
        self.settings = settings
        self.logger = logger

    def scan(self) -> dict[str, Any]:
        roots = self.settings.library_roots()
        anime_entries: list[dict[str, Any]] = []
        for root in roots:
            if not root.exists():
                self.logger.warning("Library path does not exist: %s", root)
                continue
            anime_entries.extend(self._scan_root(root))
        library = {"version": 1, "scanned_at": datetime.now(timezone.utc).isoformat(), "anime": anime_entries}
        write_json(self.settings.library_path, library)
        self.logger.info("Library scan complete: %d anime", len(anime_entries))
        return library

    def _scan_root(self, root: Path) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for anime_dir in sorted((path for path in root.iterdir() if path.is_dir()), key=lambda path: path.name.lower()):
            seasons = self._scan_seasons(anime_dir)
            if not seasons:
                continue
            entry = {
                "id": slugify(anime_dir.name),
                "title": anime_dir.name,
                "path": str(anime_dir),
                "poster": self._named_image(anime_dir, "poster"),
                "banner": self._named_image(anime_dir, "banner"),
                "seasons": seasons,
            }
            entries.append(entry)
        return entries

    def _scan_seasons(self, anime_dir: Path) -> list[dict[str, Any]]:
        seasons: list[dict[str, Any]] = []
        season_dirs = [path for path in anime_dir.iterdir() if path.is_dir() and SEASON_PATTERN.search(path.name)]
        for season_dir in sorted(season_dirs, key=lambda path: number_from(SEASON_PATTERN, path.name)):
            episodes = []
            for video in sorted(season_dir.iterdir(), key=lambda path: path.name.lower()):
                if video.suffix.lower() not in VIDEO_EXTENSIONS:
                    continue
                episode_number = number_from(EPISODE_PATTERN, video.stem)
                episode_id = f"{slugify(anime_dir.name)}-s{number_from(SEASON_PATTERN, season_dir.name):02d}-e{episode_number:02d}"
                episodes.append({
                    "id": episode_id,
                    "number": episode_number,
                    "title": video.stem,
                    "video_path": str(video),
                    "subtitle_paths": self._subtitles(video),
                    "thumbnail_path": matching_asset(season_dir, video.stem, IMAGE_EXTENSIONS),
                })
            if episodes:
                seasons.append({"number": number_from(SEASON_PATTERN, season_dir.name), "episodes": episodes})
        return seasons

    @staticmethod
    def _named_image(directory: Path, name: str) -> str | None:
        return matching_asset(directory, name, IMAGE_EXTENSIONS)

    @staticmethod
    def _subtitles(video: Path) -> list[str]:
        return [str(candidate) for candidate in sorted(video.parent.iterdir())
                if candidate.is_file() and candidate.suffix.lower() in SUBTITLE_EXTENSIONS
                and candidate.stem.lower().startswith(video.stem.lower())]

    def library(self) -> dict[str, Any]:
        return read_json(self.settings.library_path, {"version": 1, "anime": []})
