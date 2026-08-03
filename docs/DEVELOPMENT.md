DEVELOPMENT.md

---

title: Development Guide
project: Hibiki
version: 1.0.0
status: Active
owner: Rohan
last_updated: 2026-08-02

Hibiki Development Guide

Purpose

This document defines the engineering workflow, coding standards, repository conventions, and development practices for Hibiki.

Every contributor and AI coding agent should follow this guide before modifying the project.

---

Development Philosophy

Hibiki values:

- Simplicity
- Maintainability
- Readability
- Performance
- Security
- Consistency

The objective is to build software that remains understandable years after Version 1.

---

Repository Structure

/
├── assets/
├── backend/
├── config/
├── contents/          # user media root (gitignored; created on first run)
├── data/
├── docs/
├── frontend/
├── scripts/
├── README.md
└── LICENSE

Each directory should have a clearly defined responsibility.

---

Folder Responsibilities

assets/

Static project assets.

Examples:

- Fonts
- Icons
- Images
- Banners
- UI graphics

---

backend/

Python application.

Contains:

- API
- Authentication
- Library scanner
- Database layer
- Business logic
- Utilities

---

frontend/

User interface.

Contains:

- HTML
- CSS
- Modern JavaScript (ES modules)
- Components
- Pages
- Player

---

config/

Application configuration.

Examples:

- Default settings
- Environment configuration
- Paths

---

data/

Persistent application data.

Contains:

- JSON
- SQLite database

---

contents/

Local media library (the user's media root; gitignored).

Contains:

- Category folders (Anime, Movies, Tutorials, Other)
- Videos
- Posters
- Banners
- Subtitles
- info.json metadata files
- Episode thumbnails

---

scripts/

Development utilities.

Examples:

- Library scanner
- Thumbnail generator
- Media validator
- Maintenance tools

---

Coding Standards

Code should be:

- Modular
- Predictable
- Readable
- Well named
- Consistent

Avoid clever solutions when a simpler solution exists.

---

Naming Conventions

Use descriptive names.

Examples:

Good

watchHistory
continueWatching
generateThumbnail
libraryScanner

Avoid abbreviations that reduce readability.

---

Function Guidelines

Functions should:

- Perform one task
- Have a clear name
- Be short
- Avoid side effects where practical

Prefer composition over large functions.

---

File Size Guidelines

Large files should be split into smaller modules.

Approximate targets:

- Functions: small and focused
- Classes: one responsibility
- Modules: one feature

Readability is more important than strict line counts.

---

Frontend Guidelines

Frontend responsibilities:

- Rendering
- User interaction
- Accessibility
- Animation
- API communication

Business logic should remain in the backend whenever possible.

---

Backend Guidelines

Backend responsibilities:

- Business logic
- Authentication
- Validation
- Media scanning
- Database access
- Configuration

Keep API handlers thin by delegating work to services.

---

CSS Guidelines

Use design tokens whenever possible.

Avoid:

- Hardcoded colors
- Magic spacing values
- Duplicated styles

Prefer reusable utility classes and component styles.

---

JavaScript Guidelines

Prefer:

- Modern JavaScript modules
- Explicit data shapes
- Predictable modules

Avoid implicit global state and duplicated browser logic.

---

Python Guidelines

Use:

- Type hints where practical
- Clear module organization
- Small reusable functions
- Standard library first

Prefer readability over micro-optimizations.

---

Dependency Policy

Every dependency should provide clear long-term value.

Before adding a dependency, consider:

- Stability
- Maintenance
- License
- Community support
- Cross-platform compatibility

Avoid dependency duplication.

---

Error Handling

Handle errors gracefully.

Unexpected failures should:

- Produce useful logs
- Avoid application crashes
- Display understandable messages where appropriate

---

Logging

Log important events such as:

- Startup
- Library scan
- Authentication
- Configuration changes
- Errors

Do not log passwords or other sensitive information.

---

Git Workflow

Use small, focused commits.

Each commit should represent a single logical change.

Avoid combining unrelated changes.

---

Commit Message Style

Recommended format:

type: short description

Examples:

feat: add continue watching
fix: resolve subtitle loading
docs: update architecture
refactor: simplify library scanner
style: improve player layout

---

Branch Strategy

Recommended branches:

main
development
feature/*
bugfix/*
docs/*

For Version 1, development directly on "main" is acceptable for a solo project, provided commits remain small and well documented.

---

Code Review Checklist

Before considering work complete, verify:

- Code is readable.
- Naming is consistent.
- Architecture is respected.
- Existing functionality is preserved.
- No duplicated logic exists.
- Documentation is updated if required.

---

Testing Expectations

Every significant feature should be manually verified.

Minimum verification:

- Functional testing
- Regression testing
- UI validation
- Error handling
- Performance observation

Automated testing can be expanded after Version 1.

---

Documentation Workflow

When introducing significant functionality:

1. Update documentation if needed.
2. Implement the feature.
3. Verify behavior.
4. Record important architectural decisions in "DECISIONS.md".

Documentation should remain synchronized with implementation.

---

Performance Guidelines

Prioritize:

- Fast startup
- Smooth playback
- Efficient rendering
- Small assets
- Minimal memory usage

Avoid unnecessary processing during application startup.

---

Security Guidelines

Always:

- Validate input
- Hash passwords
- Limit privileges
- Protect administrator functionality
- Keep secrets out of source code

Security is part of development, not a separate phase.

---

AI Development Workflow

Before generating code, AI agents should:

1. Read the project documentation.
2. Understand the existing architecture.
3. Reuse existing modules where possible.
4. Avoid duplicate implementations.
5. Update documentation when making significant architectural changes.

AI should enhance the existing project rather than replace established patterns.

---

Definition of Complete

A task is complete only when:

- Requirements are satisfied.
- Code follows project conventions.
- Documentation is accurate.
- Existing functionality remains stable.
- No obvious technical debt has been introduced.

Quality should always take precedence over speed.
