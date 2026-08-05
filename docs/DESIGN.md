DESIGN.md

---

title: Design System
project: Hibiki
version: 1.0.0
status: Active
owner: Rohan
last_updated: 2026-08-02

Hibiki Design System

Purpose

This document defines the complete visual identity of Hibiki.

It serves as the single source of truth for colors, typography, spacing, visual hierarchy, iconography, imagery, and overall design philosophy.

Implementation details belong in "FRONTEND_DESIGN.md".

---

Design Philosophy

Hibiki should feel like a premium local streaming application inspired by modern Japanese editorial design and brutalism.

The interface should communicate confidence, simplicity, and immersion rather than decoration.

Core principles:

- Bold over flashy
- Minimal over crowded
- Typography first
- Posters second
- Icons only where useful
- High contrast
- Consistent spacing
- Cinematic atmosphere
- Fast interface
- Beautiful without unnecessary animations

---

Design Keywords

- Japanese Editorial
- Modern Brutalism
- Minimal
- Cinematic
- Dark
- Bold
- Calm
- Premium
- Functional

---

Color System

Primary Background

- Charcoal Black (#111111)

Secondary Background

- Slightly lighter charcoal

Surface

- Dark neutral surfaces

Accent

- Deep Crimson Red

Text

- White
- Light Gray
- Medium Gray

Feedback Colors

- Success
- Warning
- Error
- Information

These should remain subtle and should never overpower the primary red accent.

---

Theme

Version 1 ships with Hibiki Dark plus six alternate color themes: AMOLED, Nord, Tokyo Night, Catppuccin Mocha, Dracula, and Gruvbox.

---

Typography

Primary UI Font

Inter

Heading Font

Anton

Japanese Accent Font

Noto Sans JP

Typography Rules

- Large headings
- Comfortable body text
- Consistent font weights
- Strong hierarchy
- Excellent readability

---

Iconography

Iconography

Hibiki uses text labels and lightweight Unicode controls where appropriate; no runtime icon library is required.

Rules

- Outline icons
- Consistent stroke width
- Minimal icon usage
- Text should always be understandable without icons

---

Imagery

Images should always support the interface.

Never overwhelm it.

Image Types

- Welcome banners
- Anime posters
- Episode thumbnails

Poster Style

- High quality
- Consistent aspect ratio
- Optimized WebP images

Episode Thumbnail Style

Generated from the episode automatically.

Preferred capture window:

3–10 seconds.

---

Background System

The application background rotates randomly from the available banner collection.

Each background should include:

- Dark overlay
- Bottom-to-top black gradient
- Slight brightness reduction
- Smooth fade when changing between library views

Backgrounds should never reduce readability.

---

Corners

Radius

4–6 px

No excessive rounding.

---

Borders

Thin

Clean

High contrast

No unnecessary decoration.

---

Shadows

Minimal.

Use depth only when necessary.

Avoid large soft shadows.

---

Motion

Motion should feel purposeful.

Allowed

- Fade
- Slide
- Scale (subtle)

Avoid

- Bounce
- Elastic
- Long animations

Animations should remain short and responsive.

---

Visual Hierarchy

Priority

1. Currently playing content

2. Continue Watching

3. Library

4. Dashboard

5. Settings

Users should immediately understand where to focus.

---

Accessibility

Design should support WCAG AA.

Requirements

- High contrast
- Visible focus states
- Keyboard accessibility
- Readable typography
- Reduced motion support

---

Performance

Design decisions should prioritize rendering performance.

Avoid

- Heavy blur
- Large shadow stacks
- Excessive transparency
- Complex visual effects

---

Brand Identity

Project Name

Hibiki

Visual Identity

Premium

Minimal

Japanese-inspired

Bold

Timeless

---

Design Principles

Every visual decision should satisfy these questions:

- Does it improve usability?
- Does it improve readability?
- Does it improve consistency?
- Does it improve performance?

If not, it should not be added.

---

Future Design Ideas

Possible future improvements include:

- Additional themes
- Dynamic color accents
- Seasonal backgrounds
- Animated artwork
- Custom icon set
- Advanced player skins

These ideas are intentionally deferred to future releases and should not influence Version 1.
