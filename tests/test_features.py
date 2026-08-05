"""Tests for the filesystem library scanner (categories, metadata, warnings,
incremental rebuilds), library search/filter/sort, database maintenance,
single-password unlock, and media asset services."""

import logging
import tempfile
import unittest
from pathlib import Path

from backend.app.auth import AuthService
from backend.app.core import Settings, write_json
from backend.app.database import Database
from backend.app.maintenance import prune_dangling_references
from backend.app.media import MediaService, filter_library
from backend.app.repositories import ActivityRepository, SecretStore
from backend.app.scanner import LibraryScanner, ScanState


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


LIBRARY = {
    "version": 2,
    "entries": [
        {
            "id": "beta",
            "title": "Beta Series",
            "type": "anime",
            "seasons": [{"number": 1, "episodes": [
                {"id": "beta-s01-e01", "number": 1, "title": "First Steps"},
                {"id": "beta-s01-e02", "number": 2, "title": "Deep Dive"},
            ]}],
        },
        {
            "id": "alpha",
            "title": "Alpha Series",
            "type": "anime",
            "seasons": [
                {"number": 1, "episodes": [{"id": "alpha-s01-e01", "number": 1, "title": "Intro"}]},
                {"number": 2, "episodes": [{"id": "alpha-s02-e01", "number": 1, "title": "Return"}]},
            ],
        },
        {"id": "quick-tutorial", "title": "Quick Tutorial", "type": "tutorial", "seasons": [], "episodes": [
            {"id": "quick-tutorial-e01", "number": 1, "title": "Quick Tutorial"},
        ]},
        {"id": "a-movie", "title": "A Movie", "type": "movie", "seasons": [], "episodes": [
            {"id": "a-movie-e01", "number": 1, "title": "A Movie"},
        ]},
    ],
}


class FilterLibraryTests(unittest.TestCase):
    def test_filter_by_category(self):
        for category in ("anime", "tutorial", "movie"):
            entries = filter_library(LIBRARY, category=category)["entries"]
            self.assertTrue(all(entry["type"] == category for entry in entries), category)
        other = filter_library(LIBRARY, category="other")["entries"]
        self.assertEqual(other, [])

    def test_search_by_title(self):
        result = filter_library(LIBRARY, query="alpha")["entries"]
        self.assertEqual([entry["id"] for entry in result], ["alpha"])

    def test_search_by_episode_prunes_unmatched_episodes(self):
        result = filter_library(LIBRARY, query="deep")["entries"]
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "beta")
        episodes = result[0]["seasons"][0]["episodes"]
        self.assertEqual([episode["id"] for episode in episodes], ["beta-s01-e02"])

    def test_search_by_season_number(self):
        result = filter_library(LIBRARY, query="s02")["entries"]
        self.assertEqual([entry["id"] for entry in result], ["alpha"])
        self.assertEqual([season["number"] for season in result[0]["seasons"]], [2])

    def test_search_by_episode_number(self):
        single = {"version": 2, "entries": [LIBRARY["entries"][0]]}
        result = filter_library(single, query="2")["entries"]
        episodes = result[0]["seasons"][0]["episodes"]
        self.assertEqual([episode["id"] for episode in episodes], ["beta-s01-e02"])

    def test_search_matches_standalone_titles_and_prunes_episodes(self):
        result = filter_library(LIBRARY, query="movie")["entries"]
        self.assertEqual([entry["id"] for entry in result], ["a-movie"])

    def test_sort_by_title_and_recent(self):
        by_title = filter_library(LIBRARY, sort_by="title")["entries"]
        by_recent = filter_library(LIBRARY, sort_by="recent")["entries"]
        self.assertEqual([entry["id"] for entry in by_title], ["a-movie", "alpha", "beta", "quick-tutorial"])
        self.assertEqual([entry["id"] for entry in by_recent],
                         ["a-movie", "quick-tutorial", "alpha", "beta"])

    def test_combined_query_category_and_sort(self):
        result = filter_library(LIBRARY, query="alpha", category="anime", sort_by="title")["entries"]
        self.assertEqual([entry["id"] for entry in result], ["alpha"])


def write_video(path: Path, content: bytes = b"v") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


