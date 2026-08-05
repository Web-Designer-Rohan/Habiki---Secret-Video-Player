Hibiki

«A premium offline-first, self-hosted anime streaming application built for simplicity, performance, and long-term maintainability.»

---

Overview

Hibiki is an open-source local streaming application designed for personal media libraries.

Unlike traditional streaming platforms, Hibiki focuses on being lightweight, fast, and fully self-hosted while providing a polished user experience inspired by modern Japanese editorial design and brutalism.

Version 1 is designed primarily for Windows while also supporting Linux and macOS.

---

Project Goals

- Offline-first architecture
- Fast startup and smooth playback
- Beautiful and distraction-free interface
- Simple deployment
- Local media library
- Modular architecture
- High maintainability
- Excellent developer experience
- Clean documentation
- Open-source friendly

---

Features

Media

- Filesystem-driven library (single media root, default `contents/`)
- Automatic categories: Anime / Movies / Tutorials / Other / TV Shows / Courses
- Seasons and episodes (Anime)
- Standalone titles with one-click play (Movies / Tutorials / Other / TV Shows / Courses)
- Posters, banners, and episode thumbnails
- Optional info.json metadata (title, description, year, genre, studio)
- Incremental background scans with warnings
- Continue Watching
- Favorites
- Watch history

Player

- Custom video player
- Subtitle support (WebVTT)
- Keyboard shortcuts
- Resume playback
- Playback progress
- Fullscreen support

User Experience

- Swipe-up welcome screen
- Random cinematic backgrounds
- Teacher Mode
- Dashboard
- Now Watching
- Library browsing

System

- Offline-first
- Self-hosted
- Local configuration (media root, player preferences)
- Single-password local authentication (scrypt, brute-force protection)
- Automatic media scanning (background, deterministic, incremental)
- JSON library cache + info.json metadata
- SQLite user data

---

Design Philosophy

Hibiki combines:

- Modern Brutalism
- Japanese Editorial Design
- Minimal Interfaces
- High Contrast
- Strong Typography
- Cinematic Presentation

The result is a streaming experience that feels premium without unnecessary complexity.

---

Technology Stack

Frontend

- HTML5
- CSS3
- Modern JavaScript (ES modules)

Backend

- Python

Storage

- JSON
- SQLite

Media

- MP4, MKV, WebM, AVI, MOV, M4V, FLV, MPEG, TS, M3U8 (browser support varies)
- WebVTT subtitles
- WebP, PNG, JPEG artwork

Typography

- Anton
- Inter
- Noto Sans JP

---

Project Structure

assets/
backend/
config/
contents/      # user media root (gitignored; created on first run)
data/
docs/
frontend/
scripts/
README.md

---

Documentation

Project documentation is located in the "docs/" directory. Legal and privacy surfaces are available from the application footer and at `/frontend/legal.html`, `/frontend/privacy.html`, and `/frontend/attribution.html`.

Core documents include:

- PRD
- TRD
- Architecture
- Design
- Database
- API
- Features
- Development
- Decisions
- Memory Bank
- Roadmap
- Prompt Rules
- Installation
- Attribution
- Asset policy

These documents act as the project's single source of truth.

---

Privacy and offline operation

Hibiki is local-first and designed to work offline after setup. Continue Watching, Favorites, Watch History, local authentication, settings, and generated library metadata stay on the user's device. The current application has no analytics, advertising, cloud synchronization, telemetry, or user tracking. Users remain responsible for the rights to media and other assets they import.

Third-party acknowledgements

Hibiki vendors Anime.js 4.5.0 locally and uses Python, FastAPI, Uvicorn, Pydantic, SQLite, and optional FFmpeg tooling. Licenses, versions, purposes, and distribution notes are listed in `docs/ATTRIBUTION.md` and `assets/vendor/VERSIONS.md`.

---

Current Status

Current Phase

Release 1.0 — complete

The filesystem library (Anime / Movies / Tutorials / Other / TV Shows / Courses categories under a configurable media root), the background scanner with warnings and incremental rebuilds, the API, the custom player, activity persistence, metadata editing, Teacher Mode, and the dashboard are implemented, tested, and documented.

---

Version

Current Version

v1.0.0 — Final media library integration and release

---

License

Hibiki is licensed under the MIT License. See `LICENSE` for the complete terms.

---

Contributing

Contributions are welcome after the initial architecture and Version 1 foundation are complete.

Development guidelines are documented in "docs/DEVELOPMENT.md".

---

Vision

The goal of Hibiki is not to become the largest streaming application.

The goal is to become one of the cleanest, fastest, and most maintainable open-source local streaming applications built with professional software engineering practices.

Every design and engineering decision should prioritize clarity, consistency, performance, and long-term maintainability over unnecessary complexity.
