"""Settings routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from ..auth import require_unlocked
from ..payloads import SettingsPayload, success
from ..repositories import ActivityRepository

router = APIRouter(prefix="/api/v1", tags=["settings"])

ALLOWED_SETTING_KEYS = {
    "theme",
    "default_volume",
    "default_speed",
    "subtitles_default",
    "reduce_motion",
    "welcome_screen",
    "teacher_shortcut",
    "reading_page",
}


def filter_settings(values: dict[str, str]) -> dict[str, str]:
    """Reject unknown setting keys at the API boundary.

    The settings table is key/value storage; a client must not be able to
    write arbitrary rows into it (the password hash lives there under a key
    that is never part of the whitelist).
    """
    return {key: value for key, value in values.items() if key in ALLOWED_SETTING_KEYS}


@router.get("/settings")
def get_settings(request: Request, _: Annotated[bool, Depends(require_unlocked)]):
    with request.app.state.database.connect() as db:
        return success(ActivityRepository(db).setting_values())


@router.put("/settings")
def update_settings(payload: SettingsPayload, request: Request, _: Annotated[bool, Depends(require_unlocked)]):
    values = filter_settings(payload.values)
    with request.app.state.database.connect() as db:
        ActivityRepository(db).save_settings(values)
    return success(values)
