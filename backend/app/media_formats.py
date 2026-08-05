"""Canonical media format support for the Hibiki content pipeline."""

from __future__ import annotations

VIDEO_EXTENSIONS = frozenset({
    ".mp4", ".mkv", ".webm", ".avi", ".mov", ".m4v", ".flv", ".mpeg", ".ts", ".m3u8",
})

MEDIA_TYPES = {
    ".mp4": "video/mp4",
    ".mkv": "video/x-matroska",
    ".webm": "video/webm",
    ".avi": "video/x-msvideo",
    ".mov": "video/quicktime",
    ".m4v": "video/x-m4v",
    ".flv": "video/x-flv",
    ".mpeg": "video/mpeg",
    ".ts": "video/mp2t",
    ".m3u8": "application/vnd.apple.mpegurl",
    ".vtt": "text/vtt",
}
