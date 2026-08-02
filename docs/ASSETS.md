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

## Rights and permission

Users are responsible for ensuring they have permission to possess, copy, process, display, and play every media file and asset they place in a Hibiki library. This includes videos, subtitles, posters, banners, thumbnails, fonts, and music.

Hibiki does not grant a license to third-party media and does not verify ownership or licensing. A file being technically compatible with Hibiki does not make its use lawful. Respect copyright, privacy, publicity, trademark, and other applicable rights in your jurisdiction.

## Asset contributions

Contributors should provide the source, version, license, and required notices for any asset added to the repository. Prefer assets with clear open-source or public-domain terms, keep attribution close to the asset when required, and update `docs/ATTRIBUTION.md` and `assets/vendor/VERSIONS.md` when a vendored dependency changes.