class ScannerCategoryTests(unittest.TestCase):
    """The scanner reads one media root with Anime/Movies/Tutorials/Other."""

    def scan(self, directory: str, media_root: str = "contents"):
        settings = temp_settings(directory)
        settings.media_root = media_root
        settings.media_dir.mkdir(parents=True, exist_ok=True)
        state = ScanState()
        library = LibraryScanner(settings, logging.getLogger("test-scanner")).scan(state)
        return library["entries"], state

    def test_anime_folder_with_seasons_and_bare_number_episodes(self):
        with tempfile.TemporaryDirectory() as directory:
            season = Path(directory) / "contents" / "Anime" / "Naruto" / "Season 1"
            for name in ("1.mp4", "2.mp4", "3.mp4"):
                write_video(season / name)
            write_video(Path(directory) / "contents" / "Anime" / "Naruto" / "poster.webp", b"img")
            entries, _ = self.scan(directory)
            self.assertEqual([entry["id"] for entry in entries], ["naruto"])
            naruto = entries[0]
            self.assertEqual(naruto["type"], "anime")
            self.assertEqual(naruto["poster"], str(Path(directory) / "contents" / "Anime" / "Naruto" / "poster.webp"))
            self.assertEqual([s["number"] for s in naruto["seasons"]], [1])
            episodes = naruto["seasons"][0]["episodes"]
            self.assertEqual([e["number"] for e in episodes], [1, 2, 3])
            self.assertEqual([e["id"] for e in episodes], ["naruto-s01-e01", "naruto-s01-e02", "naruto-s01-e03"])

    def test_episode_titles_are_cleaned(self):
        with tempfile.TemporaryDirectory() as directory:
            season = Path(directory) / "contents" / "Anime" / "Demon Slayer" / "S01"
            for name in ("ep1.mp4", "Episode 2.mp4", "EP 3 - The Fight.mp4", "E04.mp4", "05 - Alone.mp4"):
                write_video(season / name)
            entries, _ = self.scan(directory)
            episodes = entries[0]["seasons"][0]["episodes"]
            self.assertEqual([e["number"] for e in episodes], [1, 2, 3, 4, 5])
            self.assertEqual([e["title"] for e in episodes],
                             ["Episode 1", "Episode 2", "The Fight", "Episode 4", "Alone"])

    def test_videos_without_numbers_are_ordered_by_name(self):
        with tempfile.TemporaryDirectory() as directory:
            season = Path(directory) / "contents" / "Anime" / "Show" / "2"
            for name in ("Zeta.mp4", "Alpha.mp4", "Beta.mp4"):
                write_video(season / name)
            entries, _ = self.scan(directory)
            self.assertEqual([s["number"] for s in entries[0]["seasons"]], [2])
            episodes = entries[0]["seasons"][0]["episodes"]
            self.assertEqual([e["number"] for e in episodes], [1, 2, 3])
            self.assertEqual([e["title"] for e in episodes], ["Alpha", "Beta", "Zeta"])

    def test_duplicate_numbers_get_unique_slots(self):
        with tempfile.TemporaryDirectory() as directory:
            season = Path(directory) / "contents" / "Anime" / "Show" / "Season 1"
            write_video(season / "1.mp4")
            write_video(season / "01.mp4")
            write_video(season / "ep2.mp4")
            entries, _ = self.scan(directory)
            episodes = entries[0]["seasons"][0]["episodes"]
            self.assertEqual([e["number"] for e in episodes], [1, 2, 3])

    def test_videos_directly_in_anime_folder_count_as_season_one(self):
        with tempfile.TemporaryDirectory() as directory:
            anime = Path(directory) / "contents" / "Anime" / "One Piece"
            write_video(anime / "1.mp4")
            write_video(anime / "2.mp4")
            entries, _ = self.scan(directory)
            self.assertEqual([s["number"] for s in entries[0]["seasons"]], [1])
            self.assertEqual([e["number"] for e in entries[0]["seasons"][0]["episodes"]], [1, 2])

    def test_multiple_seasons_are_sorted_by_number(self):
        with tempfile.TemporaryDirectory() as directory:
            anime = Path(directory) / "contents" / "Anime" / "AOT"
            for season in ("Season 2", "Season 1"):
                write_video(anime / season / "1.mp4")
            entries, _ = self.scan(directory)
            self.assertEqual([s["number"] for s in entries[0]["seasons"]], [1, 2])

    def test_standalone_movies_tutorials_and_other(self):
        with tempfile.TemporaryDirectory() as directory:
            movies = Path(directory) / "contents" / "Movies"
            tutorials = Path(directory) / "contents" / "Tutorials"
            other = Path(directory) / "contents" / "Other"
            write_video(movies / "Your Name.mp4")
            write_video(movies / "Your Name.vtt", b"sub")
            write_video(movies / "Your Name.webp", b"img")
            write_video(tutorials / "Guitar Lesson.mp4")
            write_video(other / "Home Video.mp4")
            entries, _ = self.scan(directory)
            ids = [(entry["type"], entry["id"]) for entry in entries]
            self.assertEqual(ids, [("movies", "your-name"), ("tutorials", "guitar-lesson"), ("other", "home-video")])
            movie = next(entry for entry in entries if entry["type"] == "movies")
            self.assertEqual(movie["title"], "Your Name")
            self.assertEqual(movie["episodes"][0]["id"], "your-name-e01")
            self.assertTrue(movie["episodes"][0]["video_path"].endswith("Your Name.mp4"))
            self.assertEqual(len(movie["episodes"][0]["subtitle_paths"]), 1)
            self.assertEqual(movie["poster"], str(movies / "Your Name.webp"))

    def test_standalone_folder_with_single_video(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / "contents" / "Movies" / "A Silent Voice"
            write_video(folder / "movie.mp4")
            write_video(folder / "poster.webp", b"img")
            write_video(folder / "banner.webp", b"img")
            entries, _ = self.scan(directory)
            movie = entries[0]
            self.assertEqual(movie["title"], "A Silent Voice")
            self.assertEqual(movie["episodes"][0]["video_path"], str(folder / "movie.mp4"))
            self.assertTrue(movie["poster"].endswith("poster.webp"))
            self.assertTrue(movie["banner"].endswith("banner.webp"))

    def test_standalone_folder_with_multiple_videos_warns_and_picks(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / "contents" / "Movies" / "Extra"
            write_video(folder / "aa.mp4")
            write_video(folder / "zz.mp4")
            entries, state = self.scan(directory)
            self.assertEqual(entries[0]["episodes"][0]["video_path"].endswith("aa.mp4"), True)
            self.assertTrue(any("Folder contains 2 videos" in warning for warning in state.warnings))

    def test_info_json_metadata_and_title_override(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / "contents" / "Anime" / "Old Folder Name"
            write_video(folder / "Season 1" / "1.mp4")
            write_json(folder / "info.json", {
                "title": "Pretty Title",
                "description": "A story.",
                "year": 2024,
                "genre": ["Action", "Drama"],
                "studio": "Studio X",
            })
            entries, _ = self.scan(directory)
            entry = entries[0]
            self.assertEqual(entry["title"], "Pretty Title")
            self.assertEqual(entry["id"], "pretty-title")
            self.assertEqual(entry["description"], "A story.")
            self.assertEqual(entry["year"], 2024)
            self.assertEqual(entry["genre"], ["Action", "Drama"])
            self.assertEqual(entry["studio"], "Studio X")

    def test_invalid_info_json_is_warned_not_raised(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / "contents" / "Movies" / "Broken"
            write_video(folder / "movie.mp4")
            (folder / "info.json").write_text("{not json", encoding="utf-8")
            entries, state = self.scan(directory)
            self.assertEqual(len(entries), 1)
            self.assertTrue(any("info.json" in warning for warning in state.warnings))

    def test_missing_posters_and_banners_are_tolerated(self):
        with tempfile.TemporaryDirectory() as directory:
            write_video(Path(directory) / "contents" / "Anime" / "Bare" / "1.mp4")
            entries, _ = self.scan(directory)
            self.assertIsNone(entries[0]["poster"])
            self.assertIsNone(entries[0]["banner"])

    def test_empty_and_misplaced_content_is_skipped_with_warnings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "contents"
            (root / "Anime" / "Empty").mkdir(parents=True)
            (root / "Anime" / "Assets").mkdir()
            (root / "Anime" / "Assets" / "notes.txt").write_text("not media", encoding="utf-8")
            (root / "Stray.mp4").write_bytes(b"v")
            (root / "UnknownFolder").mkdir()
            entries, state = self.scan(directory)
            self.assertEqual(entries, [])
            self.assertTrue(any("UnknownFolder" in warning for warning in state.warnings))
            self.assertTrue(any("Stray.mp4" in warning for warning in state.warnings))

    def test_duplicate_slugs_get_unique_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            movies = Path(directory) / "contents" / "Movies"
            write_video(movies / "Show.mp4")
            write_video(movies / "Show!.mp4")
            entries, _ = self.scan(directory)
            self.assertEqual([entry["id"] for entry in entries], ["show", "show-2"])

    def test_incremental_scan_reuses_unchanged_episodes(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = temp_settings(directory)
            settings.media_dir.mkdir(parents=True, exist_ok=True)
            season = settings.media_dir / "Anime" / "Show" / "Season 1"
            first = write_video(season / "1.mp4", b"a")
            write_video(season / "2.mp4", b"b")
            scanner = LibraryScanner(settings, logging.getLogger("test-scanner"))
            first_scan = scanner.scan()["entries"][0]["seasons"][0]["episodes"]
            episodes = {episode["title"]: episode for episode in first_scan}
            self.assertEqual(episodes["Episode 1"]["id"], "show-s01-e01")
            first.write_bytes(b"changed")
            second_scan = scanner.scan()["entries"][0]["seasons"][0]["episodes"]
            ids = {episode["id"] for episode in second_scan}
            self.assertEqual(ids, {"show-s01-e01", "show-s01-e02"})
            self.assertEqual([episode["title"] for episode in second_scan], ["Episode 1", "Episode 2"])

    def test_removed_media_is_dropped_from_incremental_signature_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = temp_settings(directory)
            season = settings.media_dir / "Anime" / "Show" / "Season 1"
            first = write_video(season / "1.mp4")
            removed = write_video(season / "2.mp4")
            scanner = LibraryScanner(settings, logging.getLogger("test-scanner"))
            scanner.scan()
            first.unlink()
            removed.unlink()
            library = scanner.scan()
            self.assertEqual(library["entries"], [])
            self.assertNotIn(str(first), library["signatures"])
            self.assertNotIn(str(removed), library["signatures"])

    def test_my_hero_academia_style_episode_names_sort_by_number(self):
        with tempfile.TemporaryDirectory() as directory:
            season = Path(directory) / "contents" / "Anime" / "My Hero Academia" / "Season 01"
            for name in (
                "My Hero Academia - 03.mp4",
                "My Hero Academia - 01.mp4",
                "My Hero Academia - 02.mp4",
            ):
                write_video(season / name)
            entries, _ = self.scan(directory)
            entry = entries[0]
            self.assertEqual(entry["id"], "my-hero-academia")
            self.assertEqual([episode["number"] for episode in entry["seasons"][0]["episodes"]], [1, 2, 3])
            self.assertEqual([episode["id"] for episode in entry["seasons"][0]["episodes"]], [
                "my-hero-academia-s01-e01",
                "my-hero-academia-s01-e02",
                "my-hero-academia-s01-e03",
            ])

    def test_all_production_categories_and_video_extensions_are_scanned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "contents"
            extensions = ("mp4", "mkv", "webm", "avi", "mov", "m4v", "flv", "mpeg", "ts", "m3u8")
            categories = ("Movies", "Tutorials", "Other", "TV Shows", "Courses")
            for category, extension in zip(categories, extensions):
                write_video(root / category / f"{category} title.{extension}")
            write_video(root / "Anime" / "Series" / "Season 1" / "1.mp4")
            entries, state = self.scan(directory)
            self.assertEqual(len(entries), 6)
            self.assertEqual({entry["type"] for entry in entries}, {
                "anime", "movies", "tutorials", "other", "tv-shows", "courses",
            })
            self.assertEqual(state.counts["episodes"], 6)
            self.assertFalse([warning for warning in state.warnings if "unsupported" in warning.lower()])

    def test_custom_media_root_is_used(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "custom"
            write_video(root / "Movies" / "M.mp4")
            settings = temp_settings(directory)
            settings.media_root = "custom"
            settings.media_dir.mkdir(parents=True, exist_ok=True)
            entries = LibraryScanner(settings, logging.getLogger("test-scanner")).scan()["entries"]
            self.assertEqual(entries[0]["id"], "m")

    def test_public_library_strips_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            write_video(Path(directory) / "contents" / "Tutorials" / "Guitar Lesson.mp4")
            entries, _ = self.scan(directory)
            library = {"version": 2, "entries": entries}
            public = MediaService.public_library(library)
            self.assertNotIn(str(Path(directory) / "contents"), str(public))
            self.assertEqual(public["entries"][0]["episodes"][0]["id"], "guitar-lesson-e01")


class MaintenanceTests(unittest.TestCase):
    def test_prune_removes_only_dangling_references(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Database(Path(directory) / "database.db")
            database.initialize()
            library = {"version": 2, "entries": [{"id": "valid-show", "seasons": [
                {"number": 1, "episodes": [{"id": "valid-ep"}]},
            ]}]}
            with database.connect() as connection:
                activity = ActivityRepository(connection)
                activity.set_favorite("valid-show", True)
                activity.set_favorite("ghost-show", True)
                activity.save_progress({
                    "episode_id": "valid-ep", "anime_id": "valid-show",
                    "season_number": 1, "episode_number": 1, "playback_position": 10,
                })
                activity.save_progress({
                    "episode_id": "ghost-ep", "anime_id": "ghost-show",
                    "season_number": 1, "episode_number": 1, "playback_position": 10,
                })
                repairs = prune_dangling_references(connection, library)
                self.assertEqual(len(repairs), 2)
                self.assertEqual([item["anime_id"] for item in activity.favorites()], ["valid-show"])
                self.assertIsNone(activity.progress("ghost-ep"))
                self.assertIsNotNone(activity.progress("valid-ep"))

    def test_prune_removes_all_rows_when_library_is_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Database(Path(directory) / "database.db")
            database.initialize()
            with database.connect() as connection:
                ActivityRepository(connection).set_favorite("anything", True)
                repairs = prune_dangling_references(connection, {"version": 2, "entries": []})
                self.assertEqual(len(repairs), 1)

    def test_prune_keeps_standalone_episode_progress(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Database(Path(directory) / "database.db")
            database.initialize()
            library = {"version": 2, "entries": [{"id": "guitar-lesson", "episodes": [
                {"id": "guitar-lesson-e01"},
            ]}]}
            with database.connect() as connection:
                activity = ActivityRepository(connection)
                activity.save_progress({
                    "episode_id": "guitar-lesson-e01", "anime_id": "guitar-lesson",
                    "season_number": 1, "episode_number": 1, "playback_position": 10,
                })
                activity.set_favorite("guitar-lesson", True)
                repairs = prune_dangling_references(connection, library)
                self.assertEqual(repairs, [])
                self.assertIsNotNone(activity.progress("guitar-lesson-e01"))
                self.assertEqual(len(activity.favorites()), 1)


class AuthUnlockTests(unittest.TestCase):
    def test_ensure_password_creates_password_once(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = temp_settings(directory)
            database = Database(settings.database_path)
            database.initialize()
            auth = AuthService(database, settings)
            self.assertTrue(auth.ensure_password())
            self.assertFalse(auth.ensure_password())
            self.assertFalse(auth.is_unlocked())

    def test_unlock_accepts_only_the_correct_password(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = temp_settings(directory)
            database = Database(settings.database_path)
            database.initialize()
            auth = AuthService(database, settings)
            auth.ensure_password("a-secure-local-password")
            self.assertFalse(auth.unlock("wrong-password"))
            self.assertTrue(auth.unlock("a-secure-local-password"))
            self.assertTrue(auth.is_unlocked())
            auth.lock()
            self.assertFalse(auth.is_unlocked())

    def test_change_password_replaces_the_unlock_password(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = temp_settings(directory)
            database = Database(settings.database_path)
            database.initialize()
            auth = AuthService(database, settings)
            auth.ensure_password("a-secure-local-password")
            auth.unlock("a-secure-local-password")
            auth.change_password("a-secure-local-password", "a-new-password")
            auth.lock()
            self.assertFalse(auth.unlock("a-secure-local-password"))
            self.assertTrue(auth.unlock("a-new-password"))

    def test_change_password_rejects_incorrect_current_password(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = temp_settings(directory)
            database = Database(settings.database_path)
            database.initialize()
            auth = AuthService(database, settings)
            auth.ensure_password("a-secure-local-password")
            auth.unlock("a-secure-local-password")
            with self.assertRaises(Exception):
                auth.change_password("wrong-password", "a-new-password")
            with database.connect() as connection:
                self.assertIsNotNone(SecretStore(connection).get_password_hash())


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

    def test_poster_and_banner_paths_resolve_indexed_images(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = temp_settings(directory)
            show = settings.media_dir / "Anime" / "Show"
            show.mkdir(parents=True)
            (show / "poster.webp").write_bytes(b"img")
            (show / "banner.webp").write_bytes(b"img")
            library = {"version": 2, "entries": [
                {"id": "show", "title": "Show", "type": "anime",
                 "poster": str(show / "poster.webp"), "banner": str(show / "banner.webp"), "seasons": []},
            ]}
            write_json(settings.library_path, library)
            media = MediaService(settings, LibraryScanner(settings, logging.getLogger("test-media")))
            self.assertEqual(media.poster_path("show"), (show / "poster.webp").resolve())
            self.assertEqual(media.banner_path("show"), (show / "banner.webp").resolve())
            self.assertIsNone(media.poster_path("unknown"))

    def test_asset_paths_reject_files_outside_root(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = temp_settings(directory)
            outsider = Path(directory) / "elsewhere"
            outsider.mkdir()
            (outsider / "poster.webp").write_bytes(b"img")
            library = {"version": 2, "entries": [
                {"id": "show", "title": "Show", "type": "anime",
                 "poster": str(outsider / "poster.webp"), "seasons": []},
            ]}
            write_json(settings.library_path, library)
            media = MediaService(settings, LibraryScanner(settings, logging.getLogger("test-media")))
            self.assertIsNone(media.poster_path("show"))

    def test_update_metadata_writes_info_json_and_refreshes_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = temp_settings(directory)
            show = settings.media_dir / "Anime" / "Show"
            (show / "Season 1").mkdir(parents=True)
            (show / "Season 1" / "1.mp4").write_bytes(b"v")
            scanner = LibraryScanner(settings, logging.getLogger("test-scanner"))
            media = MediaService(settings, scanner)
            media.scan()
            result = media.update_metadata("show", {
                "title": "Renamed", "year": 2021, "genre": ["Drama"], "studio": "X",
            })
            entry = next(item for item in result["entries"] if item["id"] == "show")
            self.assertEqual(entry["title"], "Renamed")
            self.assertEqual(entry["year"], 2021)
            stored = __import__("json").loads((show / "info.json").read_text(encoding="utf-8"))
            self.assertEqual(stored["title"], "Renamed")
            rescanned = scanner.scan()["entries"][0]
            self.assertEqual(rescanned["title"], "Renamed")
            self.assertEqual(rescanned["genre"], ["Drama"])


class AdminApiTests(unittest.TestCase):
    """End-to-end API tests for dashboard editing under the unlock gate."""

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

    UNLOCK_PASSWORD = "a-secure-local-password"

    def setUp(self):
        from fastapi.testclient import TestClient
        self.directory = tempfile.TemporaryDirectory()
        self.settings = temp_settings(self.directory.name)
        show = self.settings.media_dir / "Anime" / "Show"
        (show / "Season 1").mkdir(parents=True)
        (show / "Season 1" / "1.mp4").write_bytes(b"v")
        (show / "poster.webp").write_bytes(b"img")
        scanner = LibraryScanner(self.settings, logging.getLogger("test-admin"))
        MediaService(self.settings, scanner).scan()
        self.mock = self._patch.start()
        self.mock.return_value = self.settings
        self.client = TestClient(self._app)
        self.client.__enter__()
        # The lifespan auto-generates a random bootstrap password; replace it
        # with one we know so the API tests can unlock.
        self._app.state.auth.set_password(self.UNLOCK_PASSWORD)
        self._app.state.auth.lock()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self._patch.stop()
        self.directory.cleanup()

    def unlock(self):
        response = self.client.post("/api/v1/auth/unlock", json={"password": self.UNLOCK_PASSWORD})
        self.assertEqual(response.status_code, 200, response.text)

    def test_admin_edits_metadata_and_persists_info_json(self):
        self.unlock()
        response = self.client.patch("/api/v1/dashboard/anime/show", json={
            "title": "Renamed", "description": "New desc", "year": 2022,
        })
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()["data"]
        self.assertEqual(data["title"], "Renamed")
        self.assertEqual(data["year"], 2022)
        info_path = self.settings.media_dir / "Anime" / "Show" / "info.json"
        self.assertTrue(info_path.exists())
        stored = __import__("json").loads(info_path.read_text(encoding="utf-8"))
        self.assertEqual(stored["title"], "Renamed")

    def test_locked_client_cannot_edit_library(self):
        response = self.client.patch("/api/v1/dashboard/anime/show", json={"title": "Hijacked"})
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
