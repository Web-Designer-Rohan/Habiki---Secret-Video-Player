# Hibiki REST API

---

title: REST API Specification
project: Hibiki
version: 1.0.0
status: Active
owner: Rohan
last_updated: 2026-08-05

## Purpose

This document describes the API implemented by the Hibiki backend. The
frontend communicates with the backend; it never reads the filesystem or
SQLite database directly.

Base URL: `http://localhost:8000/api/v1/`

Successful JSON responses use:

```json
{"success": true, "data": {}}
```

Expected errors use:

```json
{"success": false, "error": {"code": "ERROR_CODE", "message": "Human readable message"}}
```

File and image routes return a local file response instead of JSON.

## Security contract

Every response includes:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: SAMEORIGIN`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- Content Security Policy limiting resources to the application origin, with
  `frame-src http: https:` for the configured Teacher Mode reading page.

State-changing requests that include an `Origin` header must match the request
`Host`; otherwise the API returns `403 CROSS_ORIGIN_DENIED`. Requests without
an `Origin` header remain compatible with local command-line clients.

The application uses one local password gate. Passwords are hashed with
Python `scrypt`; failed unlock attempts are rate limited to five attempts per
client in a 15-minute window. The password hash is never exposed by the
settings API. Administrative and activity routes require the application to
be unlocked.

## Health and version

### `GET /health`

Returns backend health and whether the database file exists. No unlock is
required.

### `GET /version`

Returns `{ "name": "Hibiki", "version": "1.0.0" }`. No unlock is required.

## Authentication

### `GET /auth/status`

Returns whether the current process is unlocked.

### `POST /auth/unlock`

Unlocks the local application.

Request:

```json
{"password": "..."}
```

Returns `401` for an incorrect password and `429` after the rate limit is
exceeded.

### `PUT /auth/password`

Requires an unlocked application and verifies the current password before
storing a new `scrypt` hash.

Request:

```json
{"current_password": "...", "new_password": "at-least-8-characters"}
```

Returns `401` if the application is locked or the current password is wrong.

## Library

### `GET /library`

Returns the public library. Optional query parameters:

- `query` — case-insensitive title, episode, number, or season search
- `category` — `all`, `anime`, `movies`, `tutorials`, `other`, `tv-shows`, or
  `courses`
- `sort` — `default`, `recent`, or `title`

Unsupported category or sort values return `422`. Local filesystem paths are
removed from public metadata.

### `GET /library/search`

Compatibility alias of `GET /library` with the same query parameters.

### `GET /library/{entryId}`

Returns one public library entry or `404`.

### `GET /library/{entryId}/seasons`

Returns the entry's seasons or an empty list for standalone titles.

### `GET /library/{entryId}/episodes`

Returns all episodes for an entry. Standalone titles expose one episode.

### `GET /library/{entryId}/poster`

Serves an indexed poster image after validating that it remains inside the
configured media root. Returns `404` when absent.

### `GET /library/{entryId}/banner`

Serves an indexed title banner with the same root validation as posters.

### `GET /banners`

Returns application welcome-banner URLs. This decorative endpoint does not
require unlock.

## Playback

### `GET /player/source/{episodeId}`

Returns the episode-specific media URL, thumbnail URL, and subtitle URLs. A
metadata-only or missing episode returns `404` instead of an internal error.

### `GET /player/file/{episodeId}`

Streams an indexed file after checking its path, existence, and extension.
The scanner recognizes these video extensions:

`.mp4`, `.mkv`, `.webm`, `.avi`, `.mov`, `.m4v`, `.flv`, `.mpeg`, `.ts`,
`.m3u8`

Browser playback support varies by platform and codec.

### `GET /player/thumbnail/{episodeId}`

Serves an indexed episode thumbnail. If it is missing, the route falls back
to the title poster and finally to a local SVG play placeholder.

### `GET /player/subtitle/{episodeId}/{subtitleIndex}`

Serves an indexed WebVTT subtitle after validating the episode and path.

### `POST /player/progress`

Requires unlock. Saves playback progress and supports `completed: true` for
moving an episode to watch history.

Request fields:

```json
{
  "episode_id": "show-s01-e01",
  "anime_id": "show",
  "season_number": 1,
  "episode_number": 1,
  "playback_position": 42.0,
  "completed": false
}
```

### `GET /player/progress/{episodeId}`

Requires unlock. Returns saved progress or a zero position.

## Activity

All activity routes require unlock.

- `GET /continue` — list Continue Watching items.
- `DELETE /continue/{episodeId}` — remove one Continue Watching item.
- `GET /favorites` — list favorites.
- `POST /favorites/{entryId}` — add a favorite; an optional `{ "enabled": false }` body disables it.
- `DELETE /favorites/{entryId}` — remove a favorite.
- `GET /history` — list watch history.
- `DELETE /history` — clear watch history.

## Settings

All settings routes require unlock.

### `GET /settings`

Returns the persisted setting key/value pairs. Password hashes are excluded.

### `PUT /settings`

Updates the allowed settings and persists values as strings. Unknown keys are
dropped. Supported keys are:

- `theme`
- `default_volume` (`0`–`100`)
- `default_speed` (`0.25`–`4`)
- `subtitles_default`
- `reduce_motion`
- `welcome_screen`
- `teacher_shortcut`
- `reading_page` (empty, an HTTP(S) URL, or a relative path)

## Dashboard

Dashboard routes require unlock.

- `GET /dashboard` — confirms dashboard availability.
- `GET /dashboard/status` — returns category, episode, poster, banner, and database statistics.
- `GET /dashboard/config` — returns the configured `media_root`.
- `POST /dashboard/config` — validates, persists, and asynchronously scans a relative or absolute media root.
- `GET /dashboard/library` — returns raw local library metadata for administration; this is not a public browsing response.
- `PATCH /dashboard/anime/{entryId}` — writes title metadata to the entry's `info.json` and updates the cache.
- `POST /dashboard/database/refresh` — checks SQLite integrity and removes dangling activity references.
- `POST /dashboard/library/scan` — starts a background filesystem scan and returns its state.
- `GET /dashboard/scan/status` — returns scan status, timestamps, counts, and bounded warnings.

The scan is non-blocking. Poll `/dashboard/scan/status` until `status` is
`idle` or `error`; no browser refresh is required.

## Media organization

The scanner uses one configurable root with these category folders:

`Anime`, `Movies`, `Tutorials`, `Other`, `TV Shows`, and `Courses`.

Anime folders support seasons and numbered episodes. The other categories
index standalone videos. Unsupported files are skipped with warnings; scans
do not fail because a folder contains invalid or unrelated files.

## Validation and status codes

- `200` — success
- `401` — unlock required or invalid password
- `403` — cross-origin or authorization failure
- `404` — missing or unavailable resource
- `422` — invalid payload or query value
- `429` — unlock rate limit exceeded

Validation errors use `VALIDATION_ERROR` and do not expose local source paths,
stack traces, submitted secrets, or other implementation details.
