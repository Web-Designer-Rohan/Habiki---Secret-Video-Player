from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def row_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


class UserRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def count(self) -> int:
        return int(self.connection.execute("SELECT COUNT(*) FROM users").fetchone()[0])

    def create(self, username: str, password_hash: str, role: str) -> dict[str, Any]:
        timestamp = now_iso()
        cursor = self.connection.execute(
            "INSERT INTO users(username, password_hash, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (username, password_hash, role, timestamp, timestamp),
        )
        return self.get_by_id(cursor.lastrowid) or {}

    def get_by_username(self, username: str) -> dict[str, Any] | None:
        return row_dict(self.connection.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone())

    def get_by_id(self, user_id: int) -> dict[str, Any] | None:
        return row_dict(self.connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())

    def list(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.connection.execute("SELECT id, username, role, created_at, updated_at FROM users ORDER BY id")]

    def delete(self, user_id: int) -> bool:
        cursor = self.connection.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return cursor.rowcount > 0


class SessionRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def create(self, session_id: str, user_id: int, expires_at: str) -> None:
        self.connection.execute(
            "INSERT INTO sessions(session_id, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (session_id, user_id, now_iso(), expires_at),
        )

    def get_user(self, session_id: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT users.* FROM sessions JOIN users ON users.id = sessions.user_id "
            "WHERE sessions.session_id = ? AND sessions.expires_at > datetime('now')",
            (session_id,),
        ).fetchone()
        return row_dict(row)

    def delete(self, session_id: str) -> None:
        self.connection.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))

    def delete_expired(self) -> None:
        self.connection.execute("DELETE FROM sessions WHERE expires_at <= datetime('now')")


class ActivityRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def favorites(self, user_id: int) -> list[dict[str, Any]]:
        return [dict(row) for row in self.connection.execute(
            "SELECT anime_id, created_at FROM favorites WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        )]

    def set_favorite(self, user_id: int, anime_id: str, enabled: bool) -> None:
        if enabled:
            self.connection.execute(
                "INSERT OR IGNORE INTO favorites(user_id, anime_id, created_at) VALUES (?, ?, ?)",
                (user_id, anime_id, now_iso()),
            )
        else:
            self.connection.execute("DELETE FROM favorites WHERE user_id = ? AND anime_id = ?", (user_id, anime_id))

    def save_progress(self, user_id: int, payload: dict[str, Any]) -> None:
        timestamp = now_iso()
        position = float(payload["playback_position"])
        if position <= 0:
            self.remove_progress(user_id, payload["episode_id"])
            return
        self.connection.execute("BEGIN")
        try:
            self.connection.execute(
                """INSERT INTO continue_watching(
                    user_id, episode_id, anime_id, season_number, episode_number, playback_position, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, episode_id) DO UPDATE SET
                    anime_id = excluded.anime_id,
                    season_number = excluded.season_number,
                    episode_number = excluded.episode_number,
                    playback_position = excluded.playback_position,
                    updated_at = excluded.updated_at""",
                (
                    user_id, payload["episode_id"], payload["anime_id"], payload["season_number"],
                    payload["episode_number"], position, timestamp,
                ),
            )
            if payload.get("completed", False):
                self.connection.execute(
                    """INSERT INTO watch_history(
                        user_id, episode_id, anime_id, season_number, episode_number, watched_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, episode_id) DO UPDATE SET
                        anime_id = excluded.anime_id,
                        season_number = excluded.season_number,
                        episode_number = excluded.episode_number,
                        watched_at = excluded.watched_at""",
                    (
                        user_id, payload["episode_id"], payload["anime_id"], payload["season_number"],
                        payload["episode_number"], timestamp,
                    ),
                )
                self.connection.execute(
                    "DELETE FROM continue_watching WHERE user_id = ? AND episode_id = ?",
                    (user_id, payload["episode_id"]),
                )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def remove_progress(self, user_id: int, episode_id: str) -> None:
        self.connection.execute(
            "DELETE FROM continue_watching WHERE user_id = ? AND episode_id = ?",
            (user_id, episode_id),
        )

    def progress(self, user_id: int, episode_id: str) -> dict[str, Any] | None:
        return row_dict(self.connection.execute(
            "SELECT * FROM continue_watching WHERE user_id = ? AND episode_id = ?", (user_id, episode_id)
        ).fetchone())

    def continue_watching(self, user_id: int) -> list[dict[str, Any]]:
        return [dict(row) for row in self.connection.execute(
            "SELECT * FROM continue_watching WHERE user_id = ? ORDER BY updated_at DESC", (user_id,)
        )]

    def history(self, user_id: int) -> list[dict[str, Any]]:
        return [dict(row) for row in self.connection.execute(
            "SELECT * FROM watch_history WHERE user_id = ? ORDER BY watched_at DESC", (user_id,)
        )]

    def clear_history(self, user_id: int) -> None:
        self.connection.execute("DELETE FROM watch_history WHERE user_id = ?", (user_id,))

    def setting_values(self, user_id: int) -> dict[str, str]:
        return {
            row["setting_key"]: row["setting_value"]
            for row in self.connection.execute("SELECT setting_key, setting_value FROM settings WHERE user_id = ?", (user_id,))
        }

    def save_settings(self, user_id: int, values: dict[str, str]) -> None:
        for key, value in values.items():
            self.connection.execute(
                """INSERT INTO settings(user_id, setting_key, setting_value, updated_at) VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, setting_key) DO UPDATE SET setting_value = excluded.setting_value,
                updated_at = excluded.updated_at""",
                (user_id, key, value, now_iso()),
            )
