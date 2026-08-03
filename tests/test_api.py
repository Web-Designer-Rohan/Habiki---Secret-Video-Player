"""End-to-end API tests for the security and correctness fixes:

- Security headers and cross-origin rejection
- Unlock rate limiting (brute-force protection)
- Single-password unlock lifecycle
- Player 404s for placeholder episodes, media serving
- Activity round trips (favorites, progress, continue watching)
- Library cache invalidation behavior
"""

import json
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.core import Settings, write_json
from backend.app.media import MediaService
from backend.app.scanner import LibraryScanner
from backend.app.main import app, SECURITY_HEADERS


def temp_settings(directory: str) -> Settings:
    root = Path(directory)
    settings = Settings(
        project_root=root,
        data_dir=root / "data",
        config_dir=root / "config",
        media_root="contents",
        logs_dir=root / "logs",
        database_path=root / "data" / "database.db",
        library_path=root / "data" / "library.json",
        config_path=root / "config" / "config.json",
    )
    for directory_path in (settings.data_dir, settings.config_dir, settings.media_dir, settings.logs_dir):
        directory_path.mkdir(parents=True, exist_ok=True)
    return settings


class ApiSecurityTests(unittest.TestCase):
    UNLOCK_PASSWORD = "a-secure-local-password"

    @classmethod
    def setUpClass(cls):
        cls._patch = patch("backend.app.main.Settings.load")

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.settings = temp_settings(self.directory.name)
        self.mock = self._patch.start()
        self.mock.return_value = self.settings
        self.client = TestClient(app)
        self.client.__enter__()
        # The lifespan auto-generates a random bootstrap password; replace it
        # with one we know and start locked so the API tests can unlock.
        app.state.auth.set_password(self.UNLOCK_PASSWORD)
        app.state.auth.lock()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self._patch.stop()
        self.directory.cleanup()

    def unlock(self, password: str | None = None):
        password = password or self.UNLOCK_PASSWORD
        response = self.client.post("/api/v1/auth/unlock", json={"password": password})
        self.assertEqual(response.status_code, 200, response.text)
        return response

    def test_security_headers_are_present_on_every_response(self):
        response = self.client.get("/")
        for name in SECURITY_HEADERS:
            self.assertEqual(response.headers.get(name), SECURITY_HEADERS[name], name)
        self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")

    def test_cross_origin_state_change_is_rejected(self):
        response = self.client.post(
            "/api/v1/auth/unlock",
            json={"password": self.UNLOCK_PASSWORD},
            headers={"Origin": "https://evil.example"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "CROSS_ORIGIN_DENIED")

    def test_same_origin_state_change_is_allowed(self):
        response = self.client.post(
            "/api/v1/auth/unlock",
            json={"password": self.UNLOCK_PASSWORD},
            headers={"Origin": "http://testserver"},
        )
        self.assertEqual(response.status_code, 200, response.text)

    def test_unlock_brute_force_is_rate_limited(self):
        for _ in range(5):
            response = self.client.post("/api/v1/auth/unlock", json={"password": "wrong-password"})
            self.assertEqual(response.status_code, 401, response.text)
        blocked = self.client.post("/api/v1/auth/unlock", json={"password": "wrong-password"})
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(blocked.json()["error"]["code"], "RATE_LIMITED")
        # Even a correct password is refused while locked out...
        locked = self.client.post("/api/v1/auth/unlock", json={"password": self.UNLOCK_PASSWORD})
        self.assertEqual(locked.status_code, 429)
        # ...and resetting the limiter releases the lockout.
        app.state.auth.unlock_limiter.reset("unlock|testclient")
        released = self.client.post("/api/v1/auth/unlock", json={"password": self.UNLOCK_PASSWORD})
        self.assertEqual(released.status_code, 200, released.text)

    def test_unlock_status_roundtrip(self):
        self.assertEqual(self.client.get("/api/v1/auth/status").json()["data"]["unlocked"], False)
        self.unlock()
        self.assertEqual(self.client.get("/api/v1/auth/status").json()["data"]["unlocked"], True)

    def test_locked_state_blocks_dashboard_settings_and_activity(self):
        for path in ("/api/v1/dashboard/status", "/api/v1/settings", "/api/v1/favorites"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 401, path)
            self.assertEqual(response.json()["error"]["code"], "AUTHENTICATION_REQUIRED")
        self.unlock()
        self.assertEqual(self.client.get("/api/v1/dashboard/status").status_code, 200)

    def test_wrong_password_does_not_unlock(self):
        response = self.client.post("/api/v1/auth/unlock", json={"password": "wrong-password"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.client.get("/api/v1/auth/status").json()["data"]["unlocked"], False)

    def test_change_password_requires_unlocked_and_verifies_current(self):
        self.assertEqual(
            self.client.put("/api/v1/auth/password", json={"current_password": self.UNLOCK_PASSWORD, "new_password": "a-new-password"}).status_code,
            401,
        )
        self.unlock()
        wrong = self.client.put("/api/v1/auth/password", json={"current_password": "wrong-password", "new_password": "a-new-password"})
        self.assertEqual(wrong.status_code, 401)
        ok = self.client.put("/api/v1/auth/password", json={"current_password": self.UNLOCK_PASSWORD, "new_password": "a-new-password"})
        self.assertEqual(ok.status_code, 200, ok.text)
        # The old password no longer unlocks; the new one does.
        app.state.auth.lock()
        self.assertEqual(self.client.post("/api/v1/auth/unlock", json={"password": self.UNLOCK_PASSWORD}).status_code, 401)
        self.assertEqual(self.client.post("/api/v1/auth/unlock", json={"password": "a-new-password"}).status_code, 200)

    def test_placeholder_episode_returns_clean_404(self):
        write_json(self.settings.library_path, {"version": 2, "entries": [
            {"id": "show", "title": "Show", "type": "anime", "seasons": [{"number": 1, "episodes": [
                {"id": "show-s01-e01", "number": 1, "title": "Episode 01"},
            ]}]},
        ]})
        response = self.client.get("/api/v1/player/source/show-s01-e01")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "NOT_FOUND")

    def test_media_file_is_served_and_unknown_ids_404(self):
        show = self.settings.media_dir / "Anime" / "Show" / "Season 01"
        show.mkdir(parents=True)
        video = show / "Episode 01.mp4"
        video.write_bytes(b"fake-mp4-content")
        write_json(self.settings.library_path, {"version": 2, "entries": [
            {"id": "show", "title": "Show", "type": "anime", "seasons": [{"number": 1, "episodes": [
                {"id": "show-s01-e01", "number": 1, "title": "Episode 01", "video_path": str(video), "subtitle_paths": []},
            ]}]},
        ]})
        source = self.client.get("/api/v1/player/source/show-s01-e01")
        self.assertEqual(source.status_code, 200, source.text)
        self.assertEqual(source.json()["data"]["url"], "/api/v1/player/file/show-s01-e01")
        media = self.client.get("/api/v1/player/file/show-s01-e01")
        self.assertEqual(media.status_code, 200)
        self.assertEqual(media.content, b"fake-mp4-content")
        self.assertEqual(media.headers["content-type"], "video/mp4")
        self.assertEqual(self.client.get("/api/v1/player/source/ghost-s01-e01").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/player/subtitle/show-s01-e01/-1").status_code, 404)

    def test_favorites_progress_and_continue_watching_roundtrip(self):
        write_json(self.settings.library_path, {"version": 2, "entries": [
            {"id": "show", "title": "Show", "type": "anime", "seasons": []},
        ]})
        self.unlock()
        self.assertEqual(self.client.post("/api/v1/favorites/show").status_code, 200)
        favorites = self.client.get("/api/v1/favorites").json()["data"]
        self.assertEqual([item["anime_id"] for item in favorites], ["show"])
        self.assertEqual(self.client.delete("/api/v1/favorites/show").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/favorites").json()["data"], [])
        progress = self.client.post("/api/v1/player/progress", json={
            "episode_id": "show-s01-e01", "anime_id": "show",
            "season_number": 1, "episode_number": 1, "playback_position": 42.0,
        })
        self.assertEqual(progress.status_code, 200, progress.text)
        self.assertEqual(self.client.get("/api/v1/player/progress/show-s01-e01").json()["data"]["playback_position"], 42.0)
        continued = self.client.get("/api/v1/continue").json()["data"]
        self.assertEqual([item["episode_id"] for item in continued], ["show-s01-e01"])
        self.assertEqual(self.client.delete("/api/v1/continue/show-s01-e01").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/continue").json()["data"], [])

    def test_version_endpoint_matches_single_source(self):
        from backend.app.core import VERSION
        response = self.client.get("/api/v1/version")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["version"], VERSION)

    def test_settings_whitelist_rejects_unknown_keys(self):
        self.unlock()
        response = self.client.put("/api/v1/settings", json={"values": {
            "theme": "dark",
            "injected_junk": "should-not-be-stored",
        }})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["data"], {"theme": "dark"})
        stored = self.client.get("/api/v1/settings").json()["data"]
        self.assertNotIn("injected_junk", stored)

    def test_large_responses_are_gzip_compressed(self):
        response = self.client.get("/", headers={"Accept-Encoding": "gzip"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("content-encoding"), "gzip")

    def test_reload_route_was_removed_in_favor_of_scan(self):
        self.unlock()
        response = self.client.post("/api/v1/dashboard/library/reload")
        self.assertEqual(response.status_code, 404)

    def test_library_categories_and_banner_endpoint(self):
        movies = self.settings.media_dir / "Movies" / "A Movie"
        movies.mkdir(parents=True)
        (movies / "movie.mp4").write_bytes(b"m")
        (movies / "banner.webp").write_bytes(b"img")
        app.state.media.scan()
        all_entries = self.client.get("/api/v1/library").json()["data"]["entries"]
        self.assertEqual([entry["type"] for entry in all_entries], ["movies"])
        self.assertEqual(all_entries[0]["id"], "a-movie")
        movies_only = self.client.get("/api/v1/library?category=movies").json()["data"]["entries"]
        self.assertEqual(len(movies_only), 1)
        self.assertEqual(self.client.get("/api/v1/library?category=anime").json()["data"]["entries"], [])
        bad_category = self.client.get("/api/v1/library?category=series")
        self.assertEqual(bad_category.status_code, 422)
        banner = self.client.get("/api/v1/library/a-movie/banner")
        self.assertEqual(banner.status_code, 200)
        self.assertEqual(banner.content, b"img")
        self.assertEqual(self.client.get("/api/v1/library/a-movie/poster").status_code, 404)

    def test_scan_endpoint_runs_background_scan_and_reports_status(self):
        self.unlock()
        show = self.settings.media_dir / "Anime" / "Show" / "Season 1"
        show.mkdir(parents=True)
        (show / "1.mp4").write_bytes(b"v")
        app.state.settings.library_path.unlink(missing_ok=True)
        response = self.client.post("/api/v1/dashboard/library/scan")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["data"]["status"], "scanning")
        deadline = 5.0
        while deadline > 0:
            status = self.client.get("/api/v1/dashboard/scan/status").json()["data"]
            if status["status"] != "scanning":
                break
            import time as _time
            _time.sleep(0.05)
            deadline -= 0.05
        self.assertEqual(status["status"], "idle")
        self.assertEqual(status["counts"]["anime"], 1)
        entries = self.client.get("/api/v1/library").json()["data"]["entries"]
        self.assertEqual(entries[0]["id"], "show")

    def test_config_media_root_roundtrip(self):
        self.unlock()
        current = self.client.get("/api/v1/dashboard/config").json()["data"]
        self.assertEqual(current["media_root"], "contents")
        self.settings.media_dir.mkdir(parents=True, exist_ok=True)
        response = self.client.post("/api/v1/dashboard/config", json={"media_root": "other"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["data"]["media_root"], "other")
        self.assertEqual(self.settings.media_root, "other")
        stored = json.loads(self.settings.config_path.read_text(encoding="utf-8"))
        self.assertEqual(stored["media_root"], "other")
        self.assertEqual(self.client.get("/api/v1/dashboard/config").json()["data"]["media_root"], "other")
        bad = self.client.post("/api/v1/dashboard/config", json={"media_root": ".."})
        self.assertEqual(bad.status_code, 422)


class LibraryCacheTests(unittest.TestCase):
    def test_find_episode_uses_index_and_invalidates_on_file_change(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = temp_settings(directory)
            write_json(settings.library_path, {"version": 2, "entries": [
                {"id": "show", "title": "Show", "type": "anime", "seasons": []},
            ]})
            media = MediaService(settings, LibraryScanner(settings, logging.getLogger("test-cache")))
            self.assertIsNone(media.find_episode("show-s01-e01"))
            write_json(settings.library_path, {"version": 2, "entries": [
                {"id": "show", "title": "Show", "type": "anime", "seasons": [{"number": 1, "episodes": [
                    {"id": "show-s01-e01", "number": 1, "title": "Episode 01"},
                ]}]},
            ]})
            self.assertIsNotNone(media.find_episode("show-s01-e01"))
            self.assertEqual(media.find_episode("show-s01-e01")["id"], "show-s01-e01")
            self.assertIsNone(media.find_episode("missing-s01-e01"))


if __name__ == "__main__":
    unittest.main()
