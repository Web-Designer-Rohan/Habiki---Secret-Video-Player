from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from typing import Annotated

from fastapi import Depends, Request

from .core import AuthenticationError, Settings
from .database import Database
from .repositories import SecretStore


class LoginRateLimiter:
    """Sliding-window brute-force protection for the unlock endpoint.

    Failures are tracked per ``client_host``; a key is locked out until the
    oldest failure falls outside the window. Success resets the key.
    """

    def __init__(self, max_attempts: int = 5, window_seconds: int = 900):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._failures: dict[str, list[float]] = {}

    def _prune(self, key: str, now: float) -> list[float]:
        cutoff = now - self.window_seconds
        kept = [stamp for stamp in self._failures.get(key, []) if stamp > cutoff]
        if kept:
            self._failures[key] = kept
        else:
            self._failures.pop(key, None)
        return kept

    def allowed(self, key: str, now: float | None = None) -> bool:
        now = now if now is not None else time.monotonic()
        return len(self._prune(key, now)) < self.max_attempts

    def record_failure(self, key: str, now: float | None = None) -> None:
        now = now if now is not None else time.monotonic()
        self._prune(key, now)
        self._failures.setdefault(key, []).append(now)

    def reset(self, key: str) -> None:
        self._failures.pop(key, None)


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
    """Single local password gate for the whole application.

    The application starts locked. Unlocking with the correct password keeps
    the application usable until the process closes; no sessions are persisted.
    """

    def __init__(self, database: Database, settings: Settings):
        self.database = database
        self.settings = settings
        self.unlock_limiter = LoginRateLimiter()
        self._unlocked = False

    def ensure_password(self, password: str | None = None) -> bool:
        """Create an initial random password when none is stored yet.

        Returns True when a password was created. The generated password is
        written to config/initial-admin.txt (never overwriting an existing
        file) and logged for the operator.
        """
        with self.database.connect() as connection:
            if SecretStore(connection).get_password_hash():
                return False
            initial_password = password or secrets.token_urlsafe(18)
            SecretStore(connection).set_password_hash(PasswordHasher.hash(initial_password))
        if password is None:
            credential_file = self.settings.config_path.with_name("initial-admin.txt")
            if credential_file.exists():
                self._logger().warning("initial-admin.txt already exists; keeping the existing file")
            else:
                credential_file.write_text(
                    f"Password: {initial_password}\n"
                    "Delete this file after unlocking.\n",
                    encoding="utf-8",
                )
        return True

    def is_unlocked(self) -> bool:
        return self._unlocked

    def unlock(self, password: str) -> bool:
        with self.database.connect() as connection:
            encoded = SecretStore(connection).get_password_hash()
        if not encoded or not PasswordHasher.verify(password, encoded):
            return False
        self._unlocked = True
        return True

    def set_password(self, password: str) -> None:
        """Replace the stored password hash (used at first launch and in tests)."""
        with self.database.connect() as connection:
            SecretStore(connection).set_password_hash(PasswordHasher.hash(password))

    def lock(self) -> None:
        self._unlocked = False

    def change_password(self, current: str, new: str) -> None:
        if not self._unlocked:
            raise AuthenticationError("Unlock required")
        with self.database.connect() as connection:
            store = SecretStore(connection)
            encoded = store.get_password_hash()
            if not encoded or not PasswordHasher.verify(current, encoded):
                raise AuthenticationError("Current password is incorrect")
            store.set_password_hash(PasswordHasher.hash(new))

    @staticmethod
    def _logger():
        import logging
        return logging.getLogger("hibiki.application")


def require_unlocked(request: Request) -> bool:
    """Dependency guarding administrative and activity endpoints."""
    if not request.app.state.auth.is_unlocked():
        raise AuthenticationError("Unlock required")
    return True
