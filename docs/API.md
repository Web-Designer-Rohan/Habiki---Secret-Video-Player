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
500| Internal Server Error

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

Return the complete media library.

---

GET

/library/{animeId}

Return information for a single anime.

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

Search the local library.

Supported parameters:

- query
- genre (future)
- sort
- page
- limit

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

Metadata-only placeholder episodes (created when media is not yet imported, see ASSETS.md) have no indexed file. For these, `/player/source` and `/player/file` return 404 with `Episode media is not available locally` until a library scan indexes real media.

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

POST

/dashboard/library/scan

Run a library scan.

---

POST

/dashboard/thumbnails

Generate missing thumbnails.

---

POST

/dashboard/config

Update configuration.

---

POST

/dashboard/library/reload

Reload the media library.

---

Settings

GET

/settings

Return current settings.

---

PUT

/settings

Update settings.

---

Localization

GET

/languages

Return available languages.

---

POST

/language

Update the active language.

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
