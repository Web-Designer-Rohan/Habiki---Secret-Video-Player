"""Database maintenance helpers shared by the dashboard and validation tooling.

The dashboard "refresh database" action and scripts/validate_library.py use the
same pruning rules so user activity rows never reference anime or episodes that
no longer exist in the library metadata.
"""

from __future__ import annotations

import sqlite3
from typing import Any


def prune_dangling_references(connection: sqlite3.Connection, library: dict[str, Any]) -> list[str]:
    """Delete user-activity rows whose anime/episode no longer exists.

    Returns a list of human-readable repair descriptions (empty when healthy).
    Executes inside a single transaction.
    """
    anime_ids = {anime["id"] for anime in library.get("anime", [])}
    episode_ids = {
        episode["id"]
        for anime in library.get("anime", [])
        for season in anime.get("seasons", [])
        for episode in season.get("episodes", [])
    }
    repairs: list[str] = []

    def column_names(table: str) -> set[str]:
        return {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}

    with connection:
        for table in ("favorites", "continue_watching", "watch_history"):
            if "anime_id" not in column_names(table):
                continue
            if anime_ids:
                rows = connection.execute(
                    f"SELECT id FROM {table} WHERE anime_id NOT IN ({','.join('?' * len(anime_ids))})",
                    tuple(anime_ids),
                ).fetchall()
            else:
                rows = connection.execute(f"SELECT id FROM {table}").fetchall()
            for row in rows:
                connection.execute(f"DELETE FROM {table} WHERE id = ?", (row[0],))
                repairs.append(f"pruned dangling {table} row {row[0]}")

        for table in ("continue_watching", "watch_history"):
            if "episode_id" not in column_names(table):
                continue
            for row in connection.execute(f"SELECT id, episode_id FROM {table}").fetchall():
                if row["episode_id"] not in episode_ids:
                    connection.execute(f"DELETE FROM {table} WHERE id = ?", (row["id"],))
                    repairs.append(f"pruned dangling {table} row {row['id']}")

    return repairs
