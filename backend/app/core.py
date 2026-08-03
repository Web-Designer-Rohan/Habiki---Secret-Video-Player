from __future__ import annotations

import json
import logging
import logging.handlers
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

VERSION = "1.0.0"


@dataclass(slots=True)
class Settings:
    project_root: Path = PROJECT_ROOT
    data_dir: Path = PROJECT_ROOT / "data"
    config_dir: Path = PROJECT_ROOT / "config"
    media_root: str = "contents"
    logs_dir: Path = PROJECT_ROOT / "logs"
    frontend_dir: Path = PROJECT_ROOT / "frontend"
    database_path: Path = PROJECT_ROOT / "data" / "database.db"
    library_path: Path = PROJECT_ROOT / "data" / "library.json"
    config_path: Path = PROJECT_ROOT / "config" / "config.json"
    version: str = VERSION

    @property
    def media_dir(self) -> Path:
        """Resolve the configured media root to an absolute directory.

        Relative values are interpreted against the project root, so the
        default ``contents`` means ``<project>/contents``. Absolute paths are
        used verbatim (media may live outside the repository).
        """
        root = Path(self.media_root).expanduser()
        return root.resolve() if root.is_absolute() else (self.project_root / root).resolve()

    @classmethod
    def load(cls) -> "Settings":
        settings = cls()
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        settings.config_dir.mkdir(parents=True, exist_ok=True)
        settings.media_dir.mkdir(parents=True, exist_ok=True)
        settings.logs_dir.mkdir(parents=True, exist_ok=True)

        if settings.config_path.exists():
            try:
                stored = json.loads(settings.config_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise RuntimeError(f"Unable to read configuration: {error}") from error
            settings.media_root = stored.get("media_root", "contents")
            # Legacy fallback: the first configured library path becomes the
            # single media root when no media_root was stored yet.
            if "media_root" not in stored and stored.get("library_paths"):
                settings.media_root = stored["library_paths"][0]
        else:
            settings.save()
        return settings

    def save(self) -> None:
        payload = {
            "media_root": self.media_root,
            "theme": "dark",
            "player": {
                "default_volume": 1.0,
                "default_speed": 1.0,
                "subtitles_enabled": True,
            },
        }
        self.config_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def setup_logging(settings: Settings) -> dict[str, logging.Logger]:
    format_string = "%(asctime)s %(levelname)s %(name)s %(message)s"
    formatter = logging.Formatter(format_string)
    loggers: dict[str, logging.Logger] = {}
    for name, filename in (
        ("application", "application.log"),
        ("scanner", "scanner.log"),
        ("errors", "errors.log"),
    ):
        logger = logging.getLogger(f"hibiki.{name}")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        if not logger.handlers:
            handler = logging.handlers.RotatingFileHandler(
                settings.logs_dir / filename,
                maxBytes=1_000_000,
                backupCount=3,
                encoding="utf-8",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        loggers[name] = logger
    return loggers


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Unable to read JSON file {path}: {error}") from error


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    temporary_path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary_path, path)


class HibikiError(Exception):
    """Base error for expected application failures."""


class AuthenticationError(HibikiError):
    """Raised when credentials are invalid or the application is locked."""
