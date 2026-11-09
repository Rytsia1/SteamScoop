from typing import Any

# ==========================================
# Steam Reviews API Fixtures (GetAppReviews/v1)
# ==========================================

SAMPLE_APP_REVIEWS_SUCCESS_PAYLOAD: dict[str, Any] = {
    "response": {
        "reviews": [
            {
                "recommendationid": "120000001",
                "author": {
                    "steamid": "76561198000000001",
                    "num_games_owned": 250,
                    "num_reviews": 32,
                    "playtime_forever": 5400,
                    "playtime_last_two_weeks": 180,
                    "playtime_at_review": 3600,
                    "last_played": 1700000000,
                },
                "language": "english",
                "review": "A masterpiece of the roguelike genre. Combat is tight and responsive.",
                "timestamp_created": 1600344000,  # 2020-09-17 12:00:00 UTC
                "timestamp_updated": 1600350000,  # 2020-09-17 13:40:00 UTC
                "voted_up": True,
                "votes_up": 320,
                "votes_funny": 14,
                "weighted_vote_score": "0.965000000000000000",
                "comment_count": 5,
                "steam_purchase": True,
                "received_for_free": False,
                "written_during_early_access": False,
                "primarily_steam_deck": False,
            },
            {
                "recommendationid": "120000002",
                "author": {
                    "steamid": "76561198000000002",
                    "num_games_owned": 40,
                    "num_reviews": 3,
                    "playtime_forever": 240,
                    "playtime_last_two_weeks": 0,
                    "playtime_at_review": 240,
                    "last_played": 1601000000,
                },
                "language": "english",
                "review": "Too repetitive after the first few hours. Not my cup of tea.",
                "timestamp_created": 1600500000,
                "timestamp_updated": 1600500000,
                "voted_up": False,
                "votes_up": 18,
                "votes_funny": 2,
                "weighted_vote_score": "0.450000000000000000",
                "comment_count": 1,
                "steam_purchase": True,
                "received_for_free": False,
                "written_during_early_access": False,
                "primarily_steam_deck": False,
            },
        ],
        "cursor": "AoIIPwAAAZ3s0Z4D",
        "query_summary": {
            "num_reviews": 2,
            "review_score": 9,
            "review_score_desc": "Overwhelmingly Positive",
            "total_positive": 215000,
            "total_negative": 4200,
            "total_reviews": 219200,
        },
        "success": 1,
    }
}

SAMPLE_APP_REVIEWS_TERMINAL_PAYLOAD: dict[str, Any] = {
    "response": {
        "reviews": [],
        "cursor": "AoIIPwAAAZ3s0Z4D",  # Repeated cursor indicates end of stream
        "query_summary": {
            "num_reviews": 0,
            "total_reviews": 219200,
        },
        "success": 1,
    }
}

SAMPLE_APP_REVIEWS_EMPTY_UNAVAILABLE_PAYLOAD: dict[str, Any] = {
    "response": {
        "reviews": [],
        "cursor": "*",
        "query_summary": {
            "num_reviews": 0,
            "total_reviews": 0,
        },
        "success": 2,
    }
}

# ==========================================
# Steam Store Metadata Fixtures (appdetails)
# ==========================================

SAMPLE_STORE_APPDETAILS_SUCCESS_PAYLOAD: dict[str, Any] = {
    "1145360": {
        "success": True,
        "data": {
            "type": "game",
            "name": "Hades",
            "steam_appid": 1145360,
            "required_age": 0,
            "is_free": False,
            "short_description": "Defy the god of the dead as you hack and slash out of the Underworld.",
            "header_image": "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/1145360/header.jpg",
            "website": "https://www.supergiantgames.com/games/hades/",
            "developers": ["Supergiant Games"],
            "publishers": ["Supergiant Games"],
            "genres": [
                {"id": "1", "description": "Action"},
                {"id": "3", "description": "RPG"},
                {"id": "23", "description": "Indie"},
            ],
            "categories": [
                {"id": 2, "description": "Single-player"},
                {"id": 28, "description": "Full controller support"},
                {"id": 23, "description": "Steam Cloud"},
            ],
            "release_date": {
                "coming_soon": False,
                "date": "17 Sep, 2020",
            },
        },
    }
}

SAMPLE_STORE_APPDETAILS_UNAVAILABLE_PAYLOAD: dict[str, Any] = {
    "99999999": {
        "success": False,
    }
}

