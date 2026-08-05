ARCHITECTURE.md

---

title: Software Architecture
project: Hibiki
version: 1.0.0
status: Active
owner: Rohan
last_updated: 2026-08-02

Hibiki — Software Architecture

1. Purpose

This document defines the overall software architecture of Hibiki.

It describes the major system components, their responsibilities, communication flow, and architectural principles.

Implementation details belong in the source code and technical documentation.

---

2. Architectural Goals

The architecture is designed to provide:

- Simplicity
- Maintainability
- Performance
- Offline-first operation
- Modularity
- Security
- Scalability
- Clear separation of concerns

Every component should have a single responsibility.

---

3. High-Level Architecture

                    User
                      │
                      ▼
           Frontend (HTML + CSS + modern JavaScript modules)
                      │
                 Local REST API
                      │
            Python Backend Services
                      │
     ┌───────────────┼────────────────┐
     │               │                │
     ▼               ▼                ▼
 Media Library    SQLite DB      JSON Metadata
     │               │                │
     └───────────────┼────────────────┘
                     ▼
              Local File System

The frontend never interacts directly with the filesystem.

All filesystem access is performed through the backend.

---

4. Architectural Style

Hibiki follows a layered architecture.

Layers:

1. Presentation Layer
2. API Layer
3. Service Layer
4. Data Layer
5. Storage Layer

Each layer communicates only with the layer directly beneath it.

---

5. Frontend Responsibilities

The frontend is responsible for:

- Rendering the interface
- Managing user interactions
- Displaying media
- Navigation
- Player controls
- Theme rendering
- Accessibility
- API communication

The frontend must not contain business logic related to media management or persistence.

---

6. Backend Responsibilities

The backend is responsible for:

- Library scanning
- Metadata management
- Authentication
- Settings management
- Watch history
- Favorites
- Continue Watching
- Thumbnail discovery and fallback handling
- File validation
- JSON management
- SQLite operations

The backend acts as the single source of truth for application data.

---

7. Storage Architecture

JSON

Stores relatively static data.

Examples:

- Library metadata
- Anime information
- Seasons
- Episodes
- Configuration

SQLite

Stores dynamic user data.

Examples:

- Watch history
- Continue Watching
- Favorites
- Local settings and the password hash
- User preferences

---

8. Media Library

The media library is organized on the local filesystem; the filesystem is the
single source of truth.

Recommended structure:

contents/                    # configurable media root (default "contents")
 ├── Anime/
 │    └── Anime Name/
 │         ├── info.json      # optional metadata (title, description, year, genre, studio)
 │         ├── poster.webp    # optional
 │         ├── banner.webp    # optional
 │         ├── Season 01/     # "Season 1", "S01", or "1" all work
 │         │      ├── 1.mp4   # episodes: 1, EP 1, episode 1, E01, S2E5, or unnamed
 │         │      ├── 1.vtt
 │         │      ├── 2.mp4
 │         │      └── ...
 │         └── Season 02/
 ├── Movies/                  # one video per title (direct file or folder)
 ├── Tutorials/               # same rules as Movies
 ├── Other/                   # same rules as Movies
 ├── TV Shows/                # same standalone rules
 └── Courses/                 # same standalone rules

The scanner walks this tree and builds data/library.json as a cache.

---

9. Library Scanner

The scanner (backend/app/scanner.py) is responsible for:

- Discovering media (Anime/Movies/Tutorials/Other/TV Shows/Courses categories)
- Parsing episode numbers and cleaning titles
- Reading optional info.json metadata and poster/banner images
- Writing the versioned library.json cache
- Incremental rebuilds via a path -> [mtime_ns, size] signature map
- Reporting warnings (missing assets, invalid names, duplicates, misplaced media)

Scans run in a background thread (POST /dashboard/library/scan, progress via
GET /dashboard/scan/status) so they never block the API or the player.
Thumbnail generation is a separate optional script
(scripts/generate_thumbnails.py) and never runs FFmpeg during a scan.

---

10. Player Architecture

The playback engine uses the browser's native media capabilities while exposing a fully custom user interface.

Player responsibilities:

- Playback
- Seeking
- Resume
- Volume
- Fullscreen
- Subtitle switching
- Keyboard shortcuts
- Progress tracking

Playback state should be synchronized with the backend.

---

11. Dashboard

The dashboard is isolated from normal viewing.

Responsibilities:

- Media management
- Configuration
- Settings
- Library maintenance

Authentication is required before access is granted.

---

12. Authentication

Version 1 uses local authentication only.

Requirements:

- Password hashing
- Unlock state validation
- Protected routes
- No plaintext passwords

Authentication is an in-process local password gate; no online accounts or persisted sessions exist in Version 1.

---

13. API Architecture

Communication between frontend and backend occurs exclusively through REST endpoints.

API design principles:

- Stateless requests
- Consistent responses
- Predictable naming
- Versioned endpoints
- Structured error handling

API implementation details belong in "API.md".

---

14. Configuration Architecture

Application behavior is configuration-driven.

Configuration includes:

- Library locations
- Theme
- Player options
- Dashboard preferences

Configuration should remain external to the application code whenever practical.

---

15. Error Handling

Errors should be:

- Logged
- Recoverable where possible
- Human-readable
- Consistent

Unexpected failures should not crash the application when graceful recovery is possible.

---

16. Logging

The backend maintains local application logs.

Logs should include:

- Startup events
- Library scans
- Media errors
- Authentication events
- Unexpected exceptions

Sensitive information must never be written to logs.

---

17. Security Boundaries

The frontend is considered an untrusted client.

Only the backend may:

- Access the filesystem
- Modify metadata
- Update user data
- Authenticate users
- Write configuration

This separation simplifies maintenance and improves security.

---

18. Extensibility

Future functionality should be added through new modules rather than modifying existing ones.

Examples:

- Additional media types
- Metadata providers
- Plugin system
- Multiple user profiles
- Theme support

The architecture should favor extension over modification.

---

19. Dependency Philosophy

Dependencies should be kept to a minimum.

New libraries should only be introduced when they provide significant long-term value.

Preference is given to:

- Stable
- Well-maintained
- Lightweight
- Open-source
- Cross-platform libraries

---

20. Quality Attributes

The architecture prioritizes:

- Maintainability
- Reliability
- Performance
- Simplicity
- Security
- Portability
- Accessibility
- Testability

No single quality attribute should unnecessarily compromise another.

---

21. Architectural Principles

Every architectural decision should satisfy the following questions:

- Does it reduce complexity?
- Does it improve maintainability?
- Does it preserve performance?
- Does it isolate responsibilities?
- Does it support future growth?

If the answer is no, the decision should be reconsidered.

---

22. Architecture Statement

Hibiki is designed as a modular, offline-first streaming application with a clear separation between presentation, business logic, and storage.

The architecture emphasizes long-term maintainability, predictable behavior, and clean engineering practices while remaining lightweight enough for personal self-hosted deployments.
