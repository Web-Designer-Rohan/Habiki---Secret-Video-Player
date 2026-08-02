DECISIONS.md

---

title: Architecture Decision Log
project: Hibiki
version: 1.0.0
status: Active
owner: Rohan
last_updated: 2026-08-02

Hibiki Decision Log

Purpose

This document records significant architectural, product, and engineering decisions made during the development of Hibiki.

Each decision should explain:

- What was decided
- Why it was chosen
- The expected long-term impact

Decisions should never be silently replaced. If a decision changes, add a new entry referencing the previous one.

---

Decision Format

Every new decision should follow this structure:

## D-XXX

Date:
Status:
Category:

Decision:

Reason:

Consequences:

---

D-001

Date

2026-08-02

Status

Accepted

Category

Project

Decision

The project name will be Hibiki.

Reason

The name is short, memorable, Japanese-inspired, easy to pronounce, and aligns with the visual identity of the application.

Consequences

The name will be used throughout documentation, repository structure, and future releases.

---

D-002

Date

2026-08-02

Status

Accepted

Category

Product

Decision

Hibiki will be an offline-first, self-hosted application.

Reason

Offline operation provides maximum privacy, reliability, portability, and independence from external services.

Consequences

All Version 1 functionality must work without an internet connection after installation.

---

D-003

Date

2026-08-02

Status

Accepted

Category

Technology

Decision

The frontend will use:

- HTML5
- CSS3
- Modern JavaScript (ES modules)

without Node.js, npm, or Docker in Version 1.

Reason

The project targets lightweight local deployments with minimal dependencies.

Consequences

Build complexity remains low and installation is simplified.

---

D-004

Date

2026-08-02

Status

Accepted

Category

Backend

Decision

Python will be the backend technology.

Reason

Python provides excellent cross-platform support, a strong standard library, and is well suited for media management and local automation.

Consequences

All filesystem operations, metadata management, authentication, and database access are handled by Python.

---

D-005

Date

2026-08-02

Status

Accepted

Category

Storage

Decision

Application data is divided between JSON and SQLite.

Reason

JSON is ideal for static metadata, while SQLite efficiently stores dynamic user information.

Consequences

Application metadata and user-generated data remain clearly separated.

---

D-006

Date

2026-08-02

Status

Accepted

Category

Authentication

Decision

Version 1 uses local authentication with role-based access control.

Roles:

- Mochi (Administrator)
- E-Mochi (Member)

Reason

Role-based access provides better scalability and security than a single dashboard password.

Consequences

Administrator functionality is protected while members retain personal viewing features.

---

D-007

Date

2026-08-02

Status

Accepted

Category

User Experience

Decision

A fully custom video player interface will be implemented.

Reason

A custom player provides a more cohesive experience than default browser controls while allowing tighter integration with Hibiki's design language.

Consequences

Playback uses browser media capabilities while exposing a custom interface.

---

D-008

Date

2026-08-02

Status

Accepted

Category

Design

Decision

The design language combines modern Brutalism with Japanese editorial aesthetics.

Reason

This visual identity creates a bold, memorable interface while remaining functional and readable.

Consequences

All future interface components should follow this design direction.

---

D-009

Date

2026-08-02

Status

Accepted

Category

Design System

Decision

Typography is standardized as:

- Inter
- Anton
- Noto Sans JP

Reason

The combination offers excellent readability, impactful headings, and strong Japanese language support.

Consequences

Future typography choices should remain consistent with this system.

---

D-010

Date

2026-08-02

Status

Accepted

Category

Icons

Decision

Lucide will be the primary icon library.

Reason

Lucide is lightweight, consistent, open source, and well suited to the project's minimal visual style.

Consequences

New icons should come from Lucide unless a compelling exception exists.

---

D-011

Date

2026-08-02

Status

Accepted

Category

Media

Decision

Episode thumbnails are generated automatically from the first meaningful frame, approximately 3–10 seconds into each video.

Reason

This generally avoids black frames and produces more useful previews.

Consequences

Thumbnail generation becomes part of the media import workflow.

---

D-012

Date

2026-08-02

Status

Accepted

Category

Localization

Decision

Version 1 supports:

- Hindi
- English
- Japanese

Reason

These languages match the intended audience while keeping the localization system manageable.

Consequences

The localization framework should allow additional languages in future releases.

---

D-013

Date

2026-08-02

Status

Accepted

Category

Deployment

Decision

Version 1 officially supports:

- Windows
- Linux
- macOS

Docker is intentionally excluded.

Reason

The initial release focuses on straightforward local installation without containerization.

Consequences

Installation documentation should target native operating system environments.

---

D-014

Date

2026-08-02

Status

Accepted

Category

Security and Dependencies

Decision

Local passwords use Python's standard-library scrypt hashing, and authenticated sessions use cryptographically random opaque tokens stored in SQLite and delivered through HttpOnly, SameSite cookies.

Reason

Hibiki is local-only and intentionally dependency-light. This provides password hashing and revocable sessions without adding a JWT or authentication framework dependency.

Consequences

Session cleanup, expiry, and role checks remain backend responsibilities. Password parameters must remain consistent with the implementation and should be reviewed if deployment targets change.

---

D-015

Date

2026-08-02

Status

Accepted

Category

Security and API

Decision

Library metadata returned to the frontend excludes local filesystem paths. Indexed video and subtitle files are served through episode-specific API routes that validate the configured library roots.

Reason

Absolute local paths are implementation details and should not cross the API boundary. A single indexed proxy path also supports library folders configured outside the default media directory without exposing arbitrary files.

Consequences

The frontend uses `/player/source/{episodeId}` and the returned episode-specific file routes for playback. Any future media route must preserve root validation and indexed-resource checks.

---

Future Decisions

Additional decisions should be added whenever changes affect:

- Architecture
- Security
- Storage
- Technology
- User experience
- Performance
- Accessibility
- Deployment
- Development workflow

Every accepted decision becomes part of Hibiki's long-term engineering history.
