#!/usr/bin/env python3
"""Build data/library.json from the media manifest in docs/CONTENT.md.

Series produce season/episode metadata; standalone tutorials become library
items without seasons or episodes. Referenced videos are not assumed to be
present: when a local file cannot be found the episode is written as a
metadata-only placeholder (no video path), matching the documented import flow
in docs/ASSETS.md. A later library scan replaces these entries once real media
files exist on disk.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.scanner import slugify  # noqa: E402

from content import ContentManifest, parse_content  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTENT_PATH = PROJECT_ROOT / "docs" / "CONTENT.md"
MEDIA_DIR = PROJECT_ROOT / "media"
LIBRARY_PATH = PROJECT_ROOT / "data" / "library.json"


def build_library(manifest: ContentManifest) -> dict:
    entries = []
    for entry in manifest.media:
        folder = MEDIA_DIR / entry.title
        # Prefer the optimized WebP poster produced by import_assets.py over the source JPEG.
        poster = None
        for candidate in ("poster.webp", "poster.jpg"):
            if (folder / candidate).is_file():
                poster = folder / candidate
                break
        anime = {
            "id": slugify(entry.title),
            "title": entry.title,
            "poster": str(poster) if poster else None,
            "banner": None,
        }
        if folder.is_dir():
            anime["path"] = str(folder)
        anime["seasons"] = []
        for season in entry.seasons:
            episodes = []
            for episode in season.episodes:
                episodes.append({
                    "id": f"{slugify(entry.title)}-s{season.number:02d}-e{episode.number:02d}",
                    "number": episode.number,
                    "title": f"Episode {episode.number:02d}",
                })
            anime["seasons"].append({"number": season.number, "episodes": episodes})
        entries.append(anime)
    return {"version": 1, "scanned_at": datetime.now(timezone.utc).isoformat(), "anime": entries}


def main() -> int:
    manifest = parse_content(CONTENT_PATH)
    for warning in manifest.warnings:
        print(f"WARNING {warning}", file=sys.stderr)
    if manifest.warnings:
        print("Aborting: CONTENT.md contains malformed entries.", file=sys.stderr)
        return 1

    library = build_library(manifest)
    LIBRARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = LIBRARY_PATH.with_suffix(f"{LIBRARY_PATH.suffix}.tmp")
    temporary.write_text(json.dumps(library, indent=2) + "\n", encoding="utf-8")
    temporary.replace(LIBRARY_PATH)

    total_episodes = sum(
        len(episode)
        for entry in library["anime"]
        for season in entry["seasons"]
        for episode in [season["episodes"]]
    )
    print(f"Wrote {LIBRARY_PATH}")
    print(f"  {len(library['anime'])} library items ({len(manifest.series)} series, {len(manifest.tutorials)} tutorials)")
    print(f"  {total_episodes} episodes across {sum(len(e['seasons']) for e in library['anime'])} seasons")
    return 0


if __name__ == "__main__":
    sys.exit(main())
