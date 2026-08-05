MEMORY_BANK.md

---

title: Memory Bank
project: Hibiki
version: 1.0.0
status: Active
owner: Rohan
last_updated: 2026-08-02

Hibiki Memory Bank

Purpose

This document stores the long-term memory of the project.

It contains important project decisions, conventions, and assumptions that future contributors and AI coding agents must remember throughout development.

Only stable information belongs here.

Temporary notes, bugs, ideas, or experiments should not be stored in this document.

---

Project Identity

Project Name

Hibiki

Project Type

Offline-first self-hosted streaming application.

Primary Focus

Local personal media libraries.

Development Philosophy

Professional software engineering practices with strong emphasis on maintainability, simplicity, performance, and documentation.

---

Version 1 Vision

Version 1 aims to deliver a polished, reliable, and maintainable streaming application.

The goal is quality rather than feature quantity.

Every feature should feel complete before moving to the next.

---

Design Identity

Visual Style

- Modern Brutalism
- Japanese Editorial Design
- Cinematic Presentation
- Minimal Interface
- High Contrast

Primary Theme

Dark

Accent Color

Deep Crimson Red

Primary Background

Charcoal Black

Corner Radius

4–6 px

---

Typography

Primary UI

Inter

Display

Anton

Japanese

Noto Sans JP

---

Icons

Library

Text-first controls

Icons should remain minimal and never replace readable text.

---

Supported Platforms

Primary

Windows

Supported

- Linux
- macOS

Docker is intentionally excluded from Version 1.

---

Technology Stack

Frontend

- HTML5
- CSS3
- Modern JavaScript (ES modules)

Backend

- Python

Data Storage

- JSON
- SQLite

Media

- MP4
- WebP
- WebVTT

---

Core Principles

The project should always prioritize:

- Simplicity
- Performance
- Maintainability
- Privacy
- Accessibility
- Consistency
- Modularity

---

Media Library

The application is designed around local media.

Media should be organized into:

Anime

Season

Episode

The backend is responsible for scanning and indexing media.

---

Player

The player should present a fully custom interface while relying on the browser's media playback engine.

Default browser controls should not be used.

---

Dashboard

The dashboard is intended for local administration only.

It must remain password protected.

Passwords must never be stored in plaintext.

---

Teacher Mode

Teacher Mode is a core feature.

Activation methods:

- Teacher Mode button
- Any keyboard key

Random mouse clicks must not activate Teacher Mode.

Playback progress should be preserved when entering or leaving Teacher Mode.

---

Welcome Experience

The application opens with a cinematic welcome screen.

Backgrounds rotate randomly from the local banner collection.

A swipe-up interaction transitions the user into the main interface.

---

Background System

Background images should:

- Randomize each session
- Use a dark overlay
- Use a bottom-to-top black gradient
- Preserve readability

Backgrounds are decorative and must never reduce usability.

---

Performance Guidelines

Prefer:

- Small assets
- Fast rendering
- Efficient loading
- Minimal dependencies

Avoid unnecessary visual effects that negatively impact responsiveness.

---

Documentation Rules

Documentation is considered part of the product.

Major architectural or product decisions should be reflected in the documentation before implementation.

Documentation should remain synchronized with the codebase.

---

Coding Standards

Code should be:

- Readable
- Modular
- Predictable
- Well documented
- Self-explanatory

Business logic must remain separate from presentation logic.

---

Dependency Philosophy

Prefer dependencies that are:

- Stable
- Lightweight
- Well maintained
- Cross-platform
- Open source

Avoid introducing new dependencies without a clear technical benefit.

---

AI Development Rules

AI coding agents should:

- Read all documentation before generating code.
- Follow existing architecture.
- Reuse existing components before creating new ones.
- Avoid duplicate logic.
- Prefer maintainability over clever solutions.
- Update documentation when making significant architectural changes.

AI should implement documented decisions rather than invent new product behavior.

---

Source of Truth

Documentation priority:

1. PRD.md
2. TRD.md
3. ARCHITECTURE.md
4. DESIGN.md
5. Remaining project documentation

When documentation conflicts, the higher-priority document takes precedence until the conflict is resolved.

---

Memory Update Policy

This document should only change when long-term project knowledge changes.

Routine implementation details, temporary experiments, debugging notes, and short-lived decisions should be stored in other project documents instead.

The goal is to keep this document concise, stable, and useful throughout the lifetime of the project.
