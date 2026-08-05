from __future__ import annotations

import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from .core import Settings, write_json
from .media_formats import MEDIA_TYPES
from .scanner import CATEGORY_TYPES, IMAGE_EXTENSIONS, LibraryScanner, ScanState

VALID_CATEGORIES = {"all", *CATEGORY_TYPES}
VALID_SORTS = {"default", "title", "recent"}


def filter_library(library_data: dict[str, Any], query: str = "", category: str = "all", sort_by: str = "default") -> dict[str, Any]:
    """Search, filter, and sort the public library in one pass.

    - ``query`` matches entry titles, episode titles/numbers, and season
      numbers (case-insensitive).
    - ``category`` is one of "all", "anime", "movies", "tutorials", "other", "tv-shows", "courses".
    - ``sort_by`` is "default" (canonical order), "title", or "recent"
      (reverse canonical order: newest scanned entries first).

    Pure function so it can be unit tested without a server.
    """
    entries = list(library_data.get("entries", []))
    normalized = query.casefold().strip()

    if category != "all":
        entries = [entry for entry in entries if entry.get("type") == category]

    if normalized:
        matched: list[dict[str, Any]] = []
        for entry in entries:
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
                continue
            standalone_hits = [
                episode for episode in entry.get("episodes", [])
                if normalized in episode.get("title", "").casefold()
                or str(episode.get("number", "")) == normalized
            ]
            if standalone_hits:
                matched.append({**entry, "episodes": standalone_hits})
        entries = matched

    if sort_by == "title":
        entries = sorted(entries, key=lambda entry: entry.get("title", "").casefold())
    elif sort_by == "recent":
        entries = list(reversed(entries))

    return {**library_data, "entries": entries}


