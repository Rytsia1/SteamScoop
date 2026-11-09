from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.integrations.steam.exceptions import (
    SteamGameUnavailableError,
    SteamMalformedResponseError,
)
from app.integrations.steam.normalizer import (
    parse_app_reviews_response,
    parse_steam_release_date,
    parse_store_appdetails_response,
)
from tests.fixtures.steam_fixtures import (
    SAMPLE_APP_REVIEWS_EMPTY_UNAVAILABLE_PAYLOAD,
    SAMPLE_APP_REVIEWS_SUCCESS_PAYLOAD,
    SAMPLE_APP_REVIEWS_TERMINAL_PAYLOAD,
    SAMPLE_STORE_APPDETAILS_SUCCESS_PAYLOAD,
    SAMPLE_STORE_APPDETAILS_UNAVAILABLE_PAYLOAD,
)


def test_parse_app_reviews_normalizes_fields() -> None:
    page = parse_app_reviews_response(SAMPLE_APP_REVIEWS_SUCCESS_PAYLOAD, app_id=1145360)

    assert len(page.reviews) == 2
    assert page.has_more is True
    assert page.cursor == "AoIIPwAAAZ3s0Z4D"
    assert page.total_reviews_in_query == 219200

    r1 = page.reviews[0]
    assert r1.steam_review_id == 120000001
    assert r1.language == "english"
    assert "masterpiece" in r1.review_text
    assert r1.voted_up is True
    assert r1.votes_up == 320
    assert r1.votes_funny == 14
    assert r1.weighted_vote_score == Decimal("0.965000000000000000")
    assert r1.comment_count == 5
    assert r1.steam_playtime_forever == 5400
    assert r1.steam_playtime_at_review == 3600
    assert r1.steam_playtime_last_two_weeks == 180
    assert r1.steam_purchase is True
    assert r1.received_for_free is False
    assert r1.written_during_early_access is False
    assert r1.steam_created_at == datetime(2020, 9, 17, 12, 0, tzinfo=UTC)

    # Privacy constraint: verify no author identity fields exist in the normalized model
    assert not hasattr(r1, "steamid")
    assert not hasattr(r1, "author")

    r2 = page.reviews[1]
    assert r2.steam_review_id == 120000002
    assert r2.voted_up is False
    assert r2.votes_up == 18
    assert r2.weighted_vote_score == Decimal("0.450000000000000000")


def test_parse_app_reviews_handles_cursor_loop_and_termination() -> None:
    # Current cursor matches returned cursor -> end of stream
    page = parse_app_reviews_response(
        SAMPLE_APP_REVIEWS_TERMINAL_PAYLOAD,
        app_id=1145360,
        current_cursor="AoIIPwAAAZ3s0Z4D",
    )
    assert len(page.reviews) == 0
    assert page.has_more is False


def test_parse_app_reviews_empty_unavailable() -> None:
    page = parse_app_reviews_response(
        SAMPLE_APP_REVIEWS_EMPTY_UNAVAILABLE_PAYLOAD,
        app_id=99999999,
    )
    assert len(page.reviews) == 0
    assert page.has_more is False
    assert page.cursor is None


def test_parse_app_reviews_skips_empty_text() -> None:
    payload = {
        "response": {
            "reviews": [
                {
                    "recommendationid": "111",
                    "review": "   \n\t  ",  # Whitespace only
                    "voted_up": True,
                },
                {
                    "recommendationid": "222",
                    "review": "Legitimate text review.",
                    "voted_up": True,
                },
            ],
            "cursor": "token123",
            "success": 1,
        }
    }
    page = parse_app_reviews_response(payload, app_id=1145360)
    assert len(page.reviews) == 1
    assert page.reviews[0].steam_review_id == 222


def test_parse_app_reviews_malformed_payload_raises() -> None:
    with pytest.raises(SteamMalformedResponseError):
        parse_app_reviews_response({"invalid_root": 123}, app_id=1145360)


def test_parse_store_appdetails_success() -> None:
    meta = parse_store_appdetails_response(SAMPLE_STORE_APPDETAILS_SUCCESS_PAYLOAD, app_id=1145360)

    assert meta.steam_app_id == 1145360
    assert meta.name == "Hades"
    assert "Defy the god of the dead" in (meta.short_description or "")
    assert meta.header_image_url is not None
    assert meta.website_url == "https://www.supergiantgames.com/games/hades/"
    assert meta.developers == ["Supergiant Games"]
    assert meta.publishers == ["Supergiant Games"]
    assert meta.genres == ["Action", "RPG", "Indie"]
    assert "Single-player" in meta.categories
    assert "Full controller support" in meta.categories
    assert meta.release_date == date(2020, 9, 17)
    assert meta.is_free is False


def test_parse_store_appdetails_unavailable() -> None:
    with pytest.raises(SteamGameUnavailableError) as exc_info:
        parse_store_appdetails_response(SAMPLE_STORE_APPDETAILS_UNAVAILABLE_PAYLOAD, app_id=99999999)

    assert exc_info.value.steam_app_id == 99999999
    assert exc_info.value.status_code == 404


def test_parse_store_appdetails_missing_key() -> None:
    with pytest.raises(SteamGameUnavailableError):
        parse_store_appdetails_response({}, app_id=12345)


def test_parse_steam_release_date_formats() -> None:
    assert parse_steam_release_date("17 Sep, 2020") == date(2020, 9, 17)
    assert parse_steam_release_date("Sep 17, 2020") == date(2020, 9, 17)
    assert parse_steam_release_date("17 September, 2020") == date(2020, 9, 17)
    assert parse_steam_release_date("2020-09-17") == date(2020, 9, 17)
    assert parse_steam_release_date("September 2020") == date(2020, 9, 1)
    assert parse_steam_release_date("Coming Soon") is None
    assert parse_steam_release_date("TBA") is None
    assert parse_steam_release_date("") is None

