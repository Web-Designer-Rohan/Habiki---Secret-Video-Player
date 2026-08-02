from __future__ import annotations

import json
import logging
import logging.handlers
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(slots=True)
class Settings:
    project_root: Path = PROJECT_ROOT
    data_dir: Path = PROJECT_ROOT / "data"
    config_dir: Path = PROJECT_ROOT / "config"
    media_dir: Path = PROJECT_ROOT / "media"
    logs_dir: Path = PROJECT_ROOT / "logs"
    frontend_dir: Path = PROJECT_ROOT / "frontend"
    database_path: Path = PROJECT_ROOT / "data" / "database.db"
    library_path: Path = PROJECT_ROOT / "data" / "library.json"
    config_path: Path = PROJECT_ROOT / "config" / "config.json"
    version: str = "0.2.0"
    default_language: str = "hi"
    session_days: int = 14
    library_paths: list[str] = field(default_factory=list)
    secret_key: str = ""

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
            settings.default_language = stored.get("language", settings.default_language)
            dashboard = stored.get("dashboard", {})
            settings.session_days = int(dashboard.get("session_days", stored.get("session_days", settings.session_days)))
            if settings.session_days < 1:
                raise ValueError("dashboard.session_days must be at least 1")
            settings.library_paths = [str(path) for path in stored.get("library_paths", [])]
            settings.secret_key = str(stored.get("secret_key", ""))
        else:
            settings.save()
        return settings

    def library_roots(self) -> list[Path]:
        paths = [Path(path).expanduser().resolve() for path in self.library_paths]
        return paths or [self.media_dir.resolve()]

    def save(self) -> None:
        payload = {
            "library_paths": [str(Path(path).expanduser()) for path in self.library_paths],
            "language": self.default_language,
            "theme": "dark",
            "player": {
                "default_volume": 1.0,
                "default_speed": 1.0,
                "subtitles_enabled": True,
            },
            "dashboard": {"session_days": self.session_days},
        }
        if self.secret_key:
            payload["secret_key"] = self.secret_key
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
    """Raised when credentials or a session are invalid."""


class AuthorizationError(HibikiError):
    """Raised when a user lacks permission for an operation."""
