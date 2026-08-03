"""Tests for Phase C: library search/filter/sort, database maintenance, auth
sessions and roles, and media asset services."""

import logging
import tempfile
import unittest
from pathlib import Path

from backend.app.auth import AuthService, PasswordHasher
from backend.app.core import Settings, write_json
from backend.app.database import Database
from backend.app.maintenance import prune_dangling_references
from backend.app.media import MediaService, filter_library
from backend.app.repositories import ActivityRepository, SessionRepository, UserRepository
from backend.app.scanner import LibraryScanner


def temp_settings(directory: str) -> Settings:
    root = Path(directory)
    settings = Settings(
        project_root=root,
        data_dir=root / "data",
        config_dir=root / "config",
        media_dir=root / "media",
        logs_dir=root / "logs",
        database_path=root / "data" / "database.db",
        library_path=root / "data" / "library.json",
        config_path=root / "config" / "config.json",
        library_paths=[],
    )
    for directory_path in (settings.data_dir, settings.config_dir, settings.media_dir, settings.logs_dir):
        directory_path.mkdir(parents=True, exist_ok=True)
    return settings


LIBRARY = {
    "version": 1,
    "anime": [
        {
            "id": "beta",
            "title": "Beta Series",
            "seasons": [{"number": 1, "episodes": [
                {"id": "beta-s01-e01", "number": 1, "title": "First Steps"},
                {"id": "beta-s01-e02", "number": 2, "title": "Deep Dive"},
            ]}],
        },
        {
            "id": "alpha",
            "title": "Alpha Series",
            "seasons": [
                {"number": 1, "episodes": [{"id": "alpha-s01-e01", "number": 1, "title": "Intro"}]},
                {"number": 2, "episodes": [{"id": "alpha-s02-e01", "number": 1, "title": "Return"}]},
            ],
        },
        {"id": "tutorial", "title": "Quick Tutorial", "seasons": []},
    ],
}


class FilterLibraryTests(unittest.TestCase):
    def test_filter_series_and_tutorials(self):
        series = filter_library(LIBRARY, filter_by="series")["anime"]
        tutorials = filter_library(LIBRARY, filter_by="tutorials")["anime"]
        self.assertEqual([entry["id"] for entry in series], ["beta", "alpha"])
        self.assertEqual([entry["id"] for entry in tutorials], ["tutorial"])

    def test_search_by_title(self):
        result = filter_library(LIBRARY, query="alpha")["anime"]
        self.assertEqual([entry["id"] for entry in result], ["alpha"])

    def test_search_by_episode_prunes_unmatched_episodes(self):
        result = filter_library(LIBRARY, query="deep")["anime"]
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "beta")
        episodes = result[0]["seasons"][0]["episodes"]
        self.assertEqual([episode["id"] for episode in episodes], ["beta-s01-e02"])

    def test_search_by_season_number(self):
        result = filter_library(LIBRARY, query="s02")["anime"]
        self.assertEqual([entry["id"] for entry in result], ["alpha"])
        self.assertEqual([season["number"] for season in result[0]["seasons"]], [2])

    def test_search_by_episode_number(self):
        single = {"version": 1, "anime": [LIBRARY["anime"][0]]}
        result = filter_library(single, query="2")["anime"]
        episodes = result[0]["seasons"][0]["episodes"]
        self.assertEqual([episode["id"] for episode in episodes], ["beta-s01-e02"])

    def test_sort_by_title_and_recent(self):
        by_title = filter_library(LIBRARY, sort_by="title")["anime"]
        by_recent = filter_library(LIBRARY, sort_by="recent")["anime"]
        self.assertEqual([entry["id"] for entry in by_title], ["alpha", "beta", "tutorial"])
        self.assertEqual([entry["id"] for entry in by_recent], ["tutorial", "alpha", "beta"])

    def test_combined_query_filter_and_sort(self):
        result = filter_library(LIBRARY, query="beta", filter_by="series", sort_by="title")["anime"]
        self.assertEqual([entry["id"] for entry in result], ["beta"])


