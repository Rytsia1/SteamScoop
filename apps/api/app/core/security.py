"""Security and cryptographic primitives for SteamScoop authentication.

Implements password hashing using scrypt with random salt, constant-time verification,
and secure session token generation.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import time
import uuid
from dataclasses import dataclass
from typing import ClassVar


def hash_password(plain_password: str) -> str:
    """Hash password using scrypt with a 16-byte random salt."""
    salt = secrets.token_bytes(16)
    salt_hex = salt.hex()
    hashed = hashlib.scrypt(
        plain_password.encode("utf-8"),
        salt=salt,
        n=16384,
        r=8,
        p=1,
    )
    hash_hex = hashed.hex()
    return f"$scrypt$n=16384,r=8,p=1${salt_hex}${hash_hex}"


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    """Verify password against scrypt hash in constant time."""
    if not hashed_password or not hashed_password.startswith("$scrypt$"):
        return False

    try:
        parts = hashed_password.split("$")
        # ['', 'scrypt', 'n=16384,r=8,p=1', '<salt_hex>', '<hash_hex>']
        if len(parts) != 5:
            return False

        salt = bytes.fromhex(parts[3])
        expected_hash = bytes.fromhex(parts[4])

        computed_hash = hashlib.scrypt(
            plain_password.encode("utf-8"),
            salt=salt,
            n=16384,
            r=8,
            p=1,
        )
        return hmac.compare_digest(computed_hash, expected_hash)
    except Exception:
        return False


def generate_session_token() -> str:
    """Generate cryptographically secure 256-bit URL-safe session token."""
    return secrets.token_urlsafe(32)


@dataclass(frozen=True)
class SessionData:
    """Active user session data."""

    session_token: str
    user_id: uuid.UUID
    email: str
    roles: list[str]
    expires_at: float


class SessionStore:
    """Thread-safe server-managed session store."""

    _instance: ClassVar[SessionStore | None] = None
    _lock = threading.Lock()

    def __init__(self, default_ttl_seconds: int = 86400 * 7) -> None:
        self.default_ttl = default_ttl_seconds
        self._sessions: dict[str, SessionData] = {}
        self._lock = threading.Lock()

    @classmethod
    def get_store(cls) -> SessionStore:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def create_session(
        self, user_id: uuid.UUID, email: str, roles: list[str], ttl_seconds: int | None = None
    ) -> SessionData:
        ttl = ttl_seconds or self.default_ttl
        token = generate_session_token()
        session_data = SessionData(
            session_token=token,
            user_id=user_id,
            email=email,
            roles=roles,
            expires_at=time.time() + ttl,
        )
        with self._lock:
            self._sessions[token] = session_data
        return session_data

    def get_session(self, token: str) -> SessionData | None:
        with self._lock:
            data = self._sessions.get(token)
            if not data:
                return None
            if time.time() > data.expires_at:
                del self._sessions[token]
                return None
            return data

    def delete_session(self, token: str) -> bool:
        with self._lock:
            if token in self._sessions:
                del self._sessions[token]
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            self._sessions.clear()

