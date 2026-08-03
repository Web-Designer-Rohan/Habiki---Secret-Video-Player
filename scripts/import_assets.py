#!/usr/bin/env python3
"""Import and verify project assets referenced by docs/CONTENT.md.

Downloads (or verifies already-present) poster images and the banner and font
archives, validates integrity against the hashes recorded in docs/ASSETS.md,
and reports what was imported, verified, skipped, or mismatched.

Existing local files are never overwritten unless --force is passed.
Downloads are cached in data/cache/ (gitignored) so archives are fetched at
most once.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from content import ContentManifest, parse_content

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTENT_PATH = PROJECT_ROOT / "docs" / "CONTENT.md"
ASSETS_DIR = PROJECT_ROOT / "assets"
MEDIA_DIR = PROJECT_ROOT / "media"
CACHE_DIR = PROJECT_ROOT / "data" / "cache"

# Integrity hashes recorded in docs/ASSETS.md for the development archives.
ARCHIVE_SHA256 = {
    "30_banners.zip": "b91d98f24a971a4db7bcba306311ae005e9d5becb1f388454c40e23127c678e8",
    "Anton,Inter,Noto_Sans_JP.zip": "4672ef0925791c79af4c8b5004e5e80c95ba9c279b08e54ea7084ab3f4fba2e0",
}

POSTER_DIRS = {
    "Jujutsu Kaisan": "Jujutsu_Kaisan.jpg",
    "Demon Slayer": "Demon_Slayer.jpg",
    "Sololeveling": "Solo_Leveling.jpg",
    "AOT": "Attack_On_Titans.jpg",
    "Deathnote": "Death_Note.jpg",
    "Gachiakuta": "Gachiakuta.jpg",
}


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(f"{target.suffix}.tmp")
    with urllib.request.urlopen(url, timeout=60) as response, temporary.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    temporary.replace(target)


def optimize_poster(folder: Path, force: bool) -> list[str]:
    """Create an optimized poster.webp next to poster.jpg without touching user files.

    The WebP copy is a derived artifact: the source JPEG is never overwritten and
    an existing poster.webp is left alone unless --force is passed. Missing FFmpeg
    or a failed conversion degrades gracefully to the original JPEG.
    """
    source = folder / "poster.jpg"
    target = folder / "poster.webp"
    report: list[str] = []
    if not source.is_file():
        return report
    if target.exists() and not force:
        report.append(f"poster {folder.name}: poster.webp already present (cached)")
        return report
    executable = shutil.which("ffmpeg")
    if not executable:
        report.append(f"poster {folder.name}: ffmpeg unavailable; kept JPEG (no WebP optimization)")
        return report
    temporary = target.with_suffix(f"{target.suffix}.tmp")
    try:
        result = subprocess.run(
            [executable, "-y", "-i", str(source), "-q:v", "60", "-f", "webp", str(temporary)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0 or not temporary.is_file():
            temporary.unlink(missing_ok=True)
            report.append(f"poster {folder.name}: WebP optimization failed; kept JPEG")
            return report
        temporary.replace(target)
        report.append(f"poster {folder.name}: optimized poster.webp created")
    except (OSError, subprocess.TimeoutExpired) as error:
        temporary.unlink(missing_ok=True)
        report.append(f"poster {folder.name}: WebP optimization skipped ({error})")
    return report


def verify_poster(entry_title: str, poster_url: str, force: bool) -> list[str]:
    """Ensure media/<Title>/poster.jpg exists and matches the manifest source."""
    folder = MEDIA_DIR / entry_title
    target = folder / "poster.jpg"
    report: list[str] = []
    cached = CACHE_DIR / "posters" / poster_url.rsplit("/", 1)[-1]
    try:
        if not cached.exists():
            download(poster_url, cached)
        source_hash = sha256_of(cached)
    except Exception as error:  # network or disk failure: report, keep going
        report.append(f"poster {entry_title}: could not fetch source ({error})")
        return report

    if target.exists():
        local_hash = sha256_of(target)
        if local_hash == source_hash:
            report.append(f"poster {entry_title}: present and matches source (verified)")
        elif force:
            target.write_bytes(cached.read_bytes())
            report.append(f"poster {entry_title}: replaced with source (--force)")
        else:
            report.append(f"poster {entry_title}: local file differs from source; kept (use --force to replace)")
    else:
        folder.mkdir(parents=True, exist_ok=True)
        target.write_bytes(cached.read_bytes())
        report.append(f"poster {entry_title}: downloaded ({target})")
    report.extend(optimize_poster(folder, force))
    return report


def verify_archive(kind: str, url: str, local_assets: list[Path], expected_count: int | None = None) -> list[str]:
    """Fetch an archive once, verify its sha256, and compare with local assets."""
    report: list[str] = []
    filename = "30_banners.zip" if kind == "banners" else "Anton,Inter,Noto_Sans_JP.zip"
    cached = CACHE_DIR / filename
    try:
        if not cached.exists():
            download(url, cached)
        actual_hash = sha256_of(cached)
        expected = ARCHIVE_SHA256.get(filename)
        if expected and actual_hash != expected:
            report.append(f"{kind}: sha256 MISMATCH (expected {expected}, got {actual_hash})")
            return report
        report.append(f"{kind}: sha256 verified ({actual_hash[:16]}...)")
    except Exception as error:
        report.append(f"{kind}: could not fetch archive ({error})")
        return report

    try:
        with tempfile.TemporaryDirectory() as directory:
            with zipfile.ZipFile(cached) as archive:
                archive.extractall(directory)
            extracted = sorted(path for path in Path(directory).rglob("*") if path.is_file())
            local_names = sorted(path.name for path in local_assets)
            extracted_names = sorted(path.name for path in extracted)
            if local_names == extracted_names:
                report.append(f"{kind}: extracted contents match local assets ({len(local_names)} files)")
            else:
                missing = sorted(set(extracted_names) - set(local_names))
                extra = sorted(set(local_names) - set(extracted_names))
                report.append(f"{kind}: extracted {len(extracted_names)} files, local has {len(local_names)}")
                if missing:
                    report.append(f"{kind}: not present locally: {', '.join(missing[:5])}")
                if extra:
                    report.append(f"{kind}: local-only files: {', '.join(extra[:5])}")
            if expected_count and len(local_names) != expected_count:
                report.append(f"{kind}: expected {expected_count} local files, found {len(local_names)}")
    except zipfile.BadZipFile:
        report.append(f"{kind}: downloaded archive is not a valid zip")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Import and verify project assets from CONTENT.md")
    parser.add_argument("--force", action="store_true", help="overwrite local files that differ from the source")
    args = parser.parse_args()

    manifest = parse_content(CONTENT_PATH)
    for warning in manifest.warnings:
        print(f"WARNING {warning}", file=sys.stderr)
    if manifest.warnings:
        print("Aborting: CONTENT.md contains malformed entries.", file=sys.stderr)
        return 1

    report: list[str] = []
    for entry in manifest.series:
        if entry.poster_url:
            report.extend(verify_poster(entry.title, entry.poster_url, args.force))
    for entry in manifest.tutorials:
        report.append(f"tutorial {entry.title}: no poster expected (standalone)")

    banners = sorted(ASSETS_DIR.glob("banners/*"))
    fonts = sorted(path for path in ASSETS_DIR.rglob("*") if path.is_file() and path.suffix.lower() in {".ttf"})
    if manifest.banners_url:
        report.extend(verify_archive("banners", manifest.banners_url, banners, expected_count=30))
    else:
        report.append("banners: no archive URL in CONTENT.md")
    if manifest.fonts_url:
        report.extend(verify_archive("fonts", manifest.fonts_url, fonts))
    else:
        report.append("fonts: no archive URL in CONTENT.md")

    for line in report:
        print(f"- {line}")
    errors = [line for line in report if "MISMATCH" in line or "Aborting" in line]
    print(f"Import summary: {len(manifest.series)} series, {len(manifest.tutorials)} tutorials, {len(report)} checks")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
