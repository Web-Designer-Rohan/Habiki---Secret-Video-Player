# Hibiki asset and media policy

Hibiki does not assume or bundle an anime catalog or user media. The application indexes files that the user places in configured local library folders.

## Repository asset layout

```text
assets/
├── banners/       # optional application or welcome imagery
├── fonts/         # locally supplied fonts, if present
├── icons/         # project icon assets
├── images/        # general application imagery
├── posters/       # optional artwork used by the application
├── thumbnails/    # generated or supplied episode previews
└── vendor/        # vendored open-source assets and version records
    ├── anime/
    ├── lucide/
    └── VERSIONS.md
```

The repository currently uses the local Anime.js bundle and Lucide SVG set under `assets/vendor/`. Their licenses and versions are recorded in [`docs/ATTRIBUTION.md`](ATTRIBUTION.md) and [`assets/vendor/VERSIONS.md`](../assets/vendor/VERSIONS.md).

## User library layout

A recommended local media structure is:

```text
media/
└── Anime Name/
    ├── poster.webp
    ├── banner.webp
    └── Season 01/
        ├── Episode 01.mp4
        ├── Episode 01.vtt
        └── Episode 02.mp4
```

The configured library may live outside the repository. Hibiki's backend scanner indexes supported local formats and keeps filesystem access behind the API boundary. Do not commit personal media, credentials, generated databases, logs, or private artwork to the repository.

## Imported asset sets (development)

The current development asset set is defined in `docs/CONTENT.md`, which acts as the temporary source of truth for project assets. The following sets were imported from the archive URLs listed there on 2026-08-03:

- `assets/banners/` — 30 JPeg banner images (~1.9 MB) from `30_banners.zip`. The source archive does not declare a license; treat these as user-supplied artwork pending rights confirmation.
- `assets/fonts/` — local builds of Anton (regular), Inter (variable), and Noto Sans JP (variable), each shipped with its OFL-1.1 license text. Only the builds required by the design system are committed; the full 79 MB font archive is not part of the repository.
- Poster images are placed in the user media library at `media/<Anime>/poster.jpg` and, like all user media, are not committed to the repository.

Source archive integrity (for re-acquisition before the temporary tunnel is retired):

- `30_banners.zip` — sha256 `b91d98f24a971a4db7bcba306311ae005e9d5becb1f388454c40e23127c678e8`
- `Anton,Inter,Noto_Sans_JP.zip` — sha256 `4672ef0925791c79af4c8b5004e5e80c95ba9c279b08e54ea7084ab3f4fba2e0`

The entries seeded in `data/library.json` are metadata-only placeholders: no local video files are imported yet, and placeholder episodes are not playable. Running a library scan regenerates `library.json` from the local `media/` tree, which replaces the placeholders; until local media exists, a scan produces an empty library.

These archives are temporary development sources. Replace them with licensed, versioned sources before any public release.

---

## Rights and permission

Users are responsible for ensuring they have permission to possess, copy, process, display, and play every media file and asset they place in a Hibiki library. This includes videos, subtitles, posters, banners, thumbnails, fonts, and music.

Hibiki does not grant a license to third-party media and does not verify ownership or licensing. A file being technically compatible with Hibiki does not make its use lawful. Respect copyright, privacy, publicity, trademark, and other applicable rights in your jurisdiction.

## Asset contributions

Contributors should provide the source, version, license, and required notices for any asset added to the repository. Prefer assets with clear open-source or public-domain terms, keep attribution close to the asset when required, and update `docs/ATTRIBUTION.md` and `assets/vendor/VERSIONS.md` when a vendored dependency changes.
