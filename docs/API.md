API.md

---

title: REST API Specification
project: Hibiki
version: 1.0.0
status: Draft
owner: Rohan
last_updated: 2026-08-02

Hibiki REST API

Purpose

This document defines the REST API exposed by the Hibiki backend.

The frontend communicates exclusively through these endpoints.

The frontend must never access the filesystem or database directly.

---

Design Principles

The API should be:

- RESTful
- Versioned
- Stateless
- Predictable
- Consistent
- Well documented

All endpoints return JSON unless explicitly stated otherwise. Indexed media file and subtitle routes return local file responses and are only reachable through `/player/source/{episodeId}` references.

---

Base URL

http://localhost:8000/api/v1/

The host and port should be configurable.

---

Standard Response

Successful response:

{
  "success": true,
  "data": {}
}

---

Error response:

{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message"
  }
}

---

HTTP Status Codes

Use standard HTTP status codes.

Examples:

Code| Meaning
200| Success
201| Resource Created
204| No Content
400| Invalid Request
401| Authentication Required
403| Permission Denied
404| Resource Not Found
409| Conflict
422| Validation Error
429| Rate Limited
500| Internal Server Error

---

Security

Every response carries hardening headers:

- X-Content-Type-Options: nosniff
- X-Frame-Options: SAMEORIGIN
- Referrer-Policy: no-referrer
- Permissions-Policy: camera=(), microphone=(), geolocation=()
- Content-Security-Policy: default-src 'self'; frame-src http: https: (Teacher Mode iframe)

State-changing requests (POST / PUT / PATCH / DELETE) that include an Origin
header are rejected with 403 CROSS_ORIGIN_DENIED unless the origin matches the
Host header. Requests without an Origin header are unaffected.

The login endpoint enforces a sliding-window rate limit: after 5 failed
attempts per username and client address, further attempts return
429 RATE_LIMITED until the oldest failure leaves the 15-minute window. A
successful login resets the counter.

Expired sessions are pruned at startup and on every login and logout.

---

Authentication

POST

/auth/login

Authenticate a local user.

---

POST

/auth/logout

Terminate the current session.

---

GET

/auth/session

Return the currently authenticated user.

---

Users

GET

/users/me

Return the current user profile.

---

GET

/users

Administrator only.

Return all local users.

---

POST

/users

Administrator only.

Create a new local user.

---

DELETE

/users/{id}

Administrator only.

Remove a local user.

---

Library

GET

/library

Return the media library. Optional parameters:

- query — matches entry titles, episode titles/numbers, and season numbers (case-insensitive)
- category — `all` (default), `anime`, `movies`, `tutorials`, `other`
- sort — `default` (canonical category order), `recent` (newest scanned first), `title` (A–Z)

Unsupported category/sort values return 422. Local filesystem paths are never returned; episodes carry no file paths in the public payload.

---

GET

/library/{animeId}

Return information for a single entry (anime, movie, tutorial, or other).

---

GET

/library/{animeId}/seasons

Return available seasons.

---

GET

/library/{animeId}/episodes

Return available episodes.

---

GET

/library/search

Alias of GET /library; accepts the same query / category / sort parameters.

---

Playback

GET

/player/source/{episodeId}

Return media information required for playback. The response contains episode-specific file and subtitle routes; local filesystem paths are never returned.

GET

/player/file/{episodeId}

Stream an indexed MP4 episode after validating its configured library root.

GET

/player/subtitle/{episodeId}/{subtitleIndex}

Return an indexed WebVTT subtitle file.

Metadata-only placeholder entries (created before media is scanned in, see ASSETS.md) have no indexed file. For these, `/player/source` and `/player/file` return 404 with `Episode media is not available locally` until a library scan indexes real media.

---

POST

/player/progress

Save playback progress. Positive positions update Continue Watching; `completed: true` adds Watch History and removes the Continue Watching item.

---

GET

/player/progress/{episodeId}

Return saved playback progress.

---

Continue Watching

GET

/continue

Return Continue Watching items.

---

DELETE

/continue/{episodeId}

Remove an item from Continue Watching.

---

Banners

GET

/banners

Return the application banner collection as public asset URLs (decorative; no authentication).

---

Posters

GET

/library/{animeId}/poster

Serve an indexed poster image after root validation (D-015). Returns 404 when the entry has no indexed poster.

---

GET

/library/{animeId}/banner

Serve an indexed banner image after root validation. Returns 404 when the entry has no indexed banner.

---

Favorites

GET

/favorites

Return favorite anime.

---

POST

/favorites/{animeId}

Add favorite.

---

DELETE

/favorites/{animeId}

Remove favorite.

---

Watch History

GET

/history

Return watch history.

---

DELETE

/history

Clear watch history.

---

Dashboard

Administrator only.

GET

/dashboard

Return dashboard information.

---

GET

/dashboard/status

Return library and system statistics (anime, movies, tutorials, other, episodes, posters, banners, database size).

---

GET

/dashboard/config

Return the current application configuration (media_root).

---

POST

/dashboard/config

Update the media root (a relative folder name or an absolute path; invalid values return 422). Persists to config.json and starts a background scan of the new root.

---

GET

/dashboard/library

Return the raw library metadata including local paths (administrator management only; paths never cross the public API boundary).

---

PATCH

/dashboard/anime/{animeId}

Edit metadata (title, description, year, genre, studio). The edit is written to the title's `info.json` (the filesystem source of truth) and applied to the cached library immediately, so a rescan keeps it.

---

POST

/dashboard/database/refresh

Run a database integrity check, foreign-key check, and prune dangling anime/episode references.

---

POST

/dashboard/library/scan

Start a background library scan. Returns the scan state (`scanning`); it does not block. Poll GET /dashboard/scan/status until the state leaves `scanning`.

---

GET

/dashboard/scan/status

Return the current scan state: status (`idle` | `scanning` | `error`), started/finished timestamps, entry and episode counts, and up to 100 warnings (missing assets, invalid names, duplicate numbers, misplaced files). Warnings never fail the scan.

---

POST

/dashboard/thumbnails

Generate missing thumbnails. Currently returns guidance to run scripts/generate_thumbnails.py; generated thumbnails are discovered by the scanner.

---

Settings

GET

/settings

Return current settings.

---

PUT

/settings

Update settings. Unknown setting keys are silently dropped; only the allowed keys (`theme`, `default_volume`, `default_speed`, `subtitles_default`, `reduce_motion`, `welcome_screen`, `teacher_shortcut`, `reading_page`) are stored.

---

Health

GET

/health

Return backend health information.

Used by diagnostics.

---

Version

GET

/version

Return application version information.

---

Permissions

Mochi

Full access.

Can access every endpoint.

---

E-Mochi

Limited access.

Cannot:

- Create users
- Delete users
- Change application configuration
- Manage library
- Run maintenance tools

---

Validation

Every endpoint should validate:

- Input
- Required fields
- Permissions
- Resource existence

Invalid requests should return descriptive error messages.

---

Rate Limiting

Version 1 operates locally.

Traditional rate limiting is unnecessary.

However, endpoints should still protect against accidental rapid repeated requests where appropriate.

---

Future API

Potential future endpoints:

- Metadata import
- Plugin API
- Theme API
- Diagnostics API
- Backup API
- Collection management

These are outside the scope of Version 1.

---

API Principles

Every endpoint should satisfy the following:

- Clear purpose
- Consistent naming
- Predictable responses
- Proper validation
- Secure authorization
- Comprehensive error handling

The API should remain stable so the frontend can evolve independently from the backend implementation.