class MediaService:
    def __init__(self, settings: Settings, scanner: LibraryScanner):
        self.settings = settings
        self.scanner = scanner
        self.scan_state = ScanState()
        self._scan_thread: threading.Thread | None = None
        self._cached_library: dict[str, Any] | None = None
        self._cache_key: tuple[int, int] | None = None
        self._episode_index: dict[str, dict[str, Any]] = {}
        self._poster_index: dict[str, str | None] = {}
        self._banner_index: dict[str, str | None] = {}

    def library(self) -> dict[str, Any]:
        return self.public_library(self._load_library())

    def scan(self) -> dict[str, Any]:
        """Synchronous full scan (used at startup and in tests)."""
        library = self.scanner.scan(self.scan_state)
        self._cached_library = library
        self._cache_key = None
        self._rebuild_indexes()
        return self.public_library(library)

    def scan_async(self) -> dict[str, Any]:
        """Start a background scan without blocking the request.

        Returns the current scan state; clients poll ``scan_status()`` until
        the scan finishes. A scan that is already running is not restarted.
        """
        if self.scan_state.status == "scanning":
            return self.scan_status()
        # Publish the in-progress state before starting the worker. A small
        # scan can otherwise finish between Thread.start() and the response,
        # making callers believe no scan occurred.
        self.scan_state.status = "scanning"
        self.scan_state.started_at = datetime.now(timezone.utc).isoformat()
        initial_status = self.scan_status()
        self._scan_thread = threading.Thread(target=self.scan, daemon=True)
        self._scan_thread.start()
        return initial_status

    def scan_status(self) -> dict[str, Any]:
        return self.scan_state.snapshot()

    def _invalidate(self) -> None:
        self._cache_key = None
        self._load_library()

    def _load_library(self) -> dict[str, Any]:
        """Parse library.json at most once per file change (mtime+size key).

        Keeps repeated API calls (search, player source, posters) off the disk
        until a scan or metadata edit actually rewrites the file.
        """
        path = self.settings.library_path
        try:
            stat = path.stat()
            key = (stat.st_mtime_ns, stat.st_size)
        except OSError:
            key = None
        if key is None or key != self._cache_key:
            self._cached_library = self.scanner.library()
            self._cache_key = key
            self._rebuild_indexes()
        return self._cached_library

    def _rebuild_indexes(self) -> None:
        episodes: dict[str, dict[str, Any]] = {}
        posters: dict[str, str | None] = {}
        banners: dict[str, str | None] = {}
        for entry in self._cached_library.get("entries", []):
            posters[entry.get("id", "")] = entry.get("poster")
            banners[entry.get("id", "")] = entry.get("banner")
            for season in entry.get("seasons", []):
                for episode in season.get("episodes", []):
                    episodes[episode["id"]] = episode
            for episode in entry.get("episodes", []):
                episodes[episode["id"]] = episode
        self._episode_index = episodes
        self._poster_index = posters
        self._banner_index = banners

    def find_episode(self, episode_id: str) -> dict[str, Any] | None:
        self._load_library()
        return self._episode_index.get(episode_id)

    def find_entry(self, entry_id: str) -> dict[str, Any] | None:
        for entry in self._load_library().get("entries", []):
            if entry.get("id") == entry_id:
                return entry
        return None

    @staticmethod
    def _public_episode(episode_entry: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in episode_entry.items()
                if key not in {"video_path", "subtitle_paths", "thumbnail_path"}}

    @staticmethod
    def public_library(library_data: dict[str, Any]) -> dict[str, Any]:
        """Remove local filesystem paths before library metadata crosses the API boundary."""
        public_data = {key: value for key, value in library_data.items() if key != "entries"}
        public_entries = []
        for entry in library_data.get("entries", []):
            public_entry = {key: value for key, value in entry.items()
                            if key not in {"path", "poster", "banner", "seasons", "episodes"}}
            public_entry["seasons"] = []
            for season in entry.get("seasons", []):
                season_copy = {key: value for key, value in season.items() if key != "episodes"}
                season_copy["episodes"] = [MediaService._public_episode(episode) for episode in season.get("episodes", [])]
                public_entry["seasons"].append(season_copy)
            public_entry["episodes"] = [MediaService._public_episode(episode) for episode in entry.get("episodes", [])]
            public_entries.append(public_entry)
        public_data["entries"] = public_entries
        return public_data

    def validated_path(self, path: str, allowed_extensions: set[str] | None = None) -> Path:
        candidate = Path(path).expanduser().resolve()
        root = self.settings.media_dir.resolve()
        if candidate != root and root not in candidate.parents:
            raise HTTPException(status_code=404, detail="Media file is outside the configured media root")
        extensions = allowed_extensions or set(MEDIA_TYPES)
        if candidate.suffix.lower() not in extensions:
            raise HTTPException(status_code=404, detail="Unsupported media format")
        return candidate

    def media_type(self, path: str) -> str:
        candidate = self.validated_path(path)
        return MEDIA_TYPES[candidate.suffix.lower()]

    def _asset_path(self, entry_id: str, index_attribute: str) -> Path | None:
        """Resolve an indexed poster/banner after root validation, or None."""
        self._load_library()
        value = getattr(self, index_attribute).get(entry_id)
        if not value:
            return None
        try:
            candidate = self.validated_path(value, allowed_extensions=set(IMAGE_EXTENSIONS))
        except HTTPException:
            return None
        return candidate if candidate.is_file() else None

    def poster_path(self, entry_id: str) -> Path | None:
        return self._asset_path(entry_id, "_poster_index")

    def banner_path(self, entry_id: str) -> Path | None:
        return self._asset_path(entry_id, "_banner_index")

    def thumbnail_path(self, episode_id: str) -> Path | None:
        """Resolve an indexed episode thumbnail, falling back to its title poster."""
        episode = self.find_episode(episode_id)
        if not episode:
            return None
        thumbnail = episode.get("thumbnail_path")
        if thumbnail:
            try:
                candidate = self.validated_path(thumbnail, allowed_extensions=set(IMAGE_EXTENSIONS))
            except HTTPException:
                candidate = None
            if candidate is not None and candidate.is_file():
                return candidate
        for entry in self._load_library().get("entries", []):
            episodes = [
                *[episode_item for season in entry.get("seasons", []) for episode_item in season.get("episodes", [])],
                *entry.get("episodes", []),
            ]
            if any(item.get("id") == episode_id for item in episodes):
                return self.poster_path(entry.get("id", ""))
        return None

    def update_metadata(self, entry_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        """Persist metadata edits to ``info.json`` (the source of truth).

        The change is also applied to the cached library.json so the UI sees
        the edit immediately; the next scan keeps it because info.json wins
        over filename-derived values.
        """
        entry = self.find_entry(entry_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="Entry not found")
        info_path = Path(entry["path"]) / "info.json"
        stored: dict[str, Any] = {}
        if info_path.is_file():
            try:
                loaded = __import__("json").loads(info_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    stored = loaded
            except (OSError, ValueError):
                stored = {}
        stored.update({key: value for key, value in fields.items() if value is not None})
        stored = {key: value for key, value in stored.items() if value != ""}
        write_json(info_path, stored)
        library = self._load_library()
        for current in library.get("entries", []):
            if current.get("id") == entry_id:
                for key in ("title", "description", "year", "genre", "studio"):
                    if key in fields:
                        if fields[key] in (None, ""):
                            current.pop(key, None)
                        else:
                            current[key] = fields[key]
                break
        write_json(self.settings.library_path, library)
        self._invalidate()
        return self.public_library(library)

    @staticmethod
    def banner_list(assets_dir: Path) -> list[dict[str, str]]:
        """List application banners as public asset URLs for the welcome screen."""
        directory = assets_dir / "banners"
        if not directory.is_dir():
            return []
        return [
            {"name": path.name, "url": f"/assets/banners/{path.name}"}
            for path in sorted(directory.iterdir())
            if path.is_file() and path.suffix in {".jpg", ".png"}
        ]
