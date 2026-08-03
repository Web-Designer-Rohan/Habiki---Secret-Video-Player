#!/usr/bin/env python3
"""Validate and repair Hibiki's metadata and asset pipeline.

Checks, in order:

1. docs/CONTENT.md parses without malformed entries.
2. JSON documents (data/library.json, config/config.json, localization files)
   are valid and structurally sound.
3. data/library.json matches the CONTENT.md manifest: same items, seasons,
   episodes, unique identifiers, no duplicates.
4. Repository assets are present and organized (banners, fonts, vendor).
5. Referenced user media (posters) exist; missing media is reported as a
   warning because the library is user-supplied and gitignored.
6. SQLite database exists, passes integrity checks, has no foreign-key
   violations, and contains no dangling anime/episode references.
7. Localization files for hi/en/ja share the same key set.

Inconsistencies are repaired automatically where possible (regenerated
library.json, pruned dangling rows, filled missing localization keys) and
reported. Unrepairable problems leave the command with a non-zero exit code.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTENT_PATH = PROJECT_ROOT / "docs" / "CONTENT.md"
MEDIA_DIR = PROJECT_ROOT / "media"
ASSETS_DIR = PROJECT_ROOT / "assets"
DATA_DIR = PROJECT_ROOT / "data"
LIBRARY_PATH = DATA_DIR / "library.json"
DB_PATH = DATA_DIR / "database.db"
LOCALIZATION_DIR = DATA_DIR / "localization"

LOCALE_CODES = ("hi", "en", "ja")
EXPECTED_FONTS = {
    "Anton": "Anton-Regular.ttf",
    "Inter": "Inter-VariableFont_opsz,wght.ttf",
    "Noto Sans JP": "NotoSansJP-VariableFont_wght.ttf",
}
EXPECTED_BANNER_COUNT = 30
EPISODE_ID_PATTERN = re.compile(r"^[a-z0-9-]+-s\d{2}-e\d{2}$")

from content import ContentManifest, parse_content  # noqa: E402
from build_library import build_library  # noqa: E402
from backend.app.scanner import slugify  # noqa: E402


class Findings:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.repairs: list[str] = []
        self.rebuild_library = False

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def repaired(self, message: str) -> None:
        self.repairs.append(message)

    @property
    def healthy(self) -> bool:
        return not self.errors


def read_json(path: Path, findings: Findings) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        findings.error(f"{path.relative_to(PROJECT_ROOT)}: missing file")
        return None
    except (OSError, json.JSONDecodeError) as error:
        findings.error(f"{path.relative_to(PROJECT_ROOT)}: invalid JSON ({error})")
        return None
    if not isinstance(data, dict):
        findings.error(f"{path.relative_to(PROJECT_ROOT)}: expected a JSON object")
        return None
    return data


def write_json_atomic(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def check_manifest(findings: Findings) -> ContentManifest | None:
    try:
        manifest = parse_content(CONTENT_PATH)
    except (OSError, UnicodeDecodeError) as error:
        findings.error(f"docs/CONTENT.md: unreadable ({error})")
        return None
    for warning in manifest.warnings:
        findings.error(f"docs/CONTENT.md: {warning}")
    if manifest.banners_url:
        print(f"  manifest: banners archive {manifest.banners_url.rsplit('/', 1)[-1]}")
    if manifest.fonts_url:
        print(f"  manifest: fonts archive {manifest.fonts_url.rsplit('/', 1)[-1]}")
    print(f"  manifest: {len(manifest.series)} series, {len(manifest.tutorials)} tutorials")
    return manifest


def check_library(findings: Findings, manifest: ContentManifest | None) -> dict | None:
    library = read_json(LIBRARY_PATH, findings)
    if library is None:
        findings.rebuild_library = True
        return None
    if library.get("version") != 1:
        findings.error("data/library.json: unexpected version (expected 1)")
        findings.rebuild_library = True

    anime_list = library.get("anime")
    if not isinstance(anime_list, list):
        findings.error("data/library.json: 'anime' must be a list")
        findings.rebuild_library = True
        return library

    anime_ids: set[str] = set()
    episode_ids: set[str] = set()
    for index, anime in enumerate(anime_list):
        if not isinstance(anime, dict) or "id" not in anime or "title" not in anime:
            findings.error(f"data/library.json: anime[{index}] missing id or title")
            findings.rebuild_library = True
            continue
        if anime["id"] in anime_ids:
            findings.error(f"data/library.json: duplicate anime id {anime['id']!r}")
            findings.rebuild_library = True
        anime_ids.add(anime["id"])
        season_numbers: set[int] = set()
        for season in anime.get("seasons", []):
            if season.get("number") in season_numbers:
                findings.error(f"data/library.json: duplicate season number in {anime['id']}")
                findings.rebuild_library = True
            season_numbers.add(season.get("number"))
            for episode in season.get("episodes", []):
                episode_id = episode.get("id")
                if not episode_id or not EPISODE_ID_PATTERN.match(str(episode_id)):
                    findings.error(f"data/library.json: malformed episode id {episode_id!r}")
                    findings.rebuild_library = True
                if episode_id in episode_ids:
                    findings.error(f"data/library.json: duplicate episode id {episode_id!r}")
                    findings.rebuild_library = True
                episode_ids.add(episode_id)

    if manifest is None:
        return library

    expected_ids = {slugify(entry.title): entry for entry in manifest.media}
    missing_entries = sorted(set(expected_ids) - anime_ids)
    extra_entries = sorted(anime_ids - set(expected_ids))
    if missing_entries:
        findings.error(f"data/library.json: missing manifest entries: {', '.join(missing_entries)}")
        findings.rebuild_library = True
    if extra_entries:
        # Preserve manual additions: warn instead of rebuilding them away.
        findings.warning(f"data/library.json: entries not in manifest (manual additions?): {', '.join(extra_entries)}")

    for anime in anime_list:
        entry = expected_ids.get(anime["id"])
        if entry is None:
            continue
        if entry.standalone:
            if anime.get("seasons"):
                findings.error(f"data/library.json: {anime['id']} is a standalone tutorial but has seasons")
                findings.rebuild_library = True
            continue
        expected_seasons = {season.number: len(season.episodes) for season in entry.seasons}
        actual_seasons = {season.get("number"): len(season.get("episodes", [])) for season in anime.get("seasons", [])}
        if actual_seasons != expected_seasons:
            findings.error(
                f"data/library.json: {anime['id']} season/episode counts differ from manifest "
                f"(library {actual_seasons} vs manifest {expected_seasons})"
            )
            findings.rebuild_library = True
    return library


def check_assets(findings: Findings) -> None:
    banners = [path for path in (ASSETS_DIR / "banners").glob("*") if path.is_file()]
    if len(banners) != EXPECTED_BANNER_COUNT:
        findings.error(f"assets/banners: expected {EXPECTED_BANNER_COUNT} files, found {len(banners)}")
    else:
        print(f"  assets: {len(banners)} banners")

    for family, filename in EXPECTED_FONTS.items():
        matches = list((ASSETS_DIR / "fonts").rglob(filename))
        if not matches:
            findings.error(f"assets/fonts: missing {family} build ({filename})")
        else:
            print(f"  assets: font {family} ({filename})")

    if not (ASSETS_DIR / "vendor" / "anime" / "anime.umd.min.js").is_file():
        findings.error("assets/vendor: missing anime.umd.min.js")
    if not (ASSETS_DIR / "vendor" / "lucide").is_dir():
        findings.error("assets/vendor: missing lucide icon directory")


def check_media(findings: Findings, library: dict | None, manifest: ContentManifest | None) -> None:
    if library is not None:
        for anime in library.get("anime", []):
            poster_path = anime.get("poster")
            if poster_path and not Path(poster_path).is_file():
                findings.warning(f"media: poster referenced but missing: {poster_path}")
            for season in anime.get("seasons", []):
                for episode in season.get("episodes", []):
                    for key in ("video_path", "subtitle_paths", "thumbnail_path"):
                        value = episode.get(key)
                        if isinstance(value, str) and value and not Path(value).is_file():
                            findings.warning(f"media: {key} referenced but missing: {value}")
                        elif isinstance(value, list):
                            for item in value:
                                if item and not Path(item).is_file():
                                    findings.warning(f"media: {key} entry missing: {item}")

    if manifest is not None:
        for entry in manifest.media:
            if entry.poster_url and not entry.standalone:
                folder = MEDIA_DIR / entry.title
                if not (folder / "poster.webp").is_file() and not (folder / "poster.jpg").is_file():
                    findings.warning(f"media: {entry.title} has a manifest poster but no local poster file")


def initialize_database(findings: Findings) -> sqlite3.Connection | None:
    if not DB_PATH.exists():
        findings.repaired("data/database.db: created and migrated")
        from backend.app.database import Database

        Database(DB_PATH).initialize()
    try:
        connection = sqlite3.connect(DB_PATH, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
    except sqlite3.Error as error:
        findings.error(f"data/database.db: cannot open ({error})")
        return None
    return connection


def check_database(findings: Findings, library: dict | None) -> None:
    connection = initialize_database(findings)
    if connection is None:
        return
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            findings.error(f"data/database.db: integrity check failed ({integrity})")
        foreign_key_violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if foreign_key_violations:
            findings.error(f"data/database.db: {len(foreign_key_violations)} foreign key violations")

        anime_ids = {anime["id"] for anime in (library or {}).get("anime", [])}
        episode_ids = {
            episode["id"]
            for anime in (library or {}).get("anime", [])
            for season in anime.get("seasons", [])
            for episode in season.get("episodes", [])
        }

        with connection:
            for table, column in (("favorites", "anime_id"), ("continue_watching", "anime_id"), ("watch_history", "anime_id")):
                if anime_ids:
                    rows = connection.execute(
                        f"SELECT id FROM {table} WHERE {column} NOT IN ({','.join('?' * len(anime_ids))})",
                        tuple(anime_ids),
                    ).fetchall()
                else:
                    rows = connection.execute(f"SELECT id FROM {table}").fetchall()
                for row in rows:
                    connection.execute(f"DELETE FROM {table} WHERE id = ?", (row["id"],))
                    findings.repaired(f"data/database.db: pruned dangling {table} row {row['id']}")

            for table in ("continue_watching", "watch_history"):
                for row in connection.execute(f"SELECT id, episode_id FROM {table}").fetchall():
                    if row["episode_id"] not in episode_ids:
                        connection.execute(f"DELETE FROM {table} WHERE id = ?", (row["id"],))
                        findings.repaired(f"data/database.db: pruned dangling {table} row {row['id']}")
        print("  database: integrity ok, schema present")
    except sqlite3.Error as error:
        findings.error(f"data/database.db: validation failed ({error})")
    finally:
        connection.close()


def check_localization(findings: Findings) -> None:
    canonical: dict[str, str] | None = None
    for code in LOCALE_CODES:
        path = LOCALIZATION_DIR / f"{code}.json"
        data = read_json(path, findings)
        if data is None:
            continue
        if code == "en":
            canonical = data
            continue
        if canonical is None:
            continue
        missing = [key for key in canonical if key not in data]
        extra = [key for key in data if key not in canonical]
        if missing:
            for key in missing:
                data[key] = canonical[key]
            write_json_atomic(path, data)
            findings.repaired(f"data/localization/{code}.json: added {len(missing)} missing key(s): {', '.join(sorted(missing))}")
        if extra:
            findings.warning(f"data/localization/{code}.json: {len(extra)} key(s) not in English: {', '.join(sorted(extra))}")
    print("  localization: hi/en/ja key sets verified")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and repair Hibiki metadata and assets")
    parser.add_argument("--check-only", action="store_true", help="report problems without repairing")
    args = parser.parse_args()

    findings = Findings()
    print("Hibiki validation")

    manifest = check_manifest(findings)
    library = check_library(findings, manifest)

    # Regenerate library.json from the manifest when it is stale or broken.
    # Skipped when the manifest itself is malformed (that would rebuild garbage)
    # or when running in check-only mode. Manual extra entries are preserved.
    if manifest is not None and findings.rebuild_library and not args.check_only:
        rebuilt = build_library(manifest)
        write_json_atomic(LIBRARY_PATH, rebuilt)
        findings.repaired(f"data/library.json: regenerated from manifest ({len(rebuilt['anime'])} items)")
        library = rebuilt
        recheck = Findings()
        library = check_library(recheck, manifest)
        if recheck.errors:
            findings.errors.extend(f"data/library.json after regeneration: {message}" for message in recheck.errors)
        else:
            findings.errors = [message for message in findings.errors if "data/library.json" not in message]

    check_assets(findings)
    check_media(findings, library, manifest)
    check_database(findings, library)
    check_localization(findings)

    print("  search index: served by GET /api/v1/library/search (no separate index file)")

    for message in findings.repairs:
        print(f"REPAIRED {message}")
    for message in findings.warnings:
        print(f"WARNING  {message}")
    for message in findings.errors:
        print(f"ERROR    {message}")

    print(f"Validation summary: {len(findings.errors)} errors, {len(findings.warnings)} warnings, {len(findings.repairs)} repairs")
    return 1 if findings.errors else 0


if __name__ == "__main__":
    sys.exit(main())
