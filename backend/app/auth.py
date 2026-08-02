from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, Request

from .core import AuthenticationError, AuthorizationError, Settings
from .database import Database
from .repositories import SessionRepository, UserRepository


class PasswordHasher:
    algorithm = "scrypt"

    @staticmethod
    def hash(password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
        return "$".join((PasswordHasher.algorithm, base64.urlsafe_b64encode(salt).decode(), digest.hex()))

    @staticmethod
    def verify(password: str, encoded: str) -> bool:
        try:
            algorithm, salt_text, digest_text = encoded.split("$", 2)
            if algorithm != PasswordHasher.algorithm:
                return False
            salt = base64.urlsafe_b64decode(salt_text.encode())
            digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
            return hmac.compare_digest(digest.hex(), digest_text)
        except (ValueError, TypeError):
            return False


class AuthService:
    cookie_name = "hibiki_session"

    def __init__(self, database: Database, settings: Settings):
        self.database = database
        self.settings = settings

    def ensure_initial_admin(self, username: str = "mochi", password: str | None = None) -> bool:
        with self.database.connect() as connection:
            users = UserRepository(connection)
            if users.count() > 0:
                return False
            initial_password = password or secrets.token_urlsafe(18)
            users.create(username, PasswordHasher.hash(initial_password), "mochi")
            if password is None:
                self.settings.config_path.with_name("initial-admin.txt").write_text(
                    f"Username: {username}\nPassword: {initial_password}\nDelete this file after signing in.\n",
                    encoding="utf-8",
                )
            return True

    def login(self, username: str, password: str) -> str:
        with self.database.connect() as connection:
            user = UserRepository(connection).get_by_username(username)
            if not user or not PasswordHasher.verify(password, user["password_hash"]):
                raise AuthenticationError("Invalid username or password")
            session_id = secrets.token_urlsafe(32)
            expires_at = datetime.now(timezone.utc) + timedelta(days=self.settings.session_days)
            SessionRepository(connection).create(session_id, user["id"], expires_at.isoformat())
            return session_id

    def logout(self, session_id: str | None) -> None:
        if session_id:
            with self.database.connect() as connection:
                SessionRepository(connection).delete(session_id)

    def current_user(self, request: Request) -> dict:
        session_id = request.cookies.get(self.cookie_name)
        if not session_id:
            raise AuthenticationError("Authentication required")
        with self.database.connect() as connection:
            user = SessionRepository(connection).get_user(session_id)
        if not user:
            raise AuthenticationError("Session expired")
        return user


def current_user(request: Request) -> dict:
    service = request.app.state.auth
    return service.current_user(request)


def require_mochi(user: Annotated[dict, Depends(current_user)]) -> dict:
    if user["role"] != "mochi":
        raise AuthorizationError("Mochi administrator access required")
    return user
