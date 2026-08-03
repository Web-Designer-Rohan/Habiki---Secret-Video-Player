# Hibiki asset and media policy

Hibiki does not assume or bundle an anime catalog or user media. The application indexes files that the user places in a single configured media root (default `contents/`), organized into four categories.

## Repository asset layout

```text
assets/
├── fonts/         # locally supplied fonts, if present
├── icons/         # project icon assets
├── images/        # general application imagery
└── vendor/        # vendored open-source assets and version records
    ├── anime/
    ├── lucide/
    └── VERSIONS.md
```

The repository currently uses the local Anime.js bundle and Lucide SVG set under `assets/vendor/`. Their licenses and versions are recorded in [`docs/ATTRIBUTION.md`](ATTRIBUTION.md) and [`assets/vendor/VERSIONS.md`](../assets/vendor/VERSIONS.md).

## User library layout

The filesystem is the single source of truth. The scanner walks one configurable media root (`contents/` by default; changeable in Settings → Media folder) and indexes everything it finds. The four category folders are `Anime`, `Movies`, `Tutorials`, and `Other`; anything outside them is ignored with a warning.

```text
contents/
├── Anime/
│   └── Jujutsu Kaisan/        # one folder per title
│       ├── info.json          # optional metadata (title, description, year, genre, studio)
│       ├── poster.webp        # optional; poster.png/jpg/jpeg work too
│       ├── banner.webp        # optional
│       ├── Season 01/         # "Season 1", "S01", or just "1" all work
│       │   ├── 1.mp4          # episodes: 1, 01 - Title, EP 1, episode 1, E01, S2E5, ...
│       │   ├── 1.vtt          # optional subtitle (same stem, or a prefix)
│       │   ├── 1.webp         # optional episode thumbnail (same stem)
│       │   └── ...
│       └── Season 02/
├── Movies/
│   ├── Your Name.mp4          # a video file directly in the folder is one movie
│   ├── Your Name.vtt
│   ├── Your Name.webp         # optional poster/thumbnail (same stem)
│   └── A Silent Voice/        # or a folder with one video + poster/banner/info.json
│       ├── movie.mp4
│       ├── poster.webp
│       └── info.json
├── Tutorials/                 # same rules as Movies
│   └── Guitar Lesson.mp4
└── Other/                     # same rules as Movies
```

Rules:

- **Anime** — each subfolder is a title. Season folders (`Season 1` / `S01` / bare `1`) hold the numbered episodes; videos placed directly in the title folder (no season folder) count as Season 1.
- **Movies / Tutorials / Other** — each video file directly inside the category folder is one standalone title; a subfolder with one video is a standalone title too (with room for poster/banner/info.json). A folder with several videos uses the video whose stem matches the folder name (else the alphabetically first) and logs a warning.
- Episode numbers are read from the file name: a leading number (`1`, `01 - Title`) is used first, then `EP 1` / `episode 1` / `E01` / `S2E5` styles; files with no number are ordered by name. Duplicate numbers are reassigned deterministically.
- Episode titles are cleaned from the file name (`EP 3 - The Fight` → `The Fight`, `E04` → `Episode 4`); `info.json` in an anime folder or standalone folder overrides the title and adds optional fields (`description`, `year`, `genre`, `studio`).
- The scan is deterministic (alphabetical traversal, fixed category order), incremental (unchanged videos keep their cached metadata via signatures stored in `data/library.json`), and non-blocking (the dashboard scan runs in the background and reports progress through the scan status endpoint). Problems are reported as warnings in the dashboard and `logs/scanner.log` — a missing poster, invalid `info.json`, or an unsupported file never breaks the scan.

The configured media root may live outside the repository (an absolute path in Settings → Media folder). Do not commit personal media, credentials, generated databases, logs, or private artwork to the repository: `contents/` and the generated cache `data/library.json` are gitignored.

## Imported asset sets (development)

The following sets are part of the repository:

- `assets/fonts/` — local builds of Anton (regular), Inter (variable), and Noto Sans JP (variable), each shipped with its OFL-1.1 license text. Only the builds required by the design system are committed; the full 79 MB font archive is not part of the repository.

Poster and banner images for library titles are placed in the user media root (e.g. `contents/Anime/<Title>/poster.webp`) and, like all user media, are not committed to the repository.

---

## Rights and permission

Users are responsible for ensuring they have permission to possess, copy, process, display, and play every media file and asset they place in a Hibiki library. This includes videos, subtitles, posters, banners, thumbnails, fonts, and music.

Hibiki does not grant a license to third-party media and does not verify ownership or licensing. A file being technically compatible with Hibiki does not make its use lawful. Respect copyright, privacy, publicity, trademark, and other applicable rights in your jurisdiction.

## Asset contributions

Contributors should provide the source, version, license, and required notices for any asset added to the repository. Prefer assets with clear open-source or public-domain terms, keep attribution close to the asset when required, and update `docs/ATTRIBUTION.md` and `assets/vendor/VERSIONS.md` when a vendored dependency changes.
