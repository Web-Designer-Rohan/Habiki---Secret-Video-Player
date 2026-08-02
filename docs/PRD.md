PRD.md

---

title: Product Requirements Document
project: Hibiki
version: 1.0.0
status: Active
owner: Rohan
last_updated: 2026-08-02

Hibiki — Product Requirements Document

1. Purpose

Hibiki is an offline-first, self-hosted streaming application built for personal media libraries.

The application focuses on providing a beautiful, fast, and distraction-free viewing experience while maintaining professional software architecture, excellent maintainability, and a premium user interface.

Hibiki is intended to be simple to use while remaining extensible for future improvements.

---

2. Vision

Create a premium-quality local streaming application that feels comparable to commercial streaming platforms while remaining lightweight, private, self-hosted, and fully controlled by the user.

The project prioritizes quality over feature quantity.

---

3. Goals

Primary goals include:

- Offline-first operation
- Fast startup
- Smooth playback
- Beautiful interface
- Minimal maintenance
- Professional architecture
- Modular design
- Long-term maintainability
- Cross-platform support
- High performance

---

4. Non-Goals (Version 1)

The following features are intentionally excluded from Version 1:

- Live streaming
- Cloud synchronization
- User accounts
- Online authentication
- Recommendation engine
- AI recommendations
- Watch parties
- Mobile applications
- Smart TV applications
- Browser extensions
- Plugin marketplace
- Docker deployment
- Node.js-based tooling

---

5. Target Audience

Primary audience:

- Personal users
- Anime enthusiasts managing their own local libraries
- Self-hosters
- Developers interested in clean software architecture

Version 1 is not intended for commercial deployments or public streaming services.

---

6. Supported Platforms

Primary Platform

- Windows

Supported Platforms

- Linux
- macOS

---

7. User Experience Goals

The application should feel:

- Premium
- Fast
- Calm
- Bold
- Cinematic
- Minimal
- Predictable
- Consistent

Users should be able to begin watching with minimal interaction.

---

8. Core Features

Media Library

- Local media library
- Anime organization
- Seasons
- Episodes
- Posters
- Episode thumbnails

Player

- Custom video player
- Playback controls
- Resume playback
- Playback progress
- Fullscreen
- Subtitle selection
- Keyboard shortcuts

Library Features

- Continue Watching
- Favorites
- Watch history
- Now Watching
- Library browsing

Dashboard

Protected local dashboard allowing management of:

- Library
- Media metadata
- Posters
- Settings
- User preferences

Dashboard access must require local authentication.

---

9. Teacher Mode

Teacher Mode provides an immediate distraction-free reading interface.

Activation methods:

- Teacher Mode button
- Any keyboard key

Mouse clicks outside the Teacher Mode button must not activate this mode.

Teacher Mode should preserve playback progress.

---

10. Welcome Experience

The application begins with a cinematic welcome screen.

Features include:

- Random background banner
- Swipe-up interaction
- Smooth transition
- Configurable display frequency

The welcome screen should strengthen the application's identity without slowing access to media.

---

11. Background System

The application includes a rotating collection of high-quality banners.

Each background should:

- Randomize each session
- Apply a dark overlay
- Apply a bottom-to-top black gradient
- Preserve text readability

Background transitions should remain subtle.

---

12. Localization

Supported interface languages:

- Hindi (Primary)
- English
- Japanese

Future languages should be easy to add.

---

13. Media Formats

Preferred formats:

Video

- MP4

Subtitles

- WebVTT

Images

- WebP

These formats were selected for performance, compatibility, and storage efficiency.

---

14. Data Storage

Media metadata

- JSON

User data

- SQLite

Examples of user data:

- Watch history
- Favorites
- Settings
- Dashboard authentication
- Continue Watching

---

15. Performance Requirements

The application should prioritize responsiveness.

Requirements:

- Fast startup
- Smooth navigation
- Responsive controls
- Efficient rendering
- Lightweight assets
- Minimal unnecessary animations

Performance should always take priority over visual complexity.

---

16. Accessibility Requirements

Version 1 should support:

- Keyboard navigation
- High contrast
- Visible focus indicators
- Screen reader friendly HTML
- Readable typography
- Reduced motion support

---

17. Security Requirements

Dashboard authentication should use secure password hashing.

The application must:

- Never store plaintext passwords
- Validate all user input
- Keep user data local
- Protect configuration files

Privacy is a core project principle.

---

18. Design Principles

Every interface should follow these principles:

- Simplicity
- Consistency
- Readability
- Performance
- Minimalism
- Strong typography
- Purposeful motion

Visual decoration should never reduce usability.

---

19. Success Criteria

Version 1 will be considered successful if it:

- Plays local media reliably
- Provides a polished custom player
- Maintains playback history
- Supports favorites
- Supports Continue Watching
- Includes a protected Dashboard
- Delivers excellent performance
- Functions completely offline
- Remains maintainable
- Is fully documented

---

20. Future Expansion

Potential future enhancements include:

- Multi-user profiles
- Theme customization
- Additional localization
- Advanced player features
- Metadata import tools
- Plugin architecture
- Remote control applications
- Enhanced dashboard capabilities

Future improvements must preserve the project's emphasis on simplicity and maintainability.

---

21. Product Principles

Every feature added to Hibiki should satisfy the following questions:

- Does it improve the user experience?
- Does it improve maintainability?
- Does it preserve performance?
- Does it align with the project's design philosophy?
- Can it be maintained long term?

If the answer is "no," the feature should be reconsidered or deferred.

---

22. Product Statement

Hibiki exists to provide a premium local streaming experience that values simplicity, privacy, performance, and thoughtful engineering over unnecessary complexity.

Every release should make the application better without compromising those principles.
