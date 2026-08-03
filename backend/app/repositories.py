from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def row_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


class SecretStore:
    """Single local password hash, stored as one row in the settings table.

    The key is deliberately outside the settings whitelist used by the public
    settings endpoint, so the hash is never returned to the client.
    """

    key = "auth.password_hash"

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def get_password_hash(self) -> str | None:
        row = self.connection.execute(
            "SELECT setting_value FROM settings WHERE setting_key = ?", (self.key,)
        ).fetchone()
        return row[0] if row else None

    def set_password_hash(self, encoded: str) -> None:
        self.connection.execute(
            """INSERT INTO settings(setting_key, setting_value, updated_at) VALUES (?, ?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value,
            updated_at = excluded.updated_at""",
            (self.key, encoded, now_iso()),
        )


class ActivityRepository:
    """Single-user activity data: favorites, progress, watch history, settings."""

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def favorites(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.connection.execute(
            "SELECT anime_id, created_at FROM favorites ORDER BY created_at DESC"
        )]

    def set_favorite(self, anime_id: str, enabled: bool) -> None:
        if enabled:
            self.connection.execute(
                "INSERT OR IGNORE INTO favorites(anime_id, created_at) VALUES (?, ?)",
                (anime_id, now_iso()),
            )
        else:
            self.connection.execute("DELETE FROM favorites WHERE anime_id = ?", (anime_id,))

    def save_progress(self, payload: dict[str, Any]) -> None:
        timestamp = now_iso()
        position = float(payload["playback_position"])
        if position <= 0:
            self.remove_progress(payload["episode_id"])
            return
        self.connection.execute("BEGIN")
        try:
            self.connection.execute(
                """INSERT INTO continue_watching(
                    episode_id, anime_id, season_number, episode_number, playback_position, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(episode_id) DO UPDATE SET
                    anime_id = excluded.anime_id,
                    season_number = excluded.season_number,
                    episode_number = excluded.episode_number,
                    playback_position = excluded.playback_position,
                    updated_at = excluded.updated_at""",
                (
                    payload["episode_id"], payload["anime_id"], payload["season_number"],
                    payload["episode_number"], position, timestamp,
                ),
            )
            if payload.get("completed", False):
                self.connection.execute(
                    """INSERT INTO watch_history(
                        episode_id, anime_id, season_number, episode_number, watched_at
                    ) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(episode_id) DO UPDATE SET
                        anime_id = excluded.anime_id,
                        season_number = excluded.season_number,
                        episode_number = excluded.episode_number,
                        watched_at = excluded.watched_at""",
                    (
                        payload["episode_id"], payload["anime_id"], payload["season_number"],
                        payload["episode_number"], timestamp,
                    ),
                )
                self.connection.execute(
                    "DELETE FROM continue_watching WHERE episode_id = ?",
                    (payload["episode_id"],),
                )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def remove_progress(self, episode_id: str) -> None:
        self.connection.execute(
            "DELETE FROM continue_watching WHERE episode_id = ?", (episode_id,)
        )

    def progress(self, episode_id: str) -> dict[str, Any] | None:
        return row_dict(self.connection.execute(
            "SELECT * FROM continue_watching WHERE episode_id = ?", (episode_id,)
        ).fetchone())

    def continue_watching(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.connection.execute(
            "SELECT * FROM continue_watching ORDER BY updated_at DESC"
        )]

    def history(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.connection.execute(
            "SELECT * FROM watch_history ORDER BY watched_at DESC"
        )]

    def clear_history(self) -> None:
        self.connection.execute("DELETE FROM watch_history")

    def setting_values(self) -> dict[str, str]:
        return {
            row["setting_key"]: row["setting_value"]
            for row in self.connection.execute(
                "SELECT setting_key, setting_value FROM settings WHERE setting_key != ?",
                (SecretStore.key,),
            )
        }

    def save_settings(self, values: dict[str, str]) -> None:
        for key, value in values.items():
            self.connection.execute(
                """INSERT INTO settings(setting_key, setting_value, updated_at) VALUES (?, ?, ?)
                ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value,
                updated_at = excluded.updated_at""",
                (key, value, now_iso()),
            )
