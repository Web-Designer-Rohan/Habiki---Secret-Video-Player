INSTALLATION.md

---

title: Installation Guide
project: Hibiki
version: 1.0.0
status: Active
owner: Rohan
last_updated: 2026-08-02

Hibiki Installation Guide

Purpose

This document explains how to install, configure, and run Hibiki on supported operating systems.

Version 1 is designed to run natively without Docker, Node.js, or npm.

---

Supported Operating Systems

Officially Supported

- Windows
- Linux
- macOS

Hibiki is designed to behave consistently across all supported platforms.

---

System Requirements

Minimum

- 64-bit operating system
- Dual-core CPU
- 4 GB RAM
- 2 GB free storage (excluding media)
- Modern web browser
- Python 3.12 or newer

---

Recommended

- Quad-core CPU or better
- 8 GB RAM
- SSD storage
- 1080p display
- Python 3.12+
- Hardware-accelerated video decoding

---

Project Structure

After installation the project should resemble:

Hibiki/
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

---

Required Software

Install:

- Python 3.12+
- Git
- FFmpeg (optional)

FFmpeg is used for optional thumbnail generation. It is not required for scanning or playback of browser-supported formats.

No additional runtime is required for Version 1.

---

Python Dependencies

Python packages will be listed in:

requirements.txt

Install them using:

pip install -r requirements.txt

---

Frontend

The frontend is dependency-light.

No Node.js or npm installation is required.

The frontend is served directly by the Python backend.

---

Media Library

Create the media root directory if it does not already exist (created
automatically on first run). The default root is `contents/` and is
configurable in Settings → Media folder.

Recommended structure:

contents/
├── Anime/
├── Movies/
├── Tutorials/
├── Other/
├── TV Shows/
└── Courses/

Add media per the rules in docs/ASSETS.md, then run a library scan from the
dashboard; the scan runs in the background and indexes everything
automatically.

---

First Startup

Recommended order:

1. Install Python dependencies.
2. Verify FFmpeg is available if you want to generate thumbnails (optional).
3. Launch the backend.
4. Open Hibiki in the browser.
5. Retrieve the generated bootstrap password from `config/initial-admin.txt` and unlock the application.
6. Configure the media library location.
7. Run the first library scan.

After scanning, the media library becomes available.

---

Updating the Library

Whenever new media is added:

1. Place media inside the configured library root.
2. Run the library scan from the dashboard.
3. Wait for the scan status to return to `idle`; the library updates without a page refresh.

---

Updating Hibiki

Recommended update process:

1. Back up the "data/" directory.
2. Pull or download the latest release.
3. Update Python dependencies if required.
4. Launch the application.
5. Verify the library scan.

User data should remain intact across updates whenever possible.

---

Backup

Recommended backup locations:

data/
config/
contents/    (or your configured media root)

These directories contain the application configuration, user data, and local media library.

---

Troubleshooting

Application does not start

Verify:

- Python version
- Installed dependencies
- File permissions

---

Media not detected

Verify:

- Library location
- Supported file extensions
- Folder structure

Run a library scan again.

---

Missing thumbnails

Ensure FFmpeg is installed and accessible from the system path.

Run thumbnail generation again.

---

Playback issues

Verify:

- Video format
- Browser support
- File integrity

---

Login problems

Verify:

- The bootstrap password was retrieved from `config/initial-admin.txt`.
- The application is unlocked with the correct password.
- The database file is accessible.

---

Supported Media

Video

- MP4, MKV, WebM, AVI, MOV, M4V, FLV, MPEG, TS, M3U8 (browser support varies)

Images

- WebP
- PNG
- JPEG

Subtitles

- WebVTT (.vtt) subtitles

Browser support for individual video formats varies by platform; unsupported files are skipped safely by the scanner.

---

Security Notes

- Keep the local application password secure and delete `config/initial-admin.txt` after unlocking.
- Do not manually edit the SQLite database while Hibiki is running.
- Back up important data before upgrading.

---

Version 1 Installation Philosophy

Version 1 intentionally favors a simple installation process.

Goals:

- Minimal dependencies
- Native execution
- Offline operation
- Cross-platform compatibility
- Predictable behavior

The installation process should be understandable by both experienced developers and casual users.

---

Future Improvements

Later versions may introduce:

- Automatic updates
- Installer packages
- Portable distributions
- Optional Docker support
- Native desktop packaging

These improvements are intentionally outside the scope of Version 1.
