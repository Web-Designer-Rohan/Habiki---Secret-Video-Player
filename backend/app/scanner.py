"""Filesystem library scanner (Hibiki v1).

The filesystem is the single source of truth. The scanner walks one
configurable media root (``Settings.media_root``, default ``contents/``) and
builds ``data/library.json`` as a cache. Content is organized into four
deterministic categories:

    contents/
    ├── Anime/       title folders with season folders + numbered episodes
    ├── Movies/      one video per title (a direct file or a title folder)
    ├── Tutorials/   one video per title (same rules as Movies)
    └── Other/       anything that fits the same standalone rules

Title folders may carry ``poster.*``, ``banner.*`` and an optional
``info.json`` (title, description, year, genre, studio). Episodes may be
named ``1``, ``01 - Title``, ``EP 1``, ``episode 1``, ``E01``, ``S2E5`` or
carry no number at all (ordered by filename instead).

The scan is deterministic (alphabetical traversal, explicit tie-breaks) and
incremental: unchanged videos keep their cached metadata through a
``path -> [mtime_ns, size]`` signature map stored inside library.json.
Problems (missing assets, invalid names, duplicate numbers, unsupported
files, misplaced media) are reported as warnings and never raise.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .core import Settings, read_json, write_json

SEASON_PATTERN = re.compile(r"(?:season|s)\s*[_-]?\s*(\d+)", re.IGNORECASE)
# Accepted episode names: "1", "01 - Title", "EP 1", "episode 1", "E01", "S2E5".
EPISODE_PATTERN = re.compile(r"(?:episode|ep|e)\s*[_-]?\s*(\d+)", re.IGNORECASE)
BARE_NUMBER_PATTERN = re.compile(r"^(\d+)")
VIDEO_EXTENSIONS = {".mp4"}
SUBTITLE_EXTENSIONS = {".vtt"}
IMAGE_EXTENSIONS = {".webp", ".png", ".jpg", ".jpeg"}
INFO_JSON_NAME = "info.json"

# Canonical category order; each name maps to its folder name in the root.
CATEGORY_TYPES = ("anime", "movies", "tutorials", "other")
CATEGORY_DIRS = {"anime": "Anime", "movies": "Movies", "tutorials": "Tutorials", "other": "Other"}
MAX_WARNINGS = 100

METADATA_KEYS = ("title", "description", "year", "genre", "studio")


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "untitled"


def season_number(name: str) -> int | None:
    """Season number from a folder name: ``Season 1``, ``S01``, or a bare ``1``."""
    match = SEASON_PATTERN.search(name)
    if match:
        return int(match.group(1))
    if re.fullmatch(r"\d+", name):
        return int(name)
    return None


def episode_number(stem: str) -> int | None:
    """Episode number from a file stem: ``1`` first, then ``EP 1`` / ``episode 1`` / ``E1``.

    Returns None when the name carries no number; the scanner then falls back
    to sequential ordering instead of guessing.
    """
    match = BARE_NUMBER_PATTERN.match(stem)
    if match:
        return int(match.group(1))
    match = EPISODE_PATTERN.search(stem)
    if match:
        return int(match.group(1))
    # Many real-world releases prefix the title (for example
    # ``My Hero Academia - 01``). Accept a standalone numeric token anywhere
    # in the stem after the explicit marker formats have been checked.
    tokens = re.findall(r"(?:^|[\s._-])(\d{1,3})(?=$|[\s._-])", stem)
    return int(tokens[-1]) if tokens else None


def episode_title(stem: str, number: int) -> str:
    """Human-readable episode title from a file stem.

    Strips leading episode markers (``EP 3 - The Fight`` -> ``The Fight``,
    ``E04`` -> ``Episode 4``) and falls back to ``Episode {number}`` when the
    name carries no title beyond the number.
    """
    name = re.sub(r"^(?:s\d+[._\- ]?e|episode|ep|e)[._\- ]*\d+[._\- ]*", "", stem, flags=re.IGNORECASE)
    name = re.sub(r"^\d+[._\- ]*", "", name)
    name = re.sub(r"[._\-]+", " ", name).strip()
    return name or f"Episode {number}"


def index_directory(directory: Path, extensions: set[str]) -> dict[str, str]:
    """Map ``stem.lower() -> path`` for files of the given extensions.

    Building one dict per directory keeps poster/banner/subtitle lookups O(1)
    instead of re-walking the directory for every file (O(n²) for seasons with
    many episodes).
    """
    indexed: dict[str, str] = {}
    for candidate in directory.iterdir():
        if candidate.is_file() and candidate.suffix.lower() in extensions:
            indexed.setdefault(candidate.stem.lower(), str(candidate))
    return indexed


def read_info_json(directory: Path, state: "ScanState") -> dict[str, Any]:
    """Read optional ``info.json`` metadata from a title directory.

    Only the documented keys survive; values are coerced to simple types and
    invalid files are reported as warnings, never raised.
    """
    info_path = directory / INFO_JSON_NAME
    if not info_path.is_file():
        return {}
    try:
        raw = info_path.read_text(encoding="utf-8")
        loaded = json_loads(raw)
    except (OSError, ValueError) as error:
        state.warn(f"Ignored invalid {INFO_JSON_NAME} in {relative(directory)}: {error}")
        return {}
    if not isinstance(loaded, dict):
        state.warn(f"Ignored {INFO_JSON_NAME} in {relative(directory)}: expected a JSON object")
        return {}
    metadata: dict[str, Any] = {}
    for key in METADATA_KEYS:
        if key not in loaded:
            continue
        value = loaded[key]
        if key == "genre":
            if isinstance(value, str):
                value = [part.strip() for part in value.split(",") if part.strip()]
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                state.warn(f"Ignored invalid genre in {relative(directory)}")
                continue
            value = [item.strip() for item in value if item.strip()]
        elif key == "year":
            try:
                value = int(value)
            except (TypeError, ValueError):
                state.warn(f"Ignored invalid year in {relative(directory)}")
                continue
        elif not isinstance(value, str):
            state.warn(f"Ignored invalid {key} in {relative(directory)}")
            continue
        if value:
            metadata[key] = value
    return metadata


def json_loads(text: str) -> Any:
    import json

    return json.loads(text)


def relative(path: Path) -> str:
    """Project-relative display path for warning messages."""
    try:
        return path.relative_to(Path(__file__).resolve().parents[2]).as_posix()
    except ValueError:
        return str(path)


@dataclass(slots=True)
class ScanState:
    """Progress of the most recent scan, shared between the background thread
    and the status endpoint."""

    status: str = "idle"  # idle | scanning | error
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None
    counts: dict[str, int] = field(
        default_factory=lambda: {"anime": 0, "movies": 0, "tutorials": 0, "other": 0,
                                 "episodes": 0, "posters": 0, "banners": 0}
    )
    warnings: list[str] = field(default_factory=list)

    def warn(self, message: str) -> None:
        if len(self.warnings) < MAX_WARNINGS:
            self.warnings.append(message)

    def snapshot(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error": self.error,
            "counts": dict(self.counts),
            "warnings": list(self.warnings),
        }


class LibraryScanner:
    """Indexes the configured media root into ``data/library.json``."""

    def __init__(self, settings: Settings, logger):
        self.settings = settings
        self.logger = logger
        self._signatures: dict[str, list[int]] = {}

    def scan(self, state: ScanState | None = None) -> dict[str, Any]:
        state = state or ScanState()
        now = datetime.now(timezone.utc).isoformat()
        state.status = "scanning"
        state.started_at = now
        state.error = None
        state.warnings.clear()
        state.counts = dict.fromkeys(state.counts, 0)
        try:
            self._signatures = self._load_previous_signatures()
            entries = self._scan_root(self.settings.media_dir, state)
            for entry in entries:
                self._count_entry(entry, state.counts)
            library = {
                "version": 2,
                "scanned_at": now,
                "media_root": self.settings.media_root,
                "entries": entries,
                "signatures": self._signatures,
            }
            write_json(self.settings.library_path, library)
            self.logger.info("Library scan complete: %d entries, %d episodes, %d warnings",
                             len(entries), state.counts["episodes"], len(state.warnings))
            for warning in state.warnings:
                self.logger.warning(warning)
        except OSError as error:
            state.status = "error"
            state.error = str(error)
            self.logger.error("Library scan failed: %s", error)
            raise
        state.status = "idle"
        state.finished_at = datetime.now(timezone.utc).isoformat()
        return library

    def library(self) -> dict[str, Any]:
        """Read the last scan from the cache without touching the filesystem."""
        try:
            return read_json(self.settings.library_path, {"version": 2, "entries": []})
        except RuntimeError as error:
            self.logger.warning("Library cache could not be read: %s", error)
            return {"version": 2, "entries": []}

    # ------------------------------------------------------------------ cache

    def _load_previous_signatures(self) -> dict[str, list[int]]:
        try:
            cached = self.settings.library_path.read_text(encoding="utf-8")
        except OSError:
            return {}
        try:
            import json

            stored = json.loads(cached)
        except (OSError, ValueError):
            return {}
        signatures = stored.get("signatures", {})
        return signatures if isinstance(signatures, dict) else {}

    def _cached_episodes(self) -> dict[str, dict[str, Any]]:
        """Map ``video_path -> episode`` from the previous cache.

        Only reused when the video's signature is unchanged, so the episode
        identity (id, number, title) is stable across rescans.
        """
        try:
            import json

            cached = json.loads(self.settings.library_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        episodes: dict[str, dict[str, Any]] = {}
        for entry in cached.get("entries", []):
            for season in entry.get("seasons", []):
                for episode in season.get("episodes", []):
                    episodes[episode.get("video_path", "")] = episode
            for episode in entry.get("episodes", []):
                episodes[episode.get("video_path", "")] = episode
        return episodes

    def _reuse_episode(self, video: Path, cached: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
        try:
            stat = video.stat()
            signature = [stat.st_mtime_ns, stat.st_size]
        except OSError:
            return None
        previous = cached.get(str(video))
        if previous is None or self._signatures.get(str(video)) != signature:
            self._signatures[str(video)] = signature
            return None
        return previous

    # ------------------------------------------------------------ root layout

    def _scan_root(self, root: Path, state: ScanState) -> list[dict[str, Any]]:
        if not root.is_dir():
            state.warn(f"Media root does not exist: {relative(root)}")
            return []
        entries: list[dict[str, Any]] = []
        for category in CATEGORY_TYPES:
            category_dir = root / CATEGORY_DIRS[category]
            if not category_dir.is_dir():
                continue
            if category == "anime":
                entries.extend(self._scan_anime(category_dir, state))
            else:
                entries.extend(self._scan_standalone(category_dir, category, state))
        self._warn_misplaced_media(root, state)
        return entries

    def _warn_misplaced_media(self, root: Path, state: ScanState) -> None:
        category_names = {name.casefold() for name in CATEGORY_DIRS.values()}
        for candidate in sorted(root.iterdir(), key=lambda path: path.name.casefold()):
            if candidate.is_dir():
                if candidate.name.casefold() not in category_names:
                    state.warn(f"Ignored unknown folder in media root: {relative(candidate)}")
            elif candidate.is_file():
                state.warn(f"Ignored file in media root (place it inside a category folder): {relative(candidate)}")

    # ----------------------------------------------------------------- anime

    def _scan_anime(self, category_dir: Path, state: ScanState) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        used_ids: set[str] = set()
        for title_dir in sorted((path for path in category_dir.iterdir() if path.is_dir()),
                                key=lambda path: path.name.casefold()):
            seasons = self._scan_seasons(title_dir, state)
            if not seasons:
                state.warn(f"Ignored anime folder without videos: {relative(title_dir)}")
                continue
            info = read_info_json(title_dir, state)
            images = index_directory(title_dir, IMAGE_EXTENSIONS)
            title = info.get("title") or title_dir.name
            entry: dict[str, Any] = {
                "id": self._unique_id(slugify(title), used_ids),
                "type": "anime",
                "title": title,
                "path": str(title_dir),
                "poster": images.get("poster"),
                "banner": images.get("banner"),
                "seasons": seasons,
            }
            entry.update({key: info[key] for key in METADATA_KEYS[1:] if key in info})
            entries.append(entry)
        return entries

    def _scan_seasons(self, title_dir: Path, state: ScanState) -> list[dict[str, Any]]:
        seasons: list[dict[str, Any]] = []
        for season_dir in sorted((path for path in title_dir.iterdir()
                                  if path.is_dir() and season_number(path.name) is not None),
                                 key=lambda path: season_number(path.name) or 0):
            season = self._scan_episodes(title_dir, season_number(season_dir.name) or 0, season_dir, state)
            if season:
                seasons.append(season)
            else:
                state.warn(f"Ignored season folder without videos: {relative(season_dir)}")
        # Videos placed directly in the title folder (no season folder) count as Season 1.
        direct = self._scan_episodes(title_dir, 1, title_dir, state)
        if direct:
            seasons.insert(0, direct)
        return seasons

    def _scan_episodes(self, title_dir: Path, season: int, directory: Path, state: ScanState) -> dict[str, Any] | None:
        videos = sorted(
            (path for path in directory.iterdir()
             if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS),
            key=lambda path: path.name.casefold(),
        )
        if not videos:
            return None
        subtitle_index = index_directory(directory, SUBTITLE_EXTENSIONS)
        image_index = index_directory(directory, IMAGE_EXTENSIONS)
        cached = self._cached_episodes()
        used_numbers: set[int] = set()
        fallback = 1
        episodes = []
        parsed_videos: list[tuple[Path, int | None]] = [
            (video, episode_number(video.stem)) for video in videos
        ]
        # Numbered episodes are ordered numerically; unnumbered files retain
        # deterministic filename order after the numbered files.
        parsed_videos.sort(key=lambda item: (
            item[1] is None,
            item[1] if item[1] is not None else 0,
            item[0].name.casefold(),
        ))
        anime_slug = slugify(title_dir.name)
        for video, parsed_number in parsed_videos:
            number = parsed_number
            if number is None or number in used_numbers:
                while fallback in used_numbers:
                    fallback += 1
                number = fallback
            used_numbers.add(number)
            fallback = number + 1
            expected_id = f"{anime_slug}-s{season:02d}-e{number:02d}"
            reused = self._reuse_episode(video, cached)
            if reused is not None and reused.get("id") == expected_id and reused.get("number") == number:
                # A reused record must still carry current asset paths so
                # newly added thumbnails/subtitles are visible immediately.
                episodes.append({
                    **reused,
                    "subtitle_paths": self._subtitles(video, subtitle_index),
                    "thumbnail_path": image_index.get(video.stem.lower()),
                })
                continue
            episodes.append({
                "id": expected_id,
                "number": number,
                "title": episode_title(video.stem, number),
                "video_path": str(video),
                "subtitle_paths": self._subtitles(video, subtitle_index),
                "thumbnail_path": image_index.get(video.stem.lower()),
            })
        return {"number": season, "episodes": episodes}

    # -------------------------------------------------------------- standalone

    def _scan_standalone(self, category_dir: Path, category: str, state: ScanState) -> list[dict[str, Any]]:
        """Movies/Tutorials/Other: each title is a single video.

        A video file directly inside the category folder is a title; a
        subfolder with exactly one video is a title too (with room for
        poster/banner/info.json). Folders with several videos use the video
        whose stem matches the folder name, else the alphabetically first one,
        and report a warning.
        """
        entries: list[dict[str, Any]] = []
        used_ids: set[str] = set()
        for candidate in sorted(category_dir.iterdir(), key=lambda path: path.name.casefold()):
            if candidate.is_file() and candidate.suffix.lower() in VIDEO_EXTENSIONS:
                entries.append(self._standalone_entry(category_dir, candidate, category, used_ids, state, title_fallback=candidate.stem))
            elif candidate.is_dir():
                videos = sorted((path for path in candidate.iterdir()
                                 if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS),
                                key=lambda path: path.name.casefold())
                if not videos:
                    state.warn(f"Ignored folder without videos: {relative(candidate)}")
                    continue
                video = self._pick_standalone_video(candidate, videos, state)
                entries.append(self._standalone_entry(candidate, video, category, used_ids, state, title_fallback=candidate.name))
        return entries

    @staticmethod
    def _pick_standalone_video(folder: Path, videos: list[Path], state: ScanState) -> Path:
        if len(videos) == 1:
            return videos[0]
        named = [path for path in videos if path.stem.casefold() == folder.name.casefold()]
        picked = named[0] if named else videos[0]
        state.warn(f"Folder contains {len(videos)} videos; using {picked.name}: {relative(folder)}")
        return picked

    def _standalone_entry(self, folder: Path, video: Path, category: str,
                          used_ids: set[str], state: ScanState, title_fallback: str) -> dict[str, Any]:
        images = index_directory(folder, IMAGE_EXTENSIONS)
        subtitle_index = index_directory(folder, SUBTITLE_EXTENSIONS)
        info = read_info_json(folder, state)
        title = info.get("title") or title_fallback
        entry_id = self._unique_id(slugify(title), used_ids)
        entry: dict[str, Any] = {
            "id": entry_id,
            "type": category,
            "title": title,
            "path": str(folder),
            "poster": images.get("poster") or images.get(video.stem.lower()),
            "banner": images.get("banner"),
            "episodes": [{
                "id": f"{entry_id}-e01",
                "number": 1,
                "title": video.stem,
                "video_path": str(video),
                "subtitle_paths": self._subtitles(video, subtitle_index),
                "thumbnail_path": images.get(video.stem.lower()),
            }],
        }
        entry.update({key: info[key] for key in METADATA_KEYS[1:] if key in info})
        return entry

    # ------------------------------------------------------------------ utils

    @staticmethod
    def _unique_id(proposal: str, used_ids: set[str]) -> str:
        candidate = proposal
        suffix = 2
        while candidate in used_ids:
            candidate = f"{proposal}-{suffix}"
            suffix += 1
        used_ids.add(candidate)
        return candidate

    @staticmethod
    def _subtitles(video: Path, subtitle_index: dict[str, str]) -> list[str]:
        return sorted(
            path for stem, path in subtitle_index.items()
            if stem.lower().startswith(video.stem.lower())
        )

    @staticmethod
    def _count_entry(entry: dict[str, Any], counts: dict[str, int]) -> None:
        entry_type = entry.get("type")
        if entry_type in counts:
            counts[entry_type] += 1
        counts["episodes"] += sum(len(season.get("episodes", [])) for season in entry.get("seasons", []))
        counts["episodes"] += len(entry.get("episodes", []))
        if entry.get("poster"):
            counts["posters"] += 1
        if entry.get("banner"):
            counts["banners"] += 1
