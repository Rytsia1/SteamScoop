import base64
import json
import uuid
from typing import Any

from app.core.exceptions import InvalidCursorError


def encode_cursor(sort_value: Any, tie_breaker_id: uuid.UUID) -> str:
    """Encode sort position and tie-breaker UUID into an opaque, URL-safe cursor string."""
    payload = {
        "v": sort_value,
        "id": str(tie_breaker_id),
    }
    raw_json = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw_json).decode("ascii")


def decode_cursor(cursor_str: str) -> tuple[Any, uuid.UUID]:
    """Decode an opaque cursor string into its sort value and tie-breaker UUID.

    Raises InvalidCursorError if decoding or validation fails.
    """
    try:
        raw_json = base64.urlsafe_b64decode(cursor_str.encode("ascii")).decode("utf-8")
        payload = json.loads(raw_json)
        if not isinstance(payload, dict) or "v" not in payload or "id" not in payload:
            raise ValueError("Malformed cursor structure")
        tie_breaker_id = uuid.UUID(payload["id"])
        return payload["v"], tie_breaker_id
    except Exception as exc:
        raise InvalidCursorError(
            message="The provided pagination cursor is invalid or malformed."
        ) from exc
