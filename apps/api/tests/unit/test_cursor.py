import uuid
from datetime import UTC, datetime

import pytest

from app.core.cursor import decode_cursor, encode_cursor
from app.core.exceptions import InvalidCursorError


def test_encode_and_decode_cursor_valid() -> None:
    test_id = uuid.uuid4()
    now_iso = datetime.now(UTC).isoformat()

    token = encode_cursor(now_iso, test_id)
    assert isinstance(token, str)
    assert len(token) > 0

    val, decoded_id = decode_cursor(token)
    assert val == now_iso
    assert decoded_id == test_id


def test_encode_and_decode_integer_cursor() -> None:
    test_id = uuid.uuid4()
    votes = 42

    token = encode_cursor(votes, test_id)
    val, decoded_id = decode_cursor(token)

    assert val == votes
    assert decoded_id == test_id


def test_decode_cursor_invalid_base64() -> None:
    with pytest.raises(InvalidCursorError) as exc_info:
        decode_cursor("not-valid-base64@@@!!!")
    assert exc_info.value.code == "INVALID_CURSOR"
    assert exc_info.value.status_code == 400


def test_decode_cursor_invalid_json() -> None:
    # "hello" encoded in base64url is "aGVsbG8"
    with pytest.raises(InvalidCursorError) as exc_info:
        decode_cursor("aGVsbG8")
    assert exc_info.value.code == "INVALID_CURSOR"


def test_decode_cursor_invalid_structure() -> None:
    # JSON array with 3 elements or non-UUID id
    import base64
    import json

    # 1 element array
    bad_token1 = base64.urlsafe_b64encode(json.dumps(["val_only"]).encode()).decode()
    with pytest.raises(InvalidCursorError):
        decode_cursor(bad_token1)

    # Invalid UUID string
    bad_token2 = base64.urlsafe_b64encode(json.dumps(["val", "not-a-uuid"]).encode()).decode()
    with pytest.raises(InvalidCursorError):
        decode_cursor(bad_token2)
