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
- Localization
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
- Thumbnail generation
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
- Dashboard credentials
- User preferences

---

8. Media Library

The media library is organized on the local filesystem.

Recommended structure:

media/
 ├── Anime Name/
 │    ├── poster.webp
 │    ├── Season 01/
 │    │      ├── Episode 01.mp4
 │    │      ├── Episode 01.vtt
 │    │      ├── Episode 02.mp4
 │    │      └── ...
 │    └── Season 02/
 └── ...

The application scans this structure to build the library.

---

9. Library Scanner

The scanner is responsible for:

- Discovering media
- Validating files
- Updating JSON metadata
- Generating thumbnails
- Detecting changes
- Reporting errors

Scanning should be incremental whenever possible.

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
- Session validation
- Protected routes
- No plaintext passwords

No online authentication exists in Version 1.

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
- Language
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
