from __future__ import annotations

import sqlite3
from pathlib import Path


MIGRATIONS: tuple[tuple[int, str], ...] = (
    (
        1,
        """
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anime_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(anime_id)
        );
        CREATE TABLE IF NOT EXISTS continue_watching (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            episode_id TEXT NOT NULL,
            anime_id TEXT NOT NULL,
            season_number INTEGER NOT NULL,
            episode_number INTEGER NOT NULL,
            playback_position REAL NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL,
            UNIQUE(episode_id)
        );
        CREATE TABLE IF NOT EXISTS watch_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            episode_id TEXT NOT NULL,
            anime_id TEXT NOT NULL,
            season_number INTEGER NOT NULL,
            episode_number INTEGER NOT NULL,
            watched_at TEXT NOT NULL,
            UNIQUE(episode_id)
        );
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT NOT NULL UNIQUE,
            setting_value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_continue_updated ON continue_watching(updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_history_watched ON watch_history(watched_at DESC);
        """,
    ),
)


class Database:
    def __init__(self, path: Path):
        self.path = path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
            )
            applied = {
                row[0] for row in connection.execute("SELECT version FROM schema_migrations")
            }
            for version, sql in MIGRATIONS:
                if version in applied:
                    continue
                connection.executescript(sql)
                connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (?, datetime('now'))",
                    (version,),
                )
