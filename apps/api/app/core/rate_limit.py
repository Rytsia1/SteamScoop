"""Rate limiting engine and FastAPI dependencies for SteamScoop.

Implements API_SPECIFICATION.md Section 13:
- Sliding-window rate limiting per IP or authenticated identity.
- Emits standard 429 RATE_LIMITED with Retry-After and RateLimit-* headers.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import ClassVar

from fastapi import Request

from app.core.exceptions import RateLimitExceededError


class InMemoryRateLimiter:
    """Thread-safe sliding window in-memory rate limiter."""

    _instances: ClassVar[dict[str, InMemoryRateLimiter]] = {}
    _lock = threading.Lock()

    def __init__(self, key_prefix: str, limit: int, window_seconds: int = 60) -> None:
        self.key_prefix = key_prefix
        self.limit = limit
        self.window_seconds = window_seconds
        self._history: dict[str, list[float]] = defaultdict(list)
        self._inner_lock = threading.Lock()

    @classmethod
    def get_limiter(
        cls, key_prefix: str, limit: int, window_seconds: int = 60
    ) -> InMemoryRateLimiter:
        with cls._lock:
            key = f"{key_prefix}:{limit}:{window_seconds}"
            if key not in cls._instances:
                cls._instances[key] = cls(key_prefix, limit, window_seconds)
            return cls._instances[key]

    def check_and_record(self, identity: str) -> tuple[bool, int, int]:
        """Check if request is permitted.

        Returns (is_allowed, remaining, retry_after).
        """
        now = time.time()
        window_start = now - self.window_seconds

        with self._inner_lock:
            # Clean timestamps older than window
            timestamps = self._history[identity]
            valid_timestamps = [ts for ts in timestamps if ts > window_start]

            if len(valid_timestamps) >= self.limit:
                oldest = valid_timestamps[0]
                retry_after = max(1, int(oldest + self.window_seconds - now))
                self._history[identity] = valid_timestamps
                return False, 0, retry_after

            valid_timestamps.append(now)
            self._history[identity] = valid_timestamps
            remaining = self.limit - len(valid_timestamps)
            return True, remaining, 0

    def reset(self) -> None:
        """Reset history (useful for tests)."""
        with self._inner_lock:
            self._history.clear()


class RateLimitDependency:
    """FastAPI route dependency enforcing rate limits."""

    def __init__(self, limit: int = 60, window_seconds: int = 60, bucket: str = "general") -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.bucket = bucket
        self.limiter = InMemoryRateLimiter.get_limiter(bucket, limit, window_seconds)

    async def __call__(self, request: Request) -> None:
        # Resolve identity: user ID if authenticated, else client host IP
        user = getattr(request.state, "user", None)
        user_id = str(user.id) if user else None
        client_ip = request.client.host if request.client else "127.0.0.1"
        identity = f"{self.bucket}:{user_id or client_ip}"

        allowed, remaining, retry_after = self.limiter.check_and_record(identity)
        if not allowed:
            raise RateLimitExceededError(
                retry_after=retry_after,
                message=(
                    f"Rate limit exceeded for {self.bucket}. Try again in {retry_after} seconds."
                ),
            )

        # Attach rate limit context to request state for response headers
        request.state.rate_limit_limit = self.limit
        request.state.rate_limit_remaining = remaining
        request.state.rate_limit_reset = retry_after
