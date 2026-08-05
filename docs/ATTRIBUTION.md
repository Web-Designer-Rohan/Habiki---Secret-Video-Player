# Hibiki third-party attribution

Hibiki is distributed under the [MIT License](../LICENSE). This document records the open-source software included in, used to run, or documented for the current release. It is an attribution record, not legal advice.

## Runtime and bundled software

| Project | Version | License | Purpose | Distribution note |
|---|---:|---|---|---|
| [Anime.js](https://animejs.com/) | 4.5.0 | [MIT](https://github.com/juliangarnier/anime/blob/v4.5.0/LICENSE.md) | Local welcome-screen transition. | The browser UMD build is vendored at `assets/vendor/anime/anime.umd.min.js`. |
| [Anton](https://fonts.google.com/specimen/Anton) / [Inter](https://rsms.me/inter/) / [Noto Sans JP](https://fonts.google.com/noto/specimen/Noto+Sans+JP) | Development build | [OFL-1.1](https://openfontlicense.org/) | Local UI typography. | Regular/variable builds are vendored at `assets/fonts/` with their OFL texts. |
| [FastAPI](https://fastapi.tiangolo.com/) | 0.115.6 | MIT | Local REST API framework. | Installed through `requirements.txt`. |
| [Uvicorn](https://www.uvicorn.org/) | 0.32.1 | [BSD 3-Clause](https://github.com/encode/uvicorn/blob/0.32.1/LICENSE.md) | Local ASGI application server. | Installed through `requirements.txt`. |
| [Pydantic](https://docs.pydantic.dev/) | FastAPI runtime | MIT | Request and configuration validation. | Installed as a FastAPI dependency. |
| [Python](https://www.python.org/) | 3.12+ | [PSF License](https://docs.python.org/3/license.html) | Backend language and standard library. | The application requires Python 3.12 or newer. |
| [SQLite](https://www.sqlite.org/) | System/runtime dependent | Public domain | Local user data storage. | Used through Python's standard-library `sqlite3` module. |

## Optional media tooling

| Project | Version | License | Purpose | Distribution note |
|---|---:|---|---|---|
| [FFmpeg](https://ffmpeg.org/) | User-installed | LGPL-2.1-or-later or GPL-2.0-or-later, depending on the build | Optional thumbnail generation. | FFmpeg is not bundled by this repository. |

## Project license

Hibiki-authored code and documentation are released under the **MIT License**. Third-party components retain their own licenses and notices. User-supplied videos, subtitles, posters, banners, thumbnails, and other media remain the user's responsibility.

## Compliance notes

- Keep this file, `LICENSE`, and the vendored asset version record with source distributions.
- Preserve third-party copyright and license notices when redistributing bundled assets.
- Do not describe user-supplied media as Hibiki assets.
- Consult the license text and a qualified professional for distribution questions involving a specific dependency or FFmpeg build.
