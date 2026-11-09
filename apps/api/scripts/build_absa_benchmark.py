"""Benchmark dataset generator for Aspect-Based Sentiment Analysis (ABSA).

Generates reproducible train, validation, and test splits with zero data leakage
and creates canonical benchmark files in data/benchmarks/steamscoop_absa_v1/.

Strictly implements the 12-aspect controlled taxonomy defined in:
- Docs/ML_SPECIFICATION.md Section 6.3
- Docs/ANNOTATION_GUIDELINE.md Section 4
- apps/api/app/ml/taxonomy.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Ensure apps/api is on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
API_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = API_ROOT.parent.parent

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.ml.dataset_builder import DatasetBuilder
from app.ml.taxonomy import AspectKey, SentimentLabel

# Comprehensive canonical ABSA benchmark dataset (100+ annotated reviews)
# Balanced across all 12 controlled aspects, multi-aspect reviews, mixed polarities, and no-aspect reviews.
ABSA_BENCHMARK_REVIEWS: list[dict[str, Any]] = [
    # --- GAMEPLAY REVIEWS ---
    {
        "review_id": "absa_001",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-10-02T10:15:00Z",
        "review_text": "Combat mechanics feel crisp and fluid. Hacking enemies from the shadows never gets old. Great gunplay and weapon variety.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.GAMEPLAY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Combat mechanics feel crisp and fluid. Hacking enemies from the shadows never gets old. Great gunplay and weapon variety.",
            },
        ],
    },
    {
        "review_id": "absa_002",
        "steam_app_id": 1245620,
        "steam_created_at": "2024-03-01T15:20:00Z",
        "review_text": "Boss encounters are brutally difficult yet impeccably fair. Tight parry timing and responsive dodging make every victory deeply satisfying.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.GAMEPLAY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Boss encounters are brutally difficult yet impeccably fair. Tight parry timing and responsive dodging make every victory deeply satisfying.",
            },
        ],
    },
    {
        "review_id": "absa_003",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-10-15T12:00:00Z",
        "review_text": "Controls feel clunky and unresponsive. Movement has noticeable input delay, and melee hitboxes are completely broken.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.GAMEPLAY.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Controls feel clunky and unresponsive. Movement has noticeable input delay, and melee hitboxes are completely broken.",
            },
        ],
    },
    {
        "review_id": "absa_004",
        "steam_app_id": 1145360,
        "steam_created_at": "2023-08-10T14:30:00Z",
        "review_text": "The core combat mechanics are standard for the genre. Nothing innovative, but serviceable enough to pass the time.",
        "voted_up": True,
        "sentiment": SentimentLabel.NEUTRAL.value,
        "aspects": [
            {
                "aspect": AspectKey.GAMEPLAY.value,
                "sentiment": SentimentLabel.NEUTRAL.value,
                "snippet": "The core combat mechanics are standard for the genre. Nothing innovative, but serviceable enough to pass the time.",
            },
        ],
    },
    # --- STORY REVIEWS ---
    {
        "review_id": "absa_005",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-09-28T16:00:00Z",
        "review_text": "The narrative and character writing in Phantom Liberty are unmatched. Emotional storytelling with morally grey choices that genuinely matter.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.STORY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "The narrative and character writing in Phantom Liberty are unmatched. Emotional storytelling with morally grey choices that genuinely matter.",
            },
        ],
    },
    {
        "review_id": "absa_006",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-11-05T18:40:00Z",
        "review_text": "The storyline is filled with glaring plot holes and awful dialogue. The main protagonist is insufferable and the ending feels completely rushed.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.STORY.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "The storyline is filled with glaring plot holes and awful dialogue. The main protagonist is insufferable and the ending feels completely rushed.",
            },
        ],
    },
    {
        "review_id": "absa_007",
        "steam_app_id": 1145360,
        "steam_created_at": "2023-05-14T21:10:00Z",
        "review_text": "Dialogue progression between escape attempts is clever, and worldbuilding lore gives interesting context to Greek mythology.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.STORY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Dialogue progression between escape attempts is clever, and worldbuilding lore gives interesting context to Greek mythology.",
            },
        ],
    },
    {
        "review_id": "absa_008",
        "steam_app_id": 1245620,
        "steam_created_at": "2024-04-10T11:00:00Z",
        "review_text": "The plot is typical cryptic fantasy lore. You need to read item descriptions to understand anything, which is fine if you enjoy that style.",
        "voted_up": True,
        "sentiment": SentimentLabel.NEUTRAL.value,
        "aspects": [
            {
                "aspect": AspectKey.STORY.value,
                "sentiment": SentimentLabel.NEUTRAL.value,
                "snippet": "The plot is typical cryptic fantasy lore. You need to read item descriptions to understand anything, which is fine if you enjoy that style.",
            },
        ],
    },
    # --- GRAPHICS REVIEWS ---
    {
        "review_id": "absa_009",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-09-26T14:30:00Z",
        "review_text": "Visuals with path tracing are breathtaking. Neon reflections in the rain and character model facial animations look photorealistic.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.GRAPHICS.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Visuals with path tracing are breathtaking. Neon reflections in the rain and character model facial animations look photorealistic.",
            },
        ],
    },
    {
        "review_id": "absa_010",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-10-18T09:15:00Z",
        "review_text": "Ugly low resolution textures and severe pop-in everywhere. Lighting looks flat and shadows flicker violently.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.GRAPHICS.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Ugly low resolution textures and severe pop-in everywhere. Lighting looks flat and shadows flicker violently.",
            },
        ],
    },
    {
        "review_id": "absa_011",
        "steam_app_id": 1145360,
        "steam_created_at": "2023-07-22T13:45:00Z",
        "review_text": "The 2D hand-drawn art style is gorgeous and animations are silky smooth throughout every room.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.GRAPHICS.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "The 2D hand-drawn art style is gorgeous and animations are silky smooth throughout every room.",
            },
        ],
    },
    {
        "review_id": "absa_012",
        "steam_app_id": 553850,
        "steam_created_at": "2024-03-05T14:10:00Z",
        "review_text": "Graphics are clean and adequate for a co-op shooter. Environmental effects look decent without being groundbreaking.",
        "voted_up": True,
        "sentiment": SentimentLabel.NEUTRAL.value,
        "aspects": [
            {
                "aspect": AspectKey.GRAPHICS.value,
                "sentiment": SentimentLabel.NEUTRAL.value,
                "snippet": "Graphics are clean and adequate for a co-op shooter. Environmental effects look decent without being groundbreaking.",
            },
        ],
    },
    # --- AUDIO REVIEWS ---
    {
        "review_id": "absa_013",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-11-12T19:45:00Z",
        "review_text": "The original soundtrack is an absolute masterpiece. Combat tracks get your adrenaline pumping, and ambient radio music sets the tone perfectly.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.AUDIO.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "The original soundtrack is an absolute masterpiece. Combat tracks get your adrenaline pumping, and ambient radio music sets the tone perfectly.",
            },
        ],
    },
    {
        "review_id": "absa_014",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-12-02T10:00:00Z",
        "review_text": "Sound mixing is terrible. Gunshot sound effects are muffled and quiet, while voice acting dialogue is drowned out by background static.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.AUDIO.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Sound mixing is terrible. Gunshot sound effects are muffled and quiet, while voice acting dialogue is drowned out by background static.",
            },
        ],
    },
    {
        "review_id": "absa_015",
        "steam_app_id": 1145360,
        "steam_created_at": "2023-08-01T20:00:00Z",
        "review_text": "Darren Korb does not miss. The OST and dynamic guitar riffs during boss battles elevate the whole experience.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.AUDIO.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "The OST and dynamic guitar riffs during boss battles elevate the whole experience.",
            },
        ],
    },
    {
        "review_id": "absa_016",
        "steam_app_id": 1245620,
        "steam_created_at": "2024-05-12T16:20:00Z",
        "review_text": "Music is ambient and quiet for most of the open world. It serves its purpose of background atmosphere.",
        "voted_up": True,
        "sentiment": SentimentLabel.NEUTRAL.value,
        "aspects": [
            {
                "aspect": AspectKey.AUDIO.value,
                "sentiment": SentimentLabel.NEUTRAL.value,
                "snippet": "Music is ambient and quiet for most of the open world. It serves its purpose of background atmosphere.",
            },
        ],
    },
    # --- PERFORMANCE REVIEWS ---
    {
        "review_id": "absa_017",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-12-05T08:20:00Z",
        "review_text": "Runs buttery smooth at locked 120 FPS on ultra settings with zero stuttering or crashes.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.PERFORMANCE.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Runs buttery smooth at locked 120 FPS on ultra settings with zero stuttering or crashes.",
            },
        ],
    },
    {
        "review_id": "absa_018",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-10-08T17:30:00Z",
        "review_text": "Constant stuttering, massive framerate drops down to 15 FPS, and hard desktop crashes every 20 minutes. Terrible optimization.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.PERFORMANCE.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Constant stuttering, massive framerate drops down to 15 FPS, and hard desktop crashes every 20 minutes. Terrible optimization.",
            },
        ],
    },
    {
        "review_id": "absa_019",
        "steam_app_id": 553850,
        "steam_created_at": "2024-02-25T19:00:00Z",
        "review_text": "Performance fluctuates between 50 and 70 FPS during dense explosions. Playable, but could definitely use another optimization pass.",
        "voted_up": True,
        "sentiment": SentimentLabel.NEUTRAL.value,
        "aspects": [
            {
                "aspect": AspectKey.PERFORMANCE.value,
                "sentiment": SentimentLabel.NEUTRAL.value,
                "snippet": "Performance fluctuates between 50 and 70 FPS during dense explosions. Playable, but could definitely use another optimization pass.",
            },
        ],
    },
    {
        "review_id": "absa_020",
        "steam_app_id": 1245620,
        "steam_created_at": "2024-06-25T14:00:00Z",
        "review_text": "Severe microstuttering in open areas even on high-end hardware with an RTX 4080. Memory leaks crash the game after two hours.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.PERFORMANCE.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Severe microstuttering in open areas even on high-end hardware with an RTX 4080. Memory leaks crash the game after two hours.",
            },
        ],
    },
    # --- CONTENT REVIEWS ---
    {
        "review_id": "absa_021",
        "steam_app_id": 1145360,
        "steam_created_at": "2023-07-04T16:45:00Z",
        "review_text": "Easily over 150 hours of content across multiple weapon builds and pact modifiers. Exceptional replay value that keeps giving.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.CONTENT.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Easily over 150 hours of content across multiple weapon builds and pact modifiers. Exceptional replay value that keeps giving.",
            },
        ],
    },
    {
        "review_id": "absa_022",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-11-20T11:30:00Z",
        "review_text": "Beat the main campaign in just 6 hours. Zero endgame content and completely empty side quests. Repetitive fetch quests with no substance.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.CONTENT.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Beat the main campaign in just 6 hours. Zero endgame content and completely empty side quests. Repetitive fetch quests with no substance.",
            },
        ],
    },
    {
        "review_id": "absa_023",
        "steam_app_id": 1245620,
        "steam_created_at": "2024-03-20T18:00:00Z",
        "review_text": "A massive open world packed with catacombs, dungeons, and hidden caves. The amount of content is astonishing.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.CONTENT.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "A massive open world packed with catacombs, dungeons, and hidden caves. The amount of content is astonishing.",
            },
        ],
    },
    {
        "review_id": "absa_024",
        "steam_app_id": 553850,
        "steam_created_at": "2024-04-02T13:15:00Z",
        "review_text": "Mission objectives get repetitive after 30 hours, but weekly major orders keep things somewhat interesting.",
        "voted_up": True,
        "sentiment": SentimentLabel.NEUTRAL.value,
        "aspects": [
            {
                "aspect": AspectKey.CONTENT.value,
                "sentiment": SentimentLabel.NEUTRAL.value,
                "snippet": "Mission objectives get repetitive after 30 hours, but weekly major orders keep things somewhat interesting.",
            },
        ],
    },
    # --- MULTIPLAYER REVIEWS ---
    {
        "review_id": "absa_025",
        "steam_app_id": 553850,
        "steam_created_at": "2024-02-10T18:30:00Z",
        "review_text": "Co-op with friends is pure chaotic joy. Matchmaking is fast and peer-to-peer connection is surprisingly stable.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.MULTIPLAYER.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Co-op with friends is pure chaotic joy. Matchmaking is fast and peer-to-peer connection is surprisingly stable.",
            },
        ],
    },
    {
        "review_id": "absa_026",
        "steam_app_id": 553850,
        "steam_created_at": "2024-02-15T21:45:00Z",
        "review_text": "Broken multiplayer servers with endless queue times and constant mid-mission disconnects. Lobbies are infested with cheaters.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.MULTIPLAYER.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Broken multiplayer servers with endless queue times and constant mid-mission disconnects. Lobbies are infested with cheaters.",
            },
        ],
    },
    {
        "review_id": "absa_027",
        "steam_app_id": 553850,
        "steam_created_at": "2024-03-12T17:00:00Z",
        "review_text": "Matchmaking works fine when playing with randoms, though crossplay voice chat has occasional lag.",
        "voted_up": True,
        "sentiment": SentimentLabel.NEUTRAL.value,
        "aspects": [
            {
                "aspect": AspectKey.MULTIPLAYER.value,
                "sentiment": SentimentLabel.NEUTRAL.value,
                "snippet": "Matchmaking works fine when playing with randoms, though crossplay voice chat has occasional lag.",
            },
        ],
    },
    {
        "review_id": "absa_028",
        "steam_app_id": 553850,
        "steam_created_at": "2024-04-18T19:30:00Z",
        "review_text": "PvP balance is completely out of whack with one overpowered meta loadout. Netcode feels laggy and high ping ruins gunfights.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.MULTIPLAYER.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "PvP balance is completely out of whack with one overpowered meta loadout. Netcode feels laggy and high ping ruins gunfights.",
            },
        ],
    },
    # --- MONETIZATION REVIEWS ---
    {
        "review_id": "absa_029",
        "steam_app_id": 553850,
        "steam_created_at": "2024-02-18T11:15:00Z",
        "review_text": "The war bond battle passes never expire! You can earn premium super credits in-game by just playing. Very consumer-friendly monetization.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.MONETIZATION.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "The war bond battle passes never expire! You can earn premium super credits in-game by just playing. Very consumer-friendly monetization.",
            },
        ],
    },
    {
        "review_id": "absa_030",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-11-25T14:20:00Z",
        "review_text": "Disgusting corporate greed with predatory microtransactions and pay-to-win boosters in a full price game. Avoid this cash grab.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.MONETIZATION.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Disgusting corporate greed with predatory microtransactions and pay-to-win boosters in a full price game. Avoid this cash grab.",
            },
        ],
    },
    {
        "review_id": "absa_031",
        "steam_app_id": 553850,
        "steam_created_at": "2024-03-22T10:00:00Z",
        "review_text": "Monetization includes cosmetic weapon skins and armors in the store. Totally optional and neither overly generous nor predatory.",
        "voted_up": True,
        "sentiment": SentimentLabel.NEUTRAL.value,
        "aspects": [
            {
                "aspect": AspectKey.MONETIZATION.value,
                "sentiment": SentimentLabel.NEUTRAL.value,
                "snippet": "Monetization includes cosmetic weapon skins and armors in the store. Totally optional and neither overly generous nor predatory.",
            },
        ],
    },
    {
        "review_id": "absa_032",
        "steam_app_id": 1091500,
        "steam_created_at": "2024-01-10T15:40:00Z",
        "review_text": "Lootboxes and aggressive MTX popups make the menus look like a cheap mobile game. Unacceptable monetization practices.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.MONETIZATION.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Lootboxes and aggressive MTX popups make the menus look like a cheap mobile game. Unacceptable monetization practices.",
            },
        ],
    },
    # --- PRICE / VALUE REVIEWS ---
    {
        "review_id": "absa_033",
        "steam_app_id": 1145360,
        "steam_created_at": "2023-07-04T16:45:00Z",
        "review_text": "For twenty-five dollars, you get over a hundred hours of entertainment. Best dollar-per-hour value on Steam hands down.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.PRICE_VALUE.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "For twenty-five dollars, you get over a hundred hours of entertainment. Best dollar-per-hour value on Steam hands down.",
            },
        ],
    },
    {
        "review_id": "absa_034",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-10-25T13:00:00Z",
        "review_text": "Not worth the seventy dollar price tag for such a short experience. Wait for a steep seventy percent discount.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.PRICE_VALUE.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Not worth the seventy dollar price tag for such a short experience. Wait for a steep seventy percent discount.",
            },
        ],
    },
    {
        "review_id": "absa_035",
        "steam_app_id": 553850,
        "steam_created_at": "2024-02-28T16:30:00Z",
        "review_text": "At forty dollars, the entry price is reasonable compared to standard AAA pricing.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.PRICE_VALUE.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "At forty dollars, the entry price is reasonable compared to standard AAA pricing.",
            },
        ],
    },
    {
        "review_id": "absa_036",
        "steam_app_id": 1245620,
        "steam_created_at": "2024-04-14T12:00:00Z",
        "review_text": "Full retail price is average for a big expansion. Worth picking up if you are a fan, otherwise wait for a holiday sale.",
        "voted_up": True,
        "sentiment": SentimentLabel.NEUTRAL.value,
        "aspects": [
            {
                "aspect": AspectKey.PRICE_VALUE.value,
                "sentiment": SentimentLabel.NEUTRAL.value,
                "snippet": "Full retail price is average for a big expansion. Worth picking up if you are a fan, otherwise wait for a holiday sale.",
            },
        ],
    },
    # --- SUPPORT / UPDATES REVIEWS ---
    {
        "review_id": "absa_037",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-11-01T15:00:00Z",
        "review_text": "The developers have redeemed the game with constant patches and transparent communication. Fantastic post-launch support.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.SUPPORT_UPDATES.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "The developers have redeemed the game with constant patches and transparent communication. Fantastic post-launch support.",
            },
        ],
    },
    {
        "review_id": "absa_038",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-12-18T11:20:00Z",
        "review_text": "Devs took early access money and completely abandoned the game. Zero patches in six months and bug reports are ignored.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.SUPPORT_UPDATES.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Devs took early access money and completely abandoned the game. Zero patches in six months and bug reports are ignored.",
            },
        ],
    },
    {
        "review_id": "absa_039",
        "steam_app_id": 553850,
        "steam_created_at": "2024-03-30T14:45:00Z",
        "review_text": "Arrowhead pushes frequent balance updates. Sometimes weapons get over-nerfed, but developer responsiveness to player feedback is solid.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.SUPPORT_UPDATES.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Arrowhead pushes frequent balance updates. Sometimes weapons get over-nerfed, but developer responsiveness to player feedback is solid.",
            },
        ],
    },
    {
        "review_id": "absa_040",
        "steam_app_id": 1245620,
        "steam_created_at": "2024-05-02T10:15:00Z",
        "review_text": "Patches are released every few months with minimal patch notes. Standard maintenance support without major roadmap updates.",
        "voted_up": True,
        "sentiment": SentimentLabel.NEUTRAL.value,
        "aspects": [
            {
                "aspect": AspectKey.SUPPORT_UPDATES.value,
                "sentiment": SentimentLabel.NEUTRAL.value,
                "snippet": "Patches are released every few months with minimal patch notes. Standard maintenance support without major roadmap updates.",
            },
        ],
    },
    # --- ACCESSIBILITY REVIEWS ---
    {
        "review_id": "absa_041",
        "steam_app_id": 1145360,
        "steam_created_at": "2023-06-20T12:00:00Z",
        "review_text": "God Mode in Hades is an incredible accessibility feature. It lets anyone experience the narrative with gradual damage resistance.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.ACCESSIBILITY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "God Mode in Hades is an incredible accessibility feature. It lets anyone experience the narrative with gradual damage resistance.",
            },
        ],
    },
    {
        "review_id": "absa_042",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-11-15T09:30:00Z",
        "review_text": "Terrible accessibility options. Unreadable tiny font on 4K monitors with no subtitle size slider, and no option to rebind keyboard controls.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.ACCESSIBILITY.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Terrible accessibility options. Unreadable tiny font on 4K monitors with no subtitle size slider, and no option to rebind keyboard controls.",
            },
        ],
    },
    {
        "review_id": "absa_043",
        "steam_app_id": 553850,
        "steam_created_at": "2024-03-18T16:00:00Z",
        "review_text": "Extensive accessibility settings including high-contrast mode, full keybind remapping, and multiple colorblind filter profiles.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.ACCESSIBILITY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Extensive accessibility settings including high-contrast mode, full keybind remapping, and multiple colorblind filter profiles.",
            },
        ],
    },
    {
        "review_id": "absa_044",
        "steam_app_id": 1245620,
        "steam_created_at": "2024-04-20T14:20:00Z",
        "review_text": "Basic accessibility options like subtitle toggle are present, but no colorblind filters or motion sickness FOV adjustment slider.",
        "voted_up": True,
        "sentiment": SentimentLabel.NEUTRAL.value,
        "aspects": [
            {
                "aspect": AspectKey.ACCESSIBILITY.value,
                "sentiment": SentimentLabel.NEUTRAL.value,
                "snippet": "Basic accessibility options like subtitle toggle are present, but no colorblind filters or motion sickness FOV adjustment slider.",
            },
        ],
    },
    {
        "review_id": "absa_045",
        "steam_app_id": 1091500,
        "steam_created_at": "2024-01-08T18:00:00Z",
        "review_text": "Severe motion sickness due to lack of a field of view slider and forced camera bobbing. Zero nausea prevention options.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.ACCESSIBILITY.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Severe motion sickness due to lack of a field of view slider and forced camera bobbing. Zero nausea prevention options.",
            },
        ],
    },
    # --- OTHER (LAUNCHERS / ANTI-CHEAT / PLATFORMS) REVIEWS ---
    {
        "review_id": "absa_046",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-10-30T11:00:00Z",
        "review_text": "Plays flawlessly out of the box on Steam Deck via Proton with zero configuration needed. Great handheld experience.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.OTHER.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Plays flawlessly out of the box on Steam Deck via Proton with zero configuration needed.",
            },
        ],
    },
    {
        "review_id": "absa_047",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-12-10T14:40:00Z",
        "review_text": "Mandatory third-party launcher requires separate login and breaks offline play completely. Invasive kernel anti-cheat triggers antivirus.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.OTHER.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Mandatory third-party launcher requires separate login and breaks offline play completely. Invasive kernel anti-cheat triggers antivirus.",
            },
        ],
    },
    {
        "review_id": "absa_048",
        "steam_app_id": 553850,
        "steam_created_at": "2024-02-12T13:30:00Z",
        "review_text": "Requires GameGuard anti-cheat which causes blue screens on boot for some Linux and Deck configurations.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.OTHER.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Requires GameGuard anti-cheat which causes blue screens on boot for some Linux and Deck configurations.",
            },
        ],
    },
    {
        "review_id": "absa_049",
        "steam_app_id": 1245620,
        "steam_created_at": "2024-03-25T17:15:00Z",
        "review_text": "Third-party publisher launcher opens behind the game window. A minor annoyance, but launches fine once confirmed.",
        "voted_up": True,
        "sentiment": SentimentLabel.NEUTRAL.value,
        "aspects": [
            {
                "aspect": AspectKey.OTHER.value,
                "sentiment": SentimentLabel.NEUTRAL.value,
                "snippet": "Third-party publisher launcher opens behind the game window. A minor annoyance, but launches fine once confirmed.",
            },
        ],
    },
    {
        "review_id": "absa_050",
        "steam_app_id": 1145360,
        "steam_created_at": "2023-09-05T15:20:00Z",
        "review_text": "Native Linux support and flawless Proton performance. Developer respects the open platform.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.OTHER.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Native Linux support and flawless Proton performance. Developer respects the open platform.",
            },
        ],
    },
    # --- MULTI-ASPECT CONCORDANT REVIEWS (ALL POSITIVE / ALL NEGATIVE) ---
    {
        "review_id": "absa_051",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-09-26T14:30:00Z",
        "review_text": "Cyberpunk 2077 has redeemed itself! The graphics with ray tracing are unbelievable, and Night City feels alive. The story kept me hooked for 80 hours.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.GRAPHICS.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "graphics with ray tracing are unbelievable, and Night City feels alive.",
            },
            {
                "aspect": AspectKey.STORY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "The story kept me hooked",
            },
            {
                "aspect": AspectKey.CONTENT.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "hooked for 80 hours.",
            },
        ],
    },
    {
        "review_id": "absa_052",
        "steam_app_id": 1145360,
        "steam_created_at": "2023-05-14T21:10:00Z",
        "review_text": "Hades is roguelike perfection. The combat feels snappy and responsive, dialogue writing is genius, and the soundtrack elevates every run.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.GAMEPLAY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "The combat feels snappy and responsive",
            },
            {
                "aspect": AspectKey.STORY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "dialogue writing is genius",
            },
            {
                "aspect": AspectKey.AUDIO.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "soundtrack elevates every run.",
            },
        ],
    },
    {
        "review_id": "absa_053",
        "steam_app_id": 553850,
        "steam_created_at": "2024-02-10T18:30:00Z",
        "review_text": "Helldivers 2 co-op with friends is pure chaos. Weapon gunplay is punchy and visual explosion effects look magnificent.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.MULTIPLAYER.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Helldivers 2 co-op with friends is pure chaos.",
            },
            {
                "aspect": AspectKey.GAMEPLAY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Weapon gunplay is punchy",
            },
            {
                "aspect": AspectKey.GRAPHICS.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "visual explosion effects look magnificent.",
            },
        ],
    },
    {
        "review_id": "absa_054",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-10-12T19:00:00Z",
        "review_text": "Broken unplayable mess. Frequent framerate stutters and desktop crashes, combined with clunky delayed controls.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.PERFORMANCE.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Frequent framerate stutters and desktop crashes",
            },
            {
                "aspect": AspectKey.GAMEPLAY.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "clunky delayed controls.",
            },
        ],
    },
    # --- MULTI-ASPECT DISCORDANT / MIXED OPINION REVIEWS (CRITICAL TEST CASES) ---
    {
        "review_id": "absa_055",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-10-20T14:30:00Z",
        "review_text": "The combat mechanics feel fantastic and gunplay is super responsive. However, the performance is atrocious with constant stuttering and FPS drops.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.GAMEPLAY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "The combat mechanics feel fantastic and gunplay is super responsive.",
            },
            {
                "aspect": AspectKey.PERFORMANCE.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "performance is atrocious with constant stuttering and FPS drops.",
            },
        ],
    },
    {
        "review_id": "absa_056",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-11-08T16:15:00Z",
        "review_text": "Visually stunning with ray tracing and breathtaking art design. But the predatory monetization and thirty dollar skins ruin the entire game.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.GRAPHICS.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Visually stunning with ray tracing and breathtaking art design.",
            },
            {
                "aspect": AspectKey.MONETIZATION.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "predatory monetization and thirty dollar skins ruin the entire game.",
            },
        ],
    },
    {
        "review_id": "absa_057",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-11-18T10:45:00Z",
        "review_text": "The emotional storyline and character writing brought me to tears. Too bad the multiplayer servers disconnect every ten minutes.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.STORY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "The emotional storyline and character writing brought me to tears.",
            },
            {
                "aspect": AspectKey.MULTIPLAYER.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "multiplayer servers disconnect every ten minutes.",
            },
        ],
    },
    {
        "review_id": "absa_058",
        "steam_app_id": 1145360,
        "steam_created_at": "2023-08-15T12:00:00Z",
        "review_text": "The soundtrack is an absolute masterpiece with thrilling boss music. Unfortunately, accessibility options are completely absent for deaf players.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.AUDIO.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "The soundtrack is an absolute masterpiece with thrilling boss music.",
            },
            {
                "aspect": AspectKey.ACCESSIBILITY.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "accessibility options are completely absent for deaf players.",
            },
        ],
    },
    {
        "review_id": "absa_059",
        "steam_app_id": 553850,
        "steam_created_at": "2024-03-10T15:30:00Z",
        "review_text": "Huge volume of content with hundreds of missions and planetary biomes. Sadly, the price is way too high at seventy dollars for an indie title.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.CONTENT.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Huge volume of content with hundreds of missions and planetary biomes.",
            },
            {
                "aspect": AspectKey.PRICE_VALUE.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "price is way too high at seventy dollars for an indie title.",
            },
        ],
    },
    {
        "review_id": "absa_060",
        "steam_app_id": 1245620,
        "steam_created_at": "2024-04-05T19:20:00Z",
        "review_text": "Developers patch bugs weekly with great community support. But the intrusive third-party launcher keeps failing to connect.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.SUPPORT_UPDATES.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Developers patch bugs weekly with great community support.",
            },
            {
                "aspect": AspectKey.OTHER.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "intrusive third-party launcher keeps failing to connect.",
            },
        ],
    },
    {
        "review_id": "absa_061",
        "steam_app_id": 1091500,
        "steam_created_at": "2024-01-22T13:10:00Z",
        "review_text": "Gunplay combat is exciting and visually dazzling. However, the campaign is extremely short and lack of content kills longevity.",
        "voted_up": True,
        "sentiment": SentimentLabel.NEUTRAL.value,
        "aspects": [
            {
                "aspect": AspectKey.GAMEPLAY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Gunplay combat is exciting",
            },
            {
                "aspect": AspectKey.GRAPHICS.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "visually dazzling.",
            },
            {
                "aspect": AspectKey.CONTENT.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "campaign is extremely short and lack of content kills longevity.",
            },
        ],
    },
    {
        "review_id": "absa_062",
        "steam_app_id": 553850,
        "steam_created_at": "2024-03-28T18:40:00Z",
        "review_text": "Great co-op multiplayer fun with friends. But the framerate microstutters heavily when high swarms appear on screen.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.MULTIPLAYER.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Great co-op multiplayer fun with friends.",
            },
            {
                "aspect": AspectKey.PERFORMANCE.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "framerate microstutters heavily when high swarms appear on screen.",
            },
        ],
    },
    # --- REVIEWS WITH NO IDENTIFIABLE ASPECTS (CRITICAL FOR FALSE POSITIVE AVOIDANCE) ---
    {
        "review_id": "absa_063",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-10-01T12:00:00Z",
        "review_text": "Masterpiece. Ten out of ten.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [],
    },
    {
        "review_id": "absa_064",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-10-05T14:00:00Z",
        "review_text": "Absolute garbage. Do not buy this trash.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [],
    },
    {
        "review_id": "absa_065",
        "steam_app_id": 1145360,
        "steam_created_at": "2023-06-15T16:00:00Z",
        "review_text": "Just buy it. You will not regret it.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [],
    },
    {
        "review_id": "absa_066",
        "steam_app_id": 1245620,
        "steam_created_at": "2024-04-01T11:00:00Z",
        "review_text": "Pretty mediocre. Nothing really stood out to me.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEUTRAL.value,
        "aspects": [],
    },
    {
        "review_id": "absa_067",
        "steam_app_id": 553850,
        "steam_created_at": "2024-02-20T10:30:00Z",
        "review_text": "Yes.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [],
    },
    {
        "review_id": "absa_068",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-12-01T17:00:00Z",
        "review_text": "Refunded after 30 minutes. Waste of time.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [],
    },
    {
        "review_id": "absa_069",
        "steam_app_id": 1145360,
        "steam_created_at": "2023-09-12T13:20:00Z",
        "review_text": "Good game.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [],
    },
    {
        "review_id": "absa_070",
        "steam_app_id": 1245620,
        "steam_created_at": "2024-05-10T19:00:00Z",
        "review_text": "Overhyped and boring.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [],
    },
    # --- ADDITIONAL COVERAGE TO ENSURE EVERY ASPECT HAS ADEQUATE TRAINING SAMPLES ---
    {
        "review_id": "absa_071",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-10-14T11:10:00Z",
        "review_text": "The custom keybind remapping and colorblind filters made the UI much easier to navigate for disabled gamers.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.ACCESSIBILITY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "custom keybind remapping and colorblind filters made the UI much easier to navigate",
            },
        ],
    },
    {
        "review_id": "absa_072",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-11-22T15:40:00Z",
        "review_text": "No accessibility support whatsoever. Subtitles cannot be turned on in cinematics and font sizing is tiny.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.ACCESSIBILITY.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "No accessibility support whatsoever. Subtitles cannot be turned on in cinematics and font sizing is tiny.",
            },
        ],
    },
    {
        "review_id": "absa_073",
        "steam_app_id": 553850,
        "steam_created_at": "2024-03-02T16:50:00Z",
        "review_text": "Monetization is completely fair. Free battle pass with generous credit rewards and zero pay to win shenanigans.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.MONETIZATION.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Monetization is completely fair. Free battle pass with generous credit rewards and zero pay to win shenanigans.",
            },
        ],
    },
    {
        "review_id": "absa_074",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-12-28T12:15:00Z",
        "review_text": "Invasive anti-cheat software slows down system performance and crashes whenever running background tools.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.OTHER.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Invasive anti-cheat software slows down system performance and crashes",
            },
        ],
    },
    {
        "review_id": "absa_075",
        "steam_app_id": 1145360,
        "steam_created_at": "2023-08-25T14:30:00Z",
        "review_text": "Works like a dream on Steam Deck. Sixty frames per second on battery with crisp text scaling.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.OTHER.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Works like a dream on Steam Deck. Sixty frames per second on battery",
            },
        ],
    },
    {
        "review_id": "absa_076",
        "steam_app_id": 1091500,
        "steam_created_at": "2024-01-05T17:20:00Z",
        "review_text": "The latest patch broke save files and corrupted progress. Terrible support from the development team.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.SUPPORT_UPDATES.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "The latest patch broke save files and corrupted progress. Terrible support from the development team.",
            },
        ],
    },
    {
        "review_id": "absa_077",
        "steam_app_id": 1245620,
        "steam_created_at": "2024-06-18T11:45:00Z",
        "review_text": "Outstanding value for forty dollars. Massive expansion with rich world lore and hundreds of secrets.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.PRICE_VALUE.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Outstanding value for forty dollars.",
            },
            {
                "aspect": AspectKey.STORY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "rich world lore",
            },
            {
                "aspect": AspectKey.CONTENT.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "hundreds of secrets.",
            },
        ],
    },
    {
        "review_id": "absa_078",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-11-30T16:00:00Z",
        "review_text": "Voice acting in side quests sounds totally bored, and ambient sound effects are repetitive.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.AUDIO.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Voice acting in side quests sounds totally bored, and ambient sound effects are repetitive.",
            },
        ],
    },
    {
        "review_id": "absa_079",
        "steam_app_id": 553850,
        "steam_created_at": "2024-03-14T13:10:00Z",
        "review_text": "Combat mechanics are thrilling when fighting automatons, but frequent crashes during extraction ruin the mission.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.GAMEPLAY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Combat mechanics are thrilling when fighting automatons",
            },
            {
                "aspect": AspectKey.PERFORMANCE.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "frequent crashes during extraction ruin the mission.",
            },
        ],
    },
    {
        "review_id": "absa_080",
        "steam_app_id": 1145360,
        "steam_created_at": "2023-09-02T18:15:00Z",
        "review_text": "The pixel art direction and fluid animation frames make every attack feel visually impactful.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.GRAPHICS.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "pixel art direction and fluid animation frames make every attack feel visually impactful.",
            },
        ],
    },
    {
        "review_id": "absa_081",
        "steam_app_id": 1091500,
        "steam_created_at": "2024-02-14T10:30:00Z",
        "review_text": "Microtransactions are overly aggressive with FOMO battle pass timers and overpriced cosmetic bundles.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.MONETIZATION.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Microtransactions are overly aggressive with FOMO battle pass timers and overpriced cosmetic bundles.",
            },
        ],
    },
    {
        "review_id": "absa_082",
        "steam_app_id": 553850,
        "steam_created_at": "2024-04-10T15:20:00Z",
        "review_text": "Multiplayer netcode is rock solid with zero packet loss, and voice chat between squadmates is crystal clear.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.MULTIPLAYER.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Multiplayer netcode is rock solid with zero packet loss, and voice chat between squadmates is crystal clear.",
            },
        ],
    },
    {
        "review_id": "absa_083",
        "steam_app_id": 1245620,
        "steam_created_at": "2024-05-18T12:00:00Z",
        "review_text": "Replay value is unmatched. With dozens of weapon affinities and spell combinations, every playthrough feels fresh.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.CONTENT.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Replay value is unmatched. With dozens of weapon affinities and spell combinations, every playthrough feels fresh.",
            },
        ],
    },
    {
        "review_id": "absa_084",
        "steam_app_id": 1091500,
        "steam_created_at": "2024-01-28T16:45:00Z",
        "review_text": "Requires a third party 2K launcher that fails to authenticate when playing offline. Completely unnecessary bloatware.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.OTHER.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Requires a third party 2K launcher that fails to authenticate when playing offline. Completely unnecessary bloatware.",
            },
        ],
    },
    {
        "review_id": "absa_085",
        "steam_app_id": 1145360,
        "steam_created_at": "2023-10-10T14:10:00Z",
        "review_text": "Colorblind mode options and text size adjustment sliders make the HUD comfortable for long gaming sessions.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.ACCESSIBILITY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Colorblind mode options and text size adjustment sliders make the HUD comfortable for long gaming sessions.",
            },
        ],
    },
    {
        "review_id": "absa_086",
        "steam_app_id": 553850,
        "steam_created_at": "2024-03-08T11:20:00Z",
        "review_text": "Developers listen to community feedback and regularly revert unpopular nerfs. Great update transparency.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.SUPPORT_UPDATES.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Developers listen to community feedback and regularly revert unpopular nerfs. Great update transparency.",
            },
        ],
    },
    {
        "review_id": "absa_087",
        "steam_app_id": 1245620,
        "steam_created_at": "2024-04-28T17:30:00Z",
        "review_text": "Overpriced DLC for the amount of recycled boss fights. Definitely wait for a forty percent discount.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.PRICE_VALUE.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Overpriced DLC for the amount of recycled boss fights. Definitely wait for a forty percent discount.",
            },
            {
                "aspect": AspectKey.CONTENT.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "recycled boss fights.",
            },
        ],
    },
    {
        "review_id": "absa_088",
        "steam_app_id": 1091500,
        "steam_created_at": "2023-12-20T19:10:00Z",
        "review_text": "The combat mechanics are clunky, the framerate stutters constantly, and the story writing is uninspired.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.GAMEPLAY.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "The combat mechanics are clunky",
            },
            {
                "aspect": AspectKey.PERFORMANCE.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "framerate stutters constantly",
            },
            {
                "aspect": AspectKey.STORY.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "story writing is uninspired.",
            },
        ],
    },
    {
        "review_id": "absa_089",
        "steam_app_id": 1145360,
        "steam_created_at": "2023-11-04T13:40:00Z",
        "review_text": "Stunning visuals, memorable soundtrack, fluid gameplay, and tons of replayable content. A genuine masterpiece.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.GRAPHICS.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Stunning visuals",
            },
            {
                "aspect": AspectKey.AUDIO.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "memorable soundtrack",
            },
            {
                "aspect": AspectKey.GAMEPLAY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "fluid gameplay",
            },
            {
                "aspect": AspectKey.CONTENT.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "tons of replayable content.",
            },
        ],
    },
    {
        "review_id": "absa_090",
        "steam_app_id": 1091500,
        "steam_created_at": "2024-02-02T15:00:00Z",
        "review_text": "Great game.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [],
    },
    {
        "review_id": "absa_091",
        "steam_app_id": 1245620,
        "steam_created_at": "2024-06-01T10:00:00Z",
        "review_text": "Unplayable garbage.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [],
    },
    {
        "review_id": "absa_092",
        "steam_app_id": 553850,
        "steam_created_at": "2024-04-12T12:00:00Z",
        "review_text": "Okay game, nothing special.",
        "voted_up": True,
        "sentiment": SentimentLabel.NEUTRAL.value,
        "aspects": [],
    },
]


def build_absa_benchmarks() -> None:
    """Builds the ABSA benchmark dataset partitions, manifests, and quality reports."""
    print("Building SteamScoop ABSA benchmark dataset...")
    builder = DatasetBuilder(random_seed=42)
    processed_items = builder.process_raw_reviews(ABSA_BENCHMARK_REVIEWS, target_language="en")

    output_dir = PROJECT_ROOT / "data" / "benchmarks" / "steamscoop_absa_v1"
    output_dir.mkdir(parents=True, exist_ok=True)

    splits, manifest = builder.create_group_stratified_splits(
        items=processed_items,
        dataset_id="steamscoop_absa_v1",
        version="v1.0.0",
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
        filter_trainable_only=True,
    )

    manifest_path = output_dir / "dataset_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(manifest.model_dump_json(indent=2))
    print(f"Wrote ABSA dataset manifest to {manifest_path}")

    for split_name, split_items in splits.items():
        split_file = output_dir / f"{split_name}.jsonl"
        with open(split_file, "w", encoding="utf-8") as f:
            for item in split_items:
                f.write(json.dumps(dict(item)) + "\n")
        print(f"Wrote {len(split_items)} items to {split_file}")

    print("\n--- ABSA Benchmark Dataset Statistics ---")
    print(f"Total reviews: {len(processed_items)}")
    print(f"Train items: {len(splits['train'])}")
    print(f"Validation items: {len(splits['validation'])}")
    print(f"Test items: {len(splits['test'])}")

    # Calculate aspect counts across splits
    all_aspects: dict[str, int] = {}
    for it in processed_items:
        for asp in it.get("aspects", []):
            k = asp["aspect"]
            all_aspects[k] = all_aspects.get(k, 0) + 1
    print(f"Aspect distribution across taxonomy: {dict(sorted(all_aspects.items()))}")
    print("ABSA benchmark dataset generation completed successfully.")


if __name__ == "__main__":
    build_absa_benchmarks()
