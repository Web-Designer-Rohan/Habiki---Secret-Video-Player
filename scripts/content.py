"""Parse docs/CONTENT.md, the temporary source of truth for project assets.

The file is a loose, human-edited manifest. Each top-level entry is one of:

- A series: a heading line ending in ``:`` followed by ``Poster: <url>`` and
  ``Season <n>:`` blocks, each season containing ``Episode <n>: <url>`` lines.
- A standalone tutorial: a ``Title: <url>`` line with no seasons or episodes.
- An archive entry: ``30_Banners: <url>`` or ``Fonts: <url>``.

Only well-formed entries are consumed; anything unrecognized is reported as a
warning so the manifest can be repaired instead of being silently ignored.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

EPISODE_PATTERN = re.compile(r"^Episode\s+(\d+)\s*:\s*(\S+)\s*$", re.IGNORECASE)
SEASON_PATTERN = re.compile(r"^Season\s+(\d+)\s*:?\s*$", re.IGNORECASE)
POSTER_PATTERN = re.compile(r"^Poster\s*:\s*(\S+)\s*$", re.IGNORECASE)
ARCHIVE_NAMES = {"30_BANNERS": "banners", "FONTS": "fonts"}


@dataclass
class EpisodeEntry:
    number: int
    url: str


@dataclass
class SeasonEntry:
    number: int
    episodes: list[EpisodeEntry] = field(default_factory=list)


@dataclass
class MediaEntry:
    title: str
    poster_url: str | None = None
    seasons: list[SeasonEntry] = field(default_factory=list)

    @property
    def standalone(self) -> bool:
        return not self.seasons


@dataclass
class ContentManifest:
    media: list[MediaEntry]
    banners_url: str | None
    fonts_url: str | None
    warnings: list[str]

    @property
    def series(self) -> list[MediaEntry]:
        return [entry for entry in self.media if not entry.standalone]

    @property
    def tutorials(self) -> list[MediaEntry]:
        return [entry for entry in self.media if entry.standalone]


def parse_content(path: Path) -> ContentManifest:
    lines = path.read_text(encoding="utf-8").splitlines()
    media: list[MediaEntry] = []
    banners_url: str | None = None
    fonts_url: str | None = None
    warnings: list[str] = []
    current: MediaEntry | None = None
    current_season: SeasonEntry | None = None

    for index, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line == "---":
            continue

        poster = POSTER_PATTERN.match(line)
        if poster:
            if current is None:
                warnings.append(f"line {index}: Poster outside an entry")
            else:
                current.poster_url = poster.group(1)
            continue

        season = SEASON_PATTERN.match(line)
        if season:
            if current is None:
                warnings.append(f"line {index}: Season outside an entry")
                continue
            current_season = SeasonEntry(number=int(season.group(1)))
            current.seasons.append(current_season)
            continue

        episode = EPISODE_PATTERN.match(line)
        if episode:
            if current_season is None:
                warnings.append(f"line {index}: Episode outside a season")
                continue
            current_season.episodes.append(EpisodeEntry(number=int(episode.group(1)), url=episode.group(2)))
            continue

        title, separator, rest = line.partition(":")
        title = title.strip()
        rest = rest.strip()
        if not separator:
            warnings.append(f"line {index}: unrecognized top-level line: {line!r}")
            continue
        if title.upper() in ARCHIVE_NAMES:
            if ARCHIVE_NAMES[title.upper()] == "banners":
                banners_url = rest or banners_url
            else:
                fonts_url = rest or fonts_url
            current = None
            current_season = None
            continue
        current = MediaEntry(title=title)
        media.append(current)
        current_season = None

    return ContentManifest(media=media, banners_url=banners_url, fonts_url=fonts_url, warnings=warnings)
