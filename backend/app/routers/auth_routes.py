"""Authentication routes: unlock status, unlock, password change."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ..payloads import PasswordPayload, UnlockPayload, success

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/status")
def status(request: Request):
    """Report whether the application is currently unlocked."""
    return success({"unlocked": request.app.state.auth.is_unlocked()})


@router.post("/unlock")
def unlock(payload: UnlockPayload, request: Request):
    client_host = request.client.host if request.client else "unknown"
    limiter_key = f"unlock|{client_host}"
    limiter = request.app.state.auth.unlock_limiter
    if not limiter.allowed(limiter_key):
        raise HTTPException(status_code=429, detail="Too many unlock attempts. Try again later.")
    if not request.app.state.auth.unlock(payload.password):
        limiter.record_failure(limiter_key)
        raise HTTPException(status_code=401, detail="Incorrect password")
    limiter.reset(limiter_key)
    return success({"unlocked": True})


@router.put("/password")
def change_password(payload: PasswordPayload, request: Request):
    """Change the local password. Requires an unlocked application."""
    request.app.state.auth.change_password(payload.current_password, payload.new_password)
    return success({"changed": True})