class MaintenanceTests(unittest.TestCase):
    def test_prune_removes_only_dangling_references(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Database(Path(directory) / "database.db")
            database.initialize()
            library = {"version": 1, "anime": [{"id": "valid-show", "seasons": [
                {"number": 1, "episodes": [{"id": "valid-ep"}]},
            ]}]}
            with database.connect() as connection:
                user = UserRepository(connection).create("mochi", "hash", "mochi")
                activity = ActivityRepository(connection)
                activity.set_favorite(user["id"], "valid-show", True)
                activity.set_favorite(user["id"], "ghost-show", True)
                activity.save_progress(user["id"], {
                    "episode_id": "valid-ep", "anime_id": "valid-show",
                    "season_number": 1, "episode_number": 1, "playback_position": 10,
                })
                activity.save_progress(user["id"], {
                    "episode_id": "ghost-ep", "anime_id": "ghost-show",
                    "season_number": 1, "episode_number": 1, "playback_position": 10,
                })
                repairs = prune_dangling_references(connection, library)
                self.assertEqual(len(repairs), 2)
                self.assertEqual([item["anime_id"] for item in activity.favorites(user["id"])], ["valid-show"])
                self.assertIsNone(activity.progress(user["id"], "ghost-ep"))
                self.assertIsNotNone(activity.progress(user["id"], "valid-ep"))

    def test_prune_removes_all_rows_when_library_is_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Database(Path(directory) / "database.db")
            database.initialize()
            with database.connect() as connection:
                user = UserRepository(connection).create("mochi", "hash", "mochi")
                ActivityRepository(connection).set_favorite(user["id"], "anything", True)
                repairs = prune_dangling_references(connection, {"version": 1, "anime": []})
                self.assertEqual(len(repairs), 1)


class AuthSessionTests(unittest.TestCase):
    def test_login_creates_verifiable_session_with_role(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = temp_settings(directory)
            database = Database(settings.database_path)
            database.initialize()
            auth = AuthService(database, settings)
            self.assertTrue(auth.ensure_initial_admin("mochi", "a-secure-local-password"))
            self.assertFalse(auth.ensure_initial_admin("mochi", "a-secure-local-password"))
            session_id = auth.login("mochi", "a-secure-local-password")
            with database.connect() as connection:
                user = SessionRepository(connection).get_user(session_id)
                self.assertEqual(user["username"], "mochi")
                self.assertEqual(user["role"], "mochi")
                auth.logout(session_id)
                self.assertIsNone(SessionRepository(connection).get_user(session_id))

    def test_member_session_keeps_member_role(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = temp_settings(directory)
            database = Database(settings.database_path)
            database.initialize()
            auth = AuthService(database, settings)
            auth.ensure_initial_admin("mochi", "a-secure-local-password")
            member_password = "a-member-local-password"
            with database.connect() as connection:
                UserRepository(connection).create("member", PasswordHasher.hash(member_password), "e-mochi")
            session_id = auth.login("member", member_password)
            with database.connect() as connection:
                self.assertEqual(SessionRepository(connection).get_user(session_id)["role"], "e-mochi")

    def test_invalid_credentials_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = temp_settings(directory)
            database = Database(settings.database_path)
            database.initialize()
            auth = AuthService(database, settings)
            auth.ensure_initial_admin("mochi", "a-secure-local-password")
            with self.assertRaises(Exception):
                auth.login("mochi", "wrong-password")


class MediaServiceTests(unittest.TestCase):
    def test_banner_list_returns_public_asset_urls(self):
        with tempfile.TemporaryDirectory() as directory:
            assets = Path(directory) / "assets"
            banners = assets / "banners"
            banners.mkdir(parents=True)
            (banners / "b.jpg").write_bytes(b"b")
            (banners / "a.jpg").write_bytes(b"a")
            result = MediaService.banner_list(assets)
            self.assertEqual([item["name"] for item in result], ["a.jpg", "b.jpg"])
            self.assertTrue(all(item["url"].startswith("/assets/banners/") for item in result))

    def test_banner_list_is_empty_without_banner_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(MediaService.banner_list(Path(directory) / "assets"), [])

    def test_poster_path_resolves_indexed_poster_inside_root(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = temp_settings(directory)
            media_dir = settings.media_dir
            show = media_dir / "Show"
            show.mkdir(parents=True)
            (show / "poster.webp").write_bytes(b"img")
            library = {"version": 1, "anime": [
                {"id": "show", "title": "Show", "poster": str(show / "poster.webp"), "seasons": []},
            ]}
            write_json(settings.library_path, library)
            media = MediaService(settings, LibraryScanner(settings, logging.getLogger("test-media")))
            self.assertEqual(media.poster_path("show"), (show / "poster.webp").resolve())
            self.assertIsNone(media.poster_path("unknown"))

    def test_poster_path_rejects_files_outside_root(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = temp_settings(directory)
            outsider = Path(directory) / "elsewhere"
            outsider.mkdir()
            (outsider / "poster.webp").write_bytes(b"img")
            library = {"version": 1, "anime": [
                {"id": "show", "title": "Show", "poster": str(outsider / "poster.webp"), "seasons": []},
            ]}
            write_json(settings.library_path, library)
            media = MediaService(settings, LibraryScanner(settings, logging.getLogger("test-media")))
            self.assertIsNone(media.poster_path("show"))


class AdminApiTests(unittest.TestCase):
    """End-to-end API tests for dashboard editing and user management."""

    @classmethod
    def setUpClass(cls):
        try:
            from fastapi.testclient import TestClient  # noqa: F401
        except ImportError as error:  # pragma: no cover
            raise unittest.SkipTest("httpx/TestClient not installed") from error
        from unittest.mock import patch

        from backend.app.main import app
        cls._app = app
        cls._patch = patch("backend.app.main.Settings.load")

    ADMIN_PASSWORD = "a-secure-local-password"

    def setUp(self):
        from fastapi.testclient import TestClient
        self.directory = tempfile.TemporaryDirectory()
        self.settings = temp_settings(self.directory.name)
        show = self.settings.media_dir / "Show"
        show.mkdir(parents=True)
        (show / "poster.webp").write_bytes(b"img")
        write_json(self.settings.library_path, {"version": 1, "anime": [
            {"id": "show", "title": "Show", "poster": str(show / "poster.webp"), "banner": None, "seasons": []},
        ]})
        self.mock = self._patch.start()
        self.mock.return_value = self.settings
        self.client = TestClient(self._app)
        self.client.__enter__()
        # The lifespan auto-creates an admin with a random password; replace it
        # with one we know so the API tests can authenticate.
        with self._app.state.database.connect() as connection:
            connection.execute("DELETE FROM users")
            UserRepository(connection).create("mochi", PasswordHasher.hash(self.ADMIN_PASSWORD), "mochi")

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self._patch.stop()
        self.directory.cleanup()

    def login(self, username: str, password: str):
        response = self.client.post("/api/v1/auth/login", json={"username": username, "password": password})
        self.assertEqual(response.status_code, 200, response.text)

    def test_admin_edits_anime_and_clears_poster(self):
        self.login("mochi", self.ADMIN_PASSWORD)
        response = self.client.patch("/api/v1/dashboard/anime/show", json={"title": "Renamed", "poster": ""})
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()["data"]
        self.assertEqual(data["title"], "Renamed")
        self.assertIsNone(data["poster"])

    def test_member_cannot_edit_library(self):
        from fastapi.testclient import TestClient
        self.login("mochi", self.ADMIN_PASSWORD)
        self.client.post("/api/v1/users", json={"username": "member", "password": "a-member-password", "role": "e-mochi"})
        member_client = TestClient(self._app)
        with member_client:
            response = member_client.post("/api/v1/auth/login", json={"username": "member", "password": "a-member-password"})
            self.assertEqual(response.status_code, 200)
            response = member_client.patch("/api/v1/dashboard/anime/show", json={"title": "Hijacked"})
            self.assertEqual(response.status_code, 403)

    def test_admin_creates_and_deletes_user(self):
        self.login("mochi", self.ADMIN_PASSWORD)
        created = self.client.post("/api/v1/users", json={"username": "newbie", "password": "a-new-member-password", "role": "e-mochi"})
        self.assertEqual(created.status_code, 201, created.text)
        user_id = created.json()["data"]["id"]
        deleted = self.client.delete(f"/api/v1/users/{user_id}")
        self.assertEqual(deleted.status_code, 200)
        listed = self.client.get("/api/v1/users")
        self.assertNotIn("newbie", [user["username"] for user in listed.json()["data"]])


if __name__ == "__main__":
    unittest.main()
