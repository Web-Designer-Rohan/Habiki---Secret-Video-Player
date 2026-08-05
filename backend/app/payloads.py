"""Pydantic request/response models shared across API routers."""

from __future__ import annotations

import math
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


SettingsValue = str | int | float | bool


def validate_reading_page(value: str) -> str:
    """Allow http(s) URLs and same-origin relative paths only."""
    value = value.strip()
    if not value:
        return value
    if any(ord(character) < 32 for character in value):
        raise ValueError("reading_page contains invalid control characters")
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"}:
        if not parsed.netloc:
            raise ValueError("reading_page must include a host")
    elif parsed.scheme or parsed.netloc or value.startswith("//"):
        raise ValueError("reading_page must be an http(s) URL or a relative path")
    return value


def setting_text(value: SettingsValue) -> str:
    """Persist all UI settings as the string values used by the key/value store."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


class SettingsPayload(BaseModel):
    values: dict[str, SettingsValue] = Field(default_factory=dict)

    @field_validator("values")
    @classmethod
    def validate_values(cls, values: dict[str, SettingsValue]) -> dict[str, SettingsValue]:
        if "reading_page" in values:
            validate_reading_page(setting_text(values["reading_page"]))
        if "default_volume" in values:
            try:
                volume = float(values["default_volume"])
            except (TypeError, ValueError):
                raise ValueError("default_volume must be a number") from None
            if not math.isfinite(volume) or not 0 <= volume <= 100:
                raise ValueError("default_volume must be between 0 and 100")
        if "default_speed" in values:
            try:
                speed = float(values["default_speed"])
            except (TypeError, ValueError):
                raise ValueError("default_speed must be a number") from None
            if not math.isfinite(speed) or not 0.25 <= speed <= 4:
                raise ValueError("default_speed must be between 0.25 and 4")
        return values


class ConfigPayload(BaseModel):
    media_root: str = Field(min_length=1, max_length=300)


class UnlockPayload(BaseModel):
    password: str = Field(min_length=1, max_length=256)


class PasswordPayload(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=8, max_length=256)


class ProgressPayload(BaseModel):
    episode_id: str = Field(min_length=1, max_length=200)
    anime_id: str = Field(min_length=1, max_length=200)
    season_number: int = Field(ge=1)
    episode_number: int = Field(ge=1)
    playback_position: float = Field(ge=0)
    completed: bool = False


class FavoritePayload(BaseModel):
    enabled: bool = True




class AnimeEditPayload(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    year: int | None = Field(default=None, ge=1000, le=9999)
    genre: list[str] | str | None = None
    studio: str | None = Field(default=None, max_length=200)


def success(data: Any) -> dict[str, Any]:
    return {"success": True, "data": data}
