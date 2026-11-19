"""Username/password authentication with short-lived opaque sessions."""

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from backend.app.config import PROJECT_ROOT, settings


def _verify_password(password: str, stored: str) -> bool:
    if "$" not in stored:
        return False
    salt, expected_hex = stored.split("$", 1)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return hmac.compare_digest(dk.hex(), expected_hex)


class AuthService:
    """Authenticates the configured admin and existing local user records."""

    def __init__(self):
        self._sessions: dict[str, dict[str, Any]] = {}
        self.auth_dir = PROJECT_ROOT / "artifacts" / "auth"
        self.auth_dir.mkdir(parents=True, exist_ok=True)
        self.users_path = self.auth_dir / "users.json"
        if not self.users_path.exists():
            self._write_users([])

    def _read_users(self) -> list:
        with open(self.users_path, "r", encoding="utf-8") as user_file:
            return json.load(user_file)

    def _write_users(self, users: list) -> None:
        with open(self.users_path, "w", encoding="utf-8") as user_file:
            json.dump(users, user_file, indent=2)

    def _create_session(self, username: str, role: str, email: str | None = None) -> Dict[str, Any]:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=12)
        self._sessions[token] = {"username": username, "role": role, "email": email, "expires_at": expires_at}
        return {"token": token, "username": username, "role": role, **({"email": email} if email else {})}

    def get_session(self, token: str) -> Dict[str, Any] | None:
        session = self._sessions.get(token)
        if not session:
            return None
        if datetime.now(timezone.utc) >= session["expires_at"]:
            self._sessions.pop(token, None)
            return None
        return {key: value for key, value in session.items() if key != "expires_at"}

    def revoke_session(self, token: str) -> None:
        self._sessions.pop(token, None)

    def authenticate(self, identifier: str, password: str) -> Dict[str, Any]:
        clean_identifier = identifier.strip()
        if hmac.compare_digest(clean_identifier, settings.admin_user) and hmac.compare_digest(
            password, settings.admin_password
        ):
            return self._create_session(settings.admin_user, "Admin")

        for user in self._read_users():
            if user.get("username", "").lower() == clean_identifier.lower() or user.get("email", "").lower() == clean_identifier.lower():
                if _verify_password(password, user.get("password_hash", "")):
                    return self._create_session(
                        user["username"], user.get("role", "MLOps Engineer"), user.get("email")
                    )
                break
        raise ValueError("Invalid username or password.")
