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
- Dashboard Authentication
- Sessions

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
├── library.json
├── config.json
└── localization/
    ├── en.json
    ├── hi.json
    └── ja.json

---

library.json

Stores the media library.

Each anime contains:

- Identifier
- Title
- Poster
- Banner
- Description (optional)
- Genres (future)
- Seasons

Each season contains:

- Season number
- Episodes

Each episode contains:

- Episode number
- Title
- Video path
- Subtitle paths
- Thumbnail path
- Duration

---

config.json

Stores application configuration.

Examples:

- Library paths
- Default language
- Player preferences
- Theme
- Dashboard settings

---

SQLite Database

Recommended database file:

data/database.db

---

Tables

users

Stores local users.

Fields include:

- id
- username
- password_hash
- created_at
- updated_at

---

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

- Language
- Volume
- Subtitle preference
- Playback speed
- Welcome screen preference

---

sessions

Stores dashboard sessions.

Fields include:

- session_id
- created_at
- expires_at

Version 1 may simplify session handling if appropriate.

---

Relationships

Users own:

- Favorites
- Continue Watching
- Watch History
- Settings
- Sessions

Anime identifiers stored in SQLite reference entries defined in "library.json".

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

data/
├── library.json
├── config.json
├── database.db
└── localization/

---

Media Organization

media/
├── Anime/
│   ├── poster.webp
│   ├── banner.webp
│   ├── Season 01/
│   │   ├── Episode 01.mp4
│   │   ├── Episode 01.vtt
│   │   ├── Episode 02.mp4
│   │   └── ...
│   └── Season 02/
└── ...

The backend scans this structure to build the library.

---

Thumbnail Generation

Episode thumbnails are generated automatically during library scanning.

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
