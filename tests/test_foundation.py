import asyncio
import json
import logging
import tempfile
import unittest
from pathlib import Path

from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from backend.app.api import UnlockPayload
from backend.app.auth import PasswordHasher
from backend.app.media import MediaService
from backend.app.core import Settings
from backend.app.database import Database
from backend.app.main import validation_error
from backend.app.repositories import ActivityRepository, SecretStore
from backend.app.scanner import LibraryScanner


class FoundationTests(unittest.TestCase):
    def test_password_hash_is_verifiable_and_not_plaintext(self):
        password = "a secure local password"
        encoded = PasswordHasher.hash(password)
        self.assertNotIn(password, encoded)
        self.assertTrue(PasswordHasher.verify(password, encoded))
        self.assertFalse(PasswordHasher.verify("wrong password", encoded))

    def test_database_migration_creates_documented_tables(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Database(Path(directory) / "database.db")
            database.initialize()
            with database.connect() as connection:
                tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
            self.assertTrue({"favorites", "continue_watching", "watch_history", "settings"} <= tables)
            self.assertNotIn("users", tables)
            self.assertNotIn("sessions", tables)

    def test_scanner_writes_empty_library_without_media(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = Settings(
                data_dir=root / "data",
                config_dir=root / "config",
                media_root="contents",
                logs_dir=root / "logs",
                library_path=root / "data" / "library.json",
            )
            library = LibraryScanner(settings, logging.getLogger("test-scanner")).scan()
            self.assertEqual(library["entries"], [])
            self.assertEqual(library["version"], 2)
            self.assertTrue(settings.library_path.exists())

    def test_activity_progress_updates_history_and_can_be_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Database(Path(directory) / "database.db")
            database.initialize()
            with database.connect() as connection:
                activity = ActivityRepository(connection)
                payload = {
                    "episode_id": "show-s01-e01",
                    "anime_id": "show",
                    "season_number": 1,
                    "episode_number": 1,
                    "playback_position": 42.5,
                }
                activity.save_progress(payload)
                self.assertEqual(activity.progress(payload["episode_id"])["playback_position"], 42.5)
                self.assertEqual(activity.history(), [])
                activity.save_progress({**payload, "completed": True})
                self.assertIsNone(activity.progress(payload["episode_id"]))
                self.assertEqual(len(activity.history()), 1)

    def test_media_service_accepts_only_supported_indexed_formats(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = Settings(media_root=str(root))
            scanner = LibraryScanner(settings, logging.getLogger("test-media"))
            media = MediaService(settings, scanner)
            supported = root / "episode.mp4"
            unsupported = root / "notes.txt"
            supported.write_bytes(b"video")
            unsupported.write_text("private", encoding="utf-8")
            self.assertEqual(media.media_type(str(supported)), "video/mp4")
            with self.assertRaises(Exception):
                media.validated_path(str(unsupported))

    def test_public_library_removes_local_paths(self):
        library = {
            "version": 2,
            "entries": [{
                "id": "show",
                "title": "Show",
                "type": "anime",
                "path": "/private/media/Show",
                "seasons": [{"number": 1, "episodes": [{
                    "id": "show-s01-e01",
                    "video_path": "/private/media/Show/Season 01/Episode 01.mp4",
                    "subtitle_paths": ["/private/media/Show/Season 01/Episode 01.en.vtt"],
                    "thumbnail_path": "/private/media/Show/Season 01/Episode 01.webp",
                    "number": 1,
                }]}],
            }],
        }
        public = MediaService.public_library(library)
        serialized = str(public)
        self.assertNotIn("/private/media", serialized)
        self.assertEqual(public["entries"][0]["seasons"][0]["episodes"][0]["id"], "show-s01-e01")

    def test_secret_store_stores_password_hash_outside_settings_whitelist(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Database(Path(directory) / "database.db")
            database.initialize()
            with database.connect() as connection:
                store = SecretStore(connection)
                self.assertIsNone(store.get_password_hash())
                store.set_password_hash("encoded-hash")
                self.assertEqual(store.get_password_hash(), "encoded-hash")
                # The hash must not leak through the generic settings reader.
                self.assertNotIn(SecretStore.key, ActivityRepository(connection).setting_values())

    def test_validation_error_response_does_not_leak_internals(self):
        with self.assertRaises(ValidationError) as context:
            UnlockPayload(password="")
        request_error = RequestValidationError(context.exception.errors())
        response = asyncio.run(validation_error(None, request_error))
        body = json.loads(response.body)
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")
        self.assertNotIn("backend/app", body["error"]["message"])
        self.assertNotIn("submitted-secret", body["error"]["message"])


if __name__ == "__main__":
    unittest.main()
