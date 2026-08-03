# Hibiki third-party attribution

Hibiki is distributed under the [GNU Affero General Public License, version 3 or later](../LICENSE). This document records the open-source software included in, used to run, or documented for the current release. It is an attribution record, not legal advice.

## Runtime and bundled software

| Project | Version | License | Purpose | Distribution note |
|---|---:|---|---|---|
| [Anime.js](https://animejs.com/) | 4.5.0 | [MIT](https://github.com/juliangarnier/anime/blob/v4.5.0/LICENSE.md) | Local interface motion and the welcome-screen transition. | The browser UMD build is vendored at `assets/vendor/anime/anime.umd.min.js`. |
| [Lucide](https://lucide.dev/) | 1.28.0 | [ISC](https://github.com/lucide-icons/lucide/blob/1.28.0/LICENSE) | Local SVG icon assets for the interface. | The icon set is vendored at `assets/vendor/lucide/icons/`; no CDN is required. |
| [Anton](https://fonts.google.com/specimen/Anton) / [Inter](https://rsms.me/inter/) / [Noto Sans JP](https://fonts.google.com/noto/specimen/Noto+Sans+JP) | Development build (archive 2026-08-02) | [OFL-1.1](https://openfontlicense.org/) | Local UI typography (display, body, Japanese). | Regular/variable builds vendored at `assets/fonts/` with their OFL texts; sourced from the temporary development archive in `docs/CONTENT.md`. |
| [FastAPI](https://fastapi.tiangolo.com/) | 0.141.1* | MIT | Local REST API framework. | Installed through `requirements.txt`; the file intentionally leaves dependency pinning to the deployment environment. |
| [Uvicorn](https://www.uvicorn.org/) | 0.52.1* | [BSD 3-Clause](https://github.com/encode/uvicorn/blob/0.52.1/LICENSE.md) | Local ASGI application server. | Installed through `requirements.txt`. |
| [Pydantic](https://docs.pydantic.dev/) | 2.13.4* | MIT | Request and configuration validation used by FastAPI. | A FastAPI runtime dependency; not listed directly in `requirements.txt`. |
| [Python](https://www.python.org/) | 3.12.3* | [PSF License](https://docs.python.org/3/license.html) | Backend language and standard library. | The application requires Python 3.12 or newer. |
| [SQLite](https://www.sqlite.org/) | System/runtime dependent | Public domain | Local user data database. | SQLite is used through Python's standard-library `sqlite3` module. |

## Optional media tooling

| Project | Version | License | Purpose | Distribution note |
|---|---:|---|---|---|
| [FFmpeg](https://ffmpeg.org/) | User-installed | LGPL-2.1-or-later or GPL-2.0-or-later, depending on the build | Optional local media processing and future thumbnail workflows described by the installation documentation. | FFmpeg is not bundled by this repository. The license obligations of a particular FFmpeg build depend on its enabled configuration and how it is distributed. |

\* Versions marked with an asterisk were inspected in the verification environment on 2026-08-02. `requirements.txt` is currently unpinned, so downstream installations must audit the versions they install.

## Project-level license choice

Hibiki uses **GNU AGPL-3.0-or-later**. The project is a self-hosted application with a local web interface and a REST server. AGPL's copyleft terms preserve users' ability to study, modify, and share the application, including the source-sharing expectations for modified network-accessible versions. The project remains usable offline and does not require a hosted service.

This choice applies to Hibiki-authored code and documentation unless a file says otherwise. It does not replace the separate licenses of third-party components listed above. Those components retain their own copyright and license notices.

## Compliance notes

- Keep this file, `LICENSE`, and the vendored asset version record with source distributions.
- Preserve the license and copyright notices for third-party components when redistributing them.
- Do not describe user-supplied media, posters, banners, fonts, or subtitles as Hibiki assets; their rights remain the user's responsibility.
- Consult the license text and a qualified professional for distribution questions involving a specific dependency or FFmpeg build.
