#!/usr/bin/env python3
"""Estimate and report the project size breakdown for Hibiki.

Reports bytes for source code, documentation, bundled assets (fonts, banners,
vendor), user media (posters), generated artifacts (database), and totals with
and without the user-supplied media library.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SOURCE_DIRS = ("backend", "frontend", "scripts")
DOCS_DIR = PROJECT_ROOT / "docs"
FONTS_DIR = PROJECT_ROOT / "assets" / "fonts"
BANNERS_DIR = PROJECT_ROOT / "assets" / "banners"
VENDOR_DIR = PROJECT_ROOT / "assets" / "vendor"
MEDIA_DIR = PROJECT_ROOT / "media"
DB_PATH = PROJECT_ROOT / "data" / "database.db"


def human(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.2f} {unit}" if unit != "B" else f"{size} B"
        size /= 1024
    return f"{size:.2f} GB"


def dir_size(path: Path) -> int:
    if not path.is_dir():
        return 0
    return sum(entry.stat().st_size for entry in path.rglob("*") if entry.is_file())


def file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def poster_size() -> int:
    if not MEDIA_DIR.is_dir():
        return 0
    return sum(
        entry.stat().st_size
        for entry in MEDIA_DIR.rglob("*")
        if entry.is_file() and entry.name.lower().startswith("poster")
    )


def main() -> int:
    rows: list[tuple[str, int]] = []
    source = sum(dir_size(PROJECT_ROOT / directory) for directory in SOURCE_DIRS)
    rows.append(("Source code (backend, frontend, scripts)", source))
    docs = dir_size(DOCS_DIR)
    rows.append(("Documentation (docs/)", docs))
    fonts = dir_size(FONTS_DIR)
    rows.append(("Fonts (assets/fonts)", fonts))
    banners = dir_size(BANNERS_DIR)
    rows.append(("Banners (assets/banners)", banners))
    vendor = dir_size(VENDOR_DIR)
    rows.append(("Vendored assets (assets/vendor)", vendor))
    posters = poster_size()
    rows.append(("Posters (media/**/poster.*, user media)", posters))
    thumbnails = dir_size(MEDIA_DIR) - posters
    rows.append(("Thumbnails + other media (media/)", thumbnails))
    database = file_size(DB_PATH)
    rows.append(("Database (data/database.db)", database))

    application_total = source + docs + fonts + banners + vendor + database
    project_total = application_total + posters + thumbnails

    print("Hibiki project size estimate")
    print(f"{'Component':<44} {'Size':>10}")
    print("-" * 56)
    for label, size in rows:
        print(f"{label:<44} {human(size):>10}")
    print("-" * 56)
    print(f"{'Application total (excluding user media)':<44} {human(application_total):>10}")
    print(f"{'Project total (after imported assets)':<44} {human(project_total):>10}")
    print()
    print("Media files are user-supplied and gitignored; totals above are on-disk estimates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
