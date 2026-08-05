DATABASE.md

---

title: Database Design
project: Hibiki
version: 1.0.0
status: Active
owner: Rohan
last_updated: 2026-08-02

Hibiki Database Design

Purpose

This document defines how Hibiki stores and manages persistent data.

Version 1 intentionally separates static application data from dynamic user data to improve maintainability, portability, and performance.

---

Storage Strategy

Hibiki uses two storage systems.

JSON

Stores application metadata.

Examples:

- Anime
- Seasons
- Episodes
- Posters
- Thumbnails
- Configuration

JSON files are human-readable and easy to edit.

---

SQLite

Stores dynamic user information.

Examples:

- Continue Watching
- Watch History
- Favorites
- Settings
- Local password hash

SQLite is selected because it is lightweight, reliable, serverless, and cross-platform.

---

Data Ownership

Application metadata belongs in JSON.

User activity belongs in SQLite.

The same information must never be stored in both locations.

Each dataset should have one authoritative source.

---

JSON Structure

Recommended structure:

data/
└── library.json

Application configuration is stored separately at `config/config.json`.

---

library.json

Stores the media library cache built by the scanner (the filesystem is the
source of truth; this file is regenerated and may be deleted safely).

Version 2 structure:

- version (2)
- scanned_at (ISO-8601 UTC)
- media_root (the configured media root, e.g. "contents")
- entries (list of titles)
- signatures (map of video path -> [mtime_ns, size] used for incremental rescans)

Each entry contains:

- Identifier
- Type (anime | movies | tutorials | other | tv-shows | courses)
- Title
- Poster (path, optional)
- Banner (path, optional)
- Description / Year / Genre / Studio (optional, from info.json)
- Seasons (anime only)

Each season contains:

- Season number
- Episodes

Each episode contains:

- Episode number
- Title
- Video path
- Subtitle paths
- Thumbnail path

Metadata edits made in the dashboard are written to `info.json` next to the
title's folder, so a rescan keeps them. `library.json` is gitignored.

---

config.json

Stores application configuration.

Examples:

- Media root (default "contents"; a relative folder name or an absolute path)
- Player preferences
- Theme
- Dashboard settings

---

SQLite Database

Recommended database file:

data/database.db

---

Tables

favorites

Stores favorited anime.

Fields include:

- id
- anime_id
- created_at

---

continue_watching

Stores playback progress.

Fields include:

- id
- anime_id
- season_number
- episode_number
- playback_position
- updated_at

---

watch_history

Stores previously watched episodes.

Fields include:

- id
- anime_id
- season_number
- episode_number
- watched_at

---

settings

Stores user preferences.

Examples:

- Volume
- Subtitle preference
- Playback speed
- Welcome screen preference

---

Relationships

The local password hash and user activity are stored in SQLite. Media entry identifiers stored in SQLite reference entries defined in `library.json`; dangling references are removed by dashboard maintenance.

---

Indexing Strategy

Indexes should exist for:

- Anime identifier
- Episode identifier
- Watch history timestamps
- Favorites
- Continue Watching

Indexes should improve lookup speed without unnecessary duplication.

---

File Organization

config/
└── config.json

data/
├── library.json
└── database.db

---

Media Organization

contents/                 # configurable media root (default "contents")
├── Anime/                # one folder per title
│   └── Title/
│       ├── info.json     # optional metadata (title, description, year, genre, studio)
│       ├── poster.webp   # optional
│       ├── banner.webp   # optional
│       ├── Season 01/    # "Season 1", "S01", or "1" all work
│       │   ├── 1.mp4     # any supported video extension; names: 1, EP 1, E01, or unnamed
│       │   ├── 1.vtt     # optional subtitle
│       │   └── 1.webp    # optional episode thumbnail
│       └── Season 02/
├── Movies/               # one video per title (direct file or folder)
├── Tutorials/            # same rules as Movies
├── Other/                # same rules as Movies
├── TV Shows/             # same standalone rules
└── Courses/              # same standalone rules

The scanner builds the library from this tree deterministically:
- Anime: title folders with numbered seasons/episodes.
- Movies/Tutorials/Other/TV Shows/Courses: each video file (or single-video folder) is one
  standalone title; standalone entries are playable as a single episode.
The scan runs in the background (POST /dashboard/library/scan, progress via
GET /dashboard/scan/status) and is incremental via the signature map.

---

Thumbnail Generation

Episode thumbnails are generated with scripts/generate_thumbnails.py (an FFmpeg
frame capture stored as a WebP next to the episode) and are discovered by the
scanner; the scan itself never spawns FFmpeg.

Recommended capture point:

3–10 seconds into the video.

Generated thumbnails should be stored alongside the corresponding episode.

---

Data Integrity

The backend is responsible for:

- Validating JSON
- Preventing duplicate identifiers
- Verifying media paths
- Detecting missing files
- Maintaining referential consistency

SQLite and JSON should remain synchronized through backend validation.

---

Backup Strategy

User data should be recoverable by backing up:

- database.db
- library.json
- config.json

The media library itself should be backed up separately.

---

Migration Strategy

Future schema changes should use versioned migrations.

Database migrations should preserve existing user data whenever possible.

JSON structure changes should remain backward compatible where practical.

---

Database Principles

The storage layer should prioritize:

- Simplicity
- Reliability
- Readability
- Maintainability
- Performance
- Data integrity

Application metadata and user-generated data should remain clearly separated throughout the lifetime of the project.
