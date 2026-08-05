#!/usr/bin/env python3
"""Generate episode thumbnails for locally available media.

Captures a representative frame roughly 3-10 seconds into each indexed video
(default: 5 seconds), encodes it as an optimized WebP (max 640 px wide), and
caches it next to the episode so the library scanner discovers it as the
episode thumbnail. See docs/DATABASE.md for the capture policy.

Graceful degradation: missing videos, unsupported formats, and absent FFmpeg
are reported and skipped; the command never fails because media is absent.
Existing thumbnails are reused unless --force is passed.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.media_formats import VIDEO_EXTENSIONS
MEDIA_DIR = PROJECT_ROOT / "contents"

THUMBNAIL_EXTENSIONS = {".webp", ".png", ".jpg", ".jpeg"}
DEFAULT_CAPTURE_SECONDS = 5.0
MAX_WIDTH = 640
CAPTURE_FALLBACKS = (0.0, 1.0, 2.0)  # tried in order if the requested point fails


def find_videos(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(
        (path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS),
        key=lambda path: path.as_posix().lower(),
    )


def thumbnail_for(video: Path) -> Path:
    return video.with_suffix(".webp")


def describe(path: Path) -> str:
    """Project-relative path when possible, absolute otherwise (media may live outside the repo)."""
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def thumbnail_is_current(video: Path, thumbnail: Path) -> bool:
    try:
        return thumbnail.is_file() and thumbnail.stat().st_mtime >= video.stat().st_mtime
    except OSError:
        return False


def render(executable: str, video: Path, output: Path, capture: float) -> bool:
    scale = f"scale='if(gt(iw,{MAX_WIDTH}),{MAX_WIDTH},iw)':-2"
    command = [
        executable, "-y",
        "-ss", f"{capture:g}",
        "-i", str(video),
        "-frames:v", "1",
        "-vf", scale,
        "-q:v", "60",
        "-f", "webp",
        str(output),
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    return result.returncode == 0 and output.is_file()


def generate(video: Path, force: bool, capture: float, dry_run: bool) -> str:
    thumbnail = thumbnail_for(video)
    if not force and thumbnail_is_current(video, thumbnail):
        return f"cached   {describe(video)}"
    executable = shutil.which("ffmpeg")
    if not executable:
        return f"skipped  {describe(video)} (ffmpeg unavailable)"
    if dry_run:
        return f"would    {describe(thumbnail)}"
    points = [capture, *CAPTURE_FALLBACKS]
    for point in points:
        temporary = thumbnail.with_suffix(f"{thumbnail.suffix}.tmp")
        try:
            if render(executable, video, temporary, point):
                temporary.replace(thumbnail)
                return f"created  {describe(thumbnail)} (frame @ {point:g}s)"
            temporary.unlink(missing_ok=True)
        except (OSError, subprocess.TimeoutExpired) as error:
            temporary.unlink(missing_ok=True)
            return f"failed   {describe(video)} ({error})"
    return f"failed   {describe(video)} (no usable frame 0-{capture:g}s)"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate episode thumbnails from local media")
    parser.add_argument("--seconds", type=float, default=DEFAULT_CAPTURE_SECONDS,
                        help="capture point in seconds (3-10 recommended; default 5)")
    parser.add_argument("--force", action="store_true", help="regenerate existing thumbnails")
    parser.add_argument("--dry-run", action="store_true", help="list work without writing files")
    parser.add_argument("--root", type=Path, default=MEDIA_DIR, help="media root to scan (default: contents/)")
    args = parser.parse_args()

    videos = find_videos(args.root)
    if not videos:
        print("No local videos found. Nothing to generate; skipping gracefully.")
        return 0

    reports = [generate(video, args.force, args.seconds, args.dry_run) for video in videos]
    for line in reports:
        print(line)
    created = sum(1 for line in reports if line.startswith("created"))
    failed = sum(1 for line in reports if line.startswith("failed"))
    print(f"Thumbnail summary: {created} created, {failed} failed, {len(videos) - created - failed} reused/skipped of {len(videos)} videos")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
