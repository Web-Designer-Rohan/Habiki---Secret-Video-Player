"""Pydantic request/response models shared across API routers."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


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


class SettingsPayload(BaseModel):
    values: dict[str, str] = Field(default_factory=dict)


class ConfigPayload(BaseModel):
    media_root: str = Field(min_length=1, max_length=300)


class AnimeEditPayload(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    year: int | None = Field(default=None, ge=1000, le=9999)
    genre: list[str] | str | None = None
    studio: str | None = Field(default=None, max_length=200)


def success(data: Any) -> dict[str, Any]:
    return {"success": True, "data": data}
