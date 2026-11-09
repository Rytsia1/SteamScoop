import json

import httpx

from app.integrations.steam.client import SteamClient
from app.integrations.steam.schemas import SteamReviewRequestParams
from app.integrations.steam.transport import SteamTransport
from tests.fixtures.steam_fixtures import (
    SAMPLE_APP_REVIEWS_SUCCESS_PAYLOAD,
    SAMPLE_APP_REVIEWS_TERMINAL_PAYLOAD,
    SAMPLE_STORE_APPDETAILS_SUCCESS_PAYLOAD,
)


def test_client_get_game_metadata() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/appdetails"
        assert request.url.params["appids"] == "1145360"
        return httpx.Response(200, json=SAMPLE_STORE_APPDETAILS_SUCCESS_PAYLOAD)

    transport = SteamTransport(client=httpx.Client(transport=httpx.MockTransport(handler)))
    client = SteamClient(transport=transport)

    meta = client.get_game_metadata(1145360)
    assert meta.steam_app_id == 1145360
    assert meta.name == "Hades"
    assert "Supergiant Games" in meta.developers


def test_client_get_app_reviews() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "GetAppReviews" in request.url.path
        input_json_str = request.url.params["input_json"]
        parsed_input = json.loads(input_json_str)
        assert parsed_input["appid"] == 1145360
        assert parsed_input["num_per_page"] == 50
        assert parsed_input["filter"] == 1
        return httpx.Response(200, json=SAMPLE_APP_REVIEWS_SUCCESS_PAYLOAD)

    transport = SteamTransport(client=httpx.Client(transport=httpx.MockTransport(handler)))
    client = SteamClient(transport=transport)

    params = SteamReviewRequestParams(
        appid=1145360,
        num_per_page=50,
        filter=1,
    )
    page = client.get_app_reviews(params)
    assert len(page.reviews) == 2
    assert page.has_more is True
    assert page.cursor == "AoIIPwAAAZ3s0Z4D"


def test_client_iterate_recent_reviews_pagination() -> None:
    page_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal page_count
        page_count += 1
        input_json_str = request.url.params["input_json"]
        parsed = json.loads(input_json_str)

        if page_count == 1:
            assert parsed["cursor"] == "*"
            return httpx.Response(200, json=SAMPLE_APP_REVIEWS_SUCCESS_PAYLOAD)
        else:
            assert parsed["cursor"] == "AoIIPwAAAZ3s0Z4D"
            return httpx.Response(200, json=SAMPLE_APP_REVIEWS_TERMINAL_PAYLOAD)

    transport = SteamTransport(client=httpx.Client(transport=httpx.MockTransport(handler)))
    client = SteamClient(transport=transport)

    pages = list(client.iterate_recent_reviews(steam_app_id=1145360, max_pages=5))
    # Should fetch page 1 (with 2 reviews, cursor=AoIIPwAAAZ3s0Z4D) then page 2 (terminal), then stop
    assert len(pages) == 2
    assert len(pages[0].reviews) == 2
    assert pages[0].has_more is True
    assert len(pages[1].reviews) == 0
    assert pages[1].has_more is False


def test_client_iterate_updated_reviews() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        input_json_str = request.url.params["input_json"]
        parsed = json.loads(input_json_str)
        assert parsed["filter"] == 2  # Updated filter for incremental sync
        return httpx.Response(200, json=SAMPLE_APP_REVIEWS_SUCCESS_PAYLOAD)

    transport = SteamTransport(client=httpx.Client(transport=httpx.MockTransport(handler)))
    client = SteamClient(transport=transport)

    pages = list(client.iterate_updated_reviews(steam_app_id=1145360, max_pages=1))
    assert len(pages) == 1
    assert len(pages[0].reviews) == 2

