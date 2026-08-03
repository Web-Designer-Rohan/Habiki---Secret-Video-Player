FEATURES.md

---

title: Feature Specification
project: Hibiki
version: 1.0.0
status: Active
owner: Rohan
last_updated: 2026-08-02

Hibiki Feature Specification

Purpose

This document tracks all planned, implemented, and future features of Hibiki.

Features are grouped by category and development status.

Version 1 prioritizes a polished, stable, and maintainable experience over feature quantity.

---

Version 1 Core Features

Authentication

Status: Complete

Features:

- Local login
- Multiple local users
- Role-based access control
- Secure password hashing
- Local session management

Roles:

Mochi (Administrator)

Permissions:

- Manage library
- Manage metadata
- Manage posters
- Manage banners
- Configure application settings
- Manage users
- Run library scans
- Generate thumbnails
- Access maintenance tools
- View application logs

E-Mochi (Member)

Permissions:

- Watch media
- Continue Watching
- Favorites
- Watch History
- Subtitle selection
- Audio selection (future)
- Playback settings
- Language selection

Members cannot modify the media library or application configuration.

---

Library

Status: In Progress

Features:

- Automatic library scanning
- Anime browsing
- Season selection
- Episode selection
- Posters
- Episode thumbnails
- Local metadata
- Fast searching
- Season and episode browsing in the library UI

---

Video Player

Status: In Progress

Features:

- Custom interface
- Play/Pause
- Seeking
- Volume control
- Fullscreen
- Subtitle selection
- Playback speed
- Resume playback
- Keyboard shortcuts
- Auto-hide controls

---

Continue Watching

Status: Complete

Features:

- Automatic playback progress
- Resume from last position
- Recently watched list

---

Favorites

Status: Complete

Features:

- Favorite anime
- Quick access
- Favorite persistence

---

Watch History

Status: Complete

Features:

- Recently watched episodes
- Playback timestamps
- Viewing history

---

Teacher Mode

Status: Planned

Purpose:

Provide an immediate alternative reading interface while preserving the current playback state.

Activation:

- Teacher Mode button
- Configurable keyboard shortcut

Features:

- Preserve playback position
- Instant transition
- Return to playback without losing progress

---

Dashboard

Status: Planned

Administrator features:

- Library management
- Metadata editing
- Banner management
- Poster management
- User management
- Application settings
- Library scan
- Thumbnail generation
- Diagnostics

---

Welcome Screen

Status: In Progress

Features:

- Random banner
- Swipe-up interaction
- Smooth transition
- Configurable display

---

Background System

Status: Planned

Features:

- Random background
- Dark overlay
- Bottom-to-top gradient
- Session randomization

---

Localization

Status: In Progress

Languages:

- Hindi
- English
- Japanese

Future languages should be easy to add.

---

Settings

Status: Planned

User settings:

- Language
- Subtitle preference
- Playback speed
- Volume
- Welcome screen preference

Administrator settings:

- Library paths
- Application configuration
- Media scanning options

---

Media Management

Status: In Progress

Features:

- Library scan
- Metadata validation
- Missing file detection
- Thumbnail generation
- Configuration management

The asset and validation pipeline (scripts/import_assets.py, build_library.py, generate_thumbnails.py, validate_library.py, project_size.py) is implemented; dashboard wiring is pending.

---

Accessibility

Status: In Progress

Features:

- Keyboard navigation
- Semantic HTML
- Visible focus indicators
- High contrast
- Reduced motion support

---

Performance

Status: Planned

Goals:

- Fast startup
- Smooth playback
- Efficient rendering
- Low memory usage
- Optimized assets

---

Security

Status: In Progress

Features:

- Local authentication
- Role-based authorization
- Password hashing
- Input validation
- Secure session handling

---

Deferred Features

These are intentionally postponed beyond Version 1:

- Theme customization
- Plugin system
- Metadata import providers
- Multi-profile enhancements
- Advanced player skins
- Additional localization
- Remote control support
- Cloud synchronization

---

Feature Status Legend

- Planned
- In Progress
- Complete
- Deferred
- Removed

Every feature should move through these states during development.

---

Version 1 Definition of Done

Version 1 is complete when:

- Local authentication is operational.
- Mochi and E-Mochi roles function correctly.
- Local media playback is reliable.
- Continue Watching works.
- Favorites work.
- Watch History works.
- The Dashboard is fully functional.
- The custom player is complete.
- Library scanning functions correctly.
- Documentation is synchronized with implementation.
- The application operates fully offline on supported platforms.

---

Feature Philosophy

Every new feature must satisfy the following questions before implementation:

- Does it improve the user experience?
- Does it align with the project vision?
- Can it be maintained long term?
- Does it preserve performance?
- Does it avoid unnecessary complexity?

If the answer is no, the feature should be deferred or rejected.
