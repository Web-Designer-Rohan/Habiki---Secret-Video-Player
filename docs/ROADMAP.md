ROADMAP.md

---

title: Product Roadmap
project: Hibiki
version: 1.0.0
status: Active
owner: Rohan
last_updated: 2026-08-02

Hibiki Roadmap

Purpose

This document defines the planned evolution of Hibiki.

The roadmap is organized by releases rather than dates.

Only major milestones belong here.

Detailed implementation tasks should be tracked elsewhere.

---

Project Vision

Create a lightweight, offline-first, self-hosted anime streaming application that provides a polished user experience, professional engineering quality, and long-term maintainability.

The emphasis is on reliability and craftsmanship rather than rapid feature growth.

---

Current Status

Current Phase

Foundation implementation and library experience

Progress

- ✅ Core vision established
- ✅ Product requirements documented
- ✅ Technical requirements documented
- ✅ Architecture defined
- ✅ Design system defined
- ✅ Database strategy defined
- ✅ Engineering guidelines completed
- ✅ Backend foundation implemented
- ✅ Local authentication and roles implemented
- ✅ Media scanner and versioned library JSON implemented
- ✅ Versioned REST API foundation implemented
- ✅ Frontend shell and custom player foundation implemented
- ✅ Activity-driven player and library UI integration
- ✅ Season and episode browsing in the library UI
- ✅ Library search, filters, and sorting
- ✅ Dashboard management, metadata editing, and localization editor
- ✅ Teacher Mode and Settings
- ✅ Welcome experience (random banner, swipe-up)
- ⏳ In-app thumbnail generation (available via scripts/generate_thumbnails.py; dashboard endpoint returns guidance until FFmpeg-based generation is wired)

---

Version 1.0 — Foundation

Goal

Deliver a complete offline streaming application.

Core Platform

- Local authentication
- Mochi administrator role
- E-Mochi member role
- Session management
- Configuration system

Media Library

- Local media scanner
- Automatic library generation
- Anime browsing
- Season browsing
- Episode browsing
- Poster support
- Banner support
- Episode thumbnails

Player

- Fully custom player
- Resume playback
- Subtitle support
- Keyboard shortcuts
- Fullscreen
- Playback speed
- Continue Watching

User Features

- Favorites
- Watch history
- Continue Watching
- Recently watched
- Localization
- Settings

Dashboard

- Library management
- Metadata editing
- Banner management
- Poster management
- Thumbnail generation
- User management
- Application settings

Polish

- Smooth animations
- Responsive interface
- Accessibility improvements
- Performance optimization

Release Goal

A stable, production-quality offline application suitable for daily personal use.

---

Version 1.1 — Quality Improvements

Focus on refinement rather than expansion.

Planned improvements:

- Faster library scanning
- Improved search
- Better keyboard navigation
- Enhanced accessibility
- Additional settings
- Performance optimizations
- Reduced startup time
- UI polish

---

Version 1.2 — Library Improvements

Potential additions:

- Better metadata management
- Advanced filtering
- Genre browsing
- Studio browsing
- Improved sorting
- Recently added section

---

Version 2.0 — Extensibility

Future direction.

Possible features:

- Plugin system
- Theme support
- Multiple media libraries
- Enhanced user profiles
- Advanced dashboard
- Additional localization
- Improved customization

Only features that align with Hibiki's philosophy should be considered.

---

Long-Term Ideas

Ideas under consideration:

- Multiple administrator accounts
- Additional member permissions
- Import/export utilities
- Metadata backup
- Custom collections
- Smart playlists
- Improved media validation
- Enhanced diagnostics

These ideas are exploratory and not commitments.

---

Out of Scope (Version 1)

The following features are intentionally excluded:

- Docker deployment
- Cloud synchronization
- Online streaming services
- Account registration over the internet
- Remote administration
- Mobile applications
- Browser extensions
- AI-powered recommendations

These may be reconsidered after Version 1 if they align with the project's goals.

---

Roadmap Principles

New milestones should:

- Solve real user problems.
- Preserve the offline-first philosophy.
- Maintain high performance.
- Keep the application lightweight.
- Avoid unnecessary complexity.

Quality is always preferred over feature count.

---

Definition of Success

Version 1 is considered successful when:

- The application is stable.
- The user experience feels polished.
- Performance is smooth on supported systems.
- Documentation is complete.
- The codebase remains clean and maintainable.
- The project is easy for new contributors and AI coding agents to understand.

---

Maintaining the Roadmap

The roadmap is a living document.

Completed milestones should be marked as finished.

Future milestones should only be added after careful consideration to avoid feature creep and preserve the long-term vision of Hibiki.
