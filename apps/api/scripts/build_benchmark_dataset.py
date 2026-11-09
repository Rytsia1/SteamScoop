"""Benchmark dataset generator and manifest builder for SteamScoop NLP pipelines.

Generates reproducible train, validation, and test splits with zero data leakage
and creates canonical benchmark files and experiment configs in data/benchmarks/.
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

from app.ml.config import (
    ExperimentConfig,
    LinearClassifierHyperparameters,
    TFIDFHyperparameters,
    TopicModelHyperparameters,
)
from app.ml.dataset_builder import DatasetBuilder
from app.ml.report import DataQualityReporter
from app.ml.taxonomy import AspectKey, SentimentLabel

# Canonical benchmark raw reviews
BENCHMARK_RAW_REVIEWS: list[dict[str, Any]] = [
    # Positive reviews across aspects
    {
        "review_id": "rev_001",
        "steam_app_id": 1091500,
        "review_text": "Cyberpunk 2077 has redeemed itself! The graphics with ray tracing are unbelievable, and Night City feels alive. The story kept me hooked for 80 hours.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.GRAPHICS.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "graphics with ray tracing are unbelievable",
            },
            {
                "aspect": AspectKey.STORY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "story kept me hooked",
            },
            {
                "aspect": AspectKey.CONTENT.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "kept me hooked for 80 hours",
            },
        ],
    },
    {
        "review_id": "rev_002",
        "steam_app_id": 1091500,
        "review_text": "Combat mechanics feel crisp and fluid. Hacking enemies from the shadows never gets old. Great gunplay and weapon variety.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.GAMEPLAY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Combat mechanics feel crisp and fluid",
            },
        ],
    },
    {
        "review_id": "rev_003",
        "steam_app_id": 1091500,
        "review_text": "The soundtrack is an absolute masterpiece. The radio stations perfectly capture the dystopian vibe and combat tracks get the adrenaline pumping.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.AUDIO.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "soundtrack is an absolute masterpiece",
            },
        ],
    },
    {
        "review_id": "rev_004",
        "steam_app_id": 1091500,
        "review_text": "Solid 120 FPS on high settings after the 2.0 overhaul. DLSS 3 frame generation runs flawlessly with zero stuttering.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.PERFORMANCE.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Solid 120 FPS on high settings",
            },
            {
                "aspect": AspectKey.SUPPORT_UPDATES.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "after the 2.0 overhaul",
            },
        ],
    },
    {
        "review_id": "rev_005",
        "steam_app_id": 1145360,
        "review_text": "Hades is roguelike perfection. The dialogue progression between escape attempts is genius, and voice acting is top tier.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.GAMEPLAY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "roguelike perfection",
            },
            {
                "aspect": AspectKey.STORY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "dialogue progression between escape attempts is genius",
            },
            {
                "aspect": AspectKey.AUDIO.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "voice acting is top tier",
            },
        ],
    },
    {
        "review_id": "rev_006",
        "steam_app_id": 1145360,
        "review_text": "God Mode in Hades is an incredible accessibility feature. It lets anyone experience the narrative without breaking the challenge.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.ACCESSIBILITY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "God Mode in Hades is an incredible accessibility feature",
            },
            {
                "aspect": AspectKey.STORY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "experience the narrative",
            },
        ],
    },
    {
        "review_id": "rev_007",
        "steam_app_id": 1145360,
        "review_text": "For 25 dollars, you get over 100 hours of quality content. Best dollar-per-hour value on Steam hands down.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.PRICE_VALUE.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Best dollar-per-hour value on Steam",
            },
            {
                "aspect": AspectKey.CONTENT.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "over 100 hours of quality content",
            },
        ],
    },
    {
        "review_id": "rev_008",
        "steam_app_id": 553850,
        "review_text": "Helldivers 2 co-op with friends is pure chaos and fun. Friendly fire leads to hilarious moments. Excellent cooperative PvE multiplayer.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.MULTIPLAYER.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "co-op with friends is pure chaos and fun",
            },
            {
                "aspect": AspectKey.GAMEPLAY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "pure chaos and fun",
            },
        ],
    },
    {
        "review_id": "rev_009",
        "steam_app_id": 553850,
        "review_text": "The war bond battle passes never expire! You can earn super credits just by playing missions. Very fair monetization model.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.MONETIZATION.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "war bond battle passes never expire",
            },
        ],
    },
    {
        "review_id": "rev_010",
        "steam_app_id": 1245620,
        "review_text": "Elden Ring is a masterclass in world design. Every corner rewards exploration, and boss fights are brutal yet fair.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.GAMEPLAY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "boss fights are brutal yet fair",
            },
            {
                "aspect": AspectKey.CONTENT.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Every corner rewards exploration",
            },
        ],
    },
    {
        "review_id": "rev_011",
        "steam_app_id": 1245620,
        "review_text": "The devs quickly patched stuttering issues on PC. Good post-launch support and regular balancing patches.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.SUPPORT_UPDATES.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "devs quickly patched stuttering issues",
            },
            {
                "aspect": AspectKey.PERFORMANCE.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "patched stuttering issues on PC",
            },
        ],
    },
    {
        "review_id": "rev_012",
        "steam_app_id": 814380,
        "review_text": "Sekiro's parry system is the most satisfying sword combat ever created in gaming. When you deflect all hits in rhythm, it feels amazing.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.GAMEPLAY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "satisfying sword combat ever created",
            },
        ],
    },
    {
        "review_id": "rev_013",
        "steam_app_id": 292030,
        "review_text": "The Witcher 3 has the finest side quests in gaming history. Bloody Baron's story arc is unforgettable. 10/10 masterwork.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.STORY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "finest side quests in gaming history",
            },
            {
                "aspect": AspectKey.CONTENT.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Bloody Baron's story arc is unforgettable",
            },
        ],
    },
    {
        "review_id": "rev_014",
        "steam_app_id": 292030,
        "review_text": "Slavic folk music and environmental sounds in Velen build incredible atmospheric immersion. Masterful audio design.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.AUDIO.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Slavic folk music and environmental sounds",
            },
        ],
    },
    {
        "review_id": "rev_015",
        "steam_app_id": 1145360,
        "review_text": "Masterpiece",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [],
    },
    {
        "review_id": "rev_016",
        "steam_app_id": 1145360,
        "review_text": "Not bad at all. Actually exceeded all my initial expectations by a mile.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.OTHER.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "exceeded all my initial expectations",
            },
        ],
    },
    # Negative reviews across aspects
    {
        "review_id": "rev_017",
        "steam_app_id": 1091500,
        "review_text": "Constant crashes to desktop every 20 minutes. Game drops from 60 FPS down to 14 FPS in crowded areas. Unplayable stuttering.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.PERFORMANCE.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Constant crashes to desktop every 20 minutes",
            },
        ],
    },
    {
        "review_id": "rev_018",
        "steam_app_id": 1091500,
        "review_text": "The AI is completely brain dead. Police spawn directly behind your back out of thin air. Combat feels empty and hollow.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.GAMEPLAY.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "The AI is completely brain dead",
            },
        ],
    },
    {
        "review_id": "rev_019",
        "steam_app_id": 553850,
        "review_text": "Server error 10002018. Cannot connect to game. Stuck in queue for 2 hours. Multiplayer matchmaker is completely broken.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.MULTIPLAYER.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Server error 10002018. Cannot connect to game",
            },
            {
                "aspect": AspectKey.PERFORMANCE.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Stuck in queue for 2 hours",
            },
        ],
    },
    {
        "review_id": "rev_020",
        "steam_app_id": 553850,
        "review_text": "Greedy publisher forcing PSN account linking in 170 unsupported countries. Disgraceful anti-consumer behavior.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.SUPPORT_UPDATES.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "forcing PSN account linking",
            },
            {
                "aspect": AspectKey.OTHER.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Disgraceful anti-consumer behavior",
            },
        ],
    },
    {
        "review_id": "rev_021",
        "steam_app_id": 2357570,
        "review_text": "70 dollar price tag for an unfinished game filled with aggressive microtransactions and 20 dollar skins. Avoid this scam.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.PRICE_VALUE.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "70 dollar price tag for an unfinished game",
            },
            {
                "aspect": AspectKey.MONETIZATION.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "aggressive microtransactions and 20 dollar skins",
            },
        ],
    },
    {
        "review_id": "rev_022",
        "steam_app_id": 2357570,
        "review_text": "The story makes zero sense and characters are completely obnoxious. Dialogue was written by an algorithm. Terrible ending.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.STORY.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "story makes zero sense and characters are completely obnoxious",
            },
        ],
    },
    {
        "review_id": "rev_023",
        "steam_app_id": 2357570,
        "review_text": "Zero subtitle sizing options, no colorblind mode, and keybindings cannot be remapped. Complete lack of accessibility support.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.ACCESSIBILITY.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Complete lack of accessibility support",
            },
        ],
    },
    {
        "review_id": "rev_024",
        "steam_app_id": 2357570,
        "review_text": "Audio mixing is atrocious. Gunshots deafen you while character voices are barely audible whisper murmurs. No volume sliders.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.AUDIO.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Audio mixing is atrocious",
            },
        ],
    },
    {
        "review_id": "rev_025",
        "steam_app_id": 2357570,
        "review_text": "Blurry textures and heavy ghosting artifacts from forced TAA. Looks worse than games released ten years ago.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.GRAPHICS.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Blurry textures and heavy ghosting artifacts",
            },
        ],
    },
    {
        "review_id": "rev_026",
        "steam_app_id": 2357570,
        "review_text": "Only 3 maps and repetitive fetch quests. You can finish the entire campaign in 4 hours. Not worth the money.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.CONTENT.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Only 3 maps and repetitive fetch quests",
            },
            {
                "aspect": AspectKey.PRICE_VALUE.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Not worth the money",
            },
        ],
    },
    {
        "review_id": "rev_027",
        "steam_app_id": 2357570,
        "review_text": "Total garbage",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [],
    },
    {
        "review_id": "rev_028",
        "steam_app_id": 2357570,
        "review_text": "Do not buy this game. The developers abandoned it after two weeks without fixing game-breaking progress bugs.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.SUPPORT_UPDATES.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "developers abandoned it after two weeks",
            },
        ],
    },
    {
        "review_id": "rev_029",
        "steam_app_id": 1091500,
        "review_text": "Best crash-to-desktop simulator of the year, 10/10 would freeze my RTX 4090 again.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.PERFORMANCE.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Best crash-to-desktop simulator",
            },
        ],
    },
    {
        "review_id": "rev_030",
        "steam_app_id": 1091500,
        "review_text": "I will never recommend this game to anyone until they rebuild the physics engine from scratch.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.GAMEPLAY.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "rebuild the physics engine from scratch",
            },
        ],
    },
    # Neutral and mixed reviews
    {
        "review_id": "rev_031",
        "steam_app_id": 1091500,
        "review_text": "The story and visuals are genuinely great, but the terrible performance and bugs make it impossible to give a full recommendation. Wait for patches.",
        "voted_up": True,  # Voted up despite critical reservation
        "sentiment": SentimentLabel.NEUTRAL.value,
        "aspects": [
            {
                "aspect": AspectKey.STORY.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "story and visuals are genuinely great",
            },
            {
                "aspect": AspectKey.GRAPHICS.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "story and visuals are genuinely great",
            },
            {
                "aspect": AspectKey.PERFORMANCE.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "terrible performance and bugs",
            },
        ],
    },
    {
        "review_id": "rev_032",
        "steam_app_id": 1091500,
        "review_text": "Average shooter with RPG elements. Neither good nor bad, just thoroughly mediocre. Pick it up on a deep 50% discount.",
        "voted_up": True,
        "sentiment": SentimentLabel.NEUTRAL.value,
        "aspects": [
            {
                "aspect": AspectKey.GAMEPLAY.value,
                "sentiment": SentimentLabel.NEUTRAL.value,
                "snippet": "Average shooter with RPG elements",
            },
            {
                "aspect": AspectKey.PRICE_VALUE.value,
                "sentiment": SentimentLabel.NEUTRAL.value,
                "snippet": "Pick it up on a deep 50% discount",
            },
        ],
    },
    {
        "review_id": "rev_033",
        "steam_app_id": 1145360,
        "review_text": "Art direction is stunning, but roguelikes simply are not my cup of tea. If you like the genre it is good, but for others it might feel grindy.",
        "voted_up": True,
        "sentiment": SentimentLabel.NEUTRAL.value,
        "aspects": [
            {
                "aspect": AspectKey.GRAPHICS.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Art direction is stunning",
            },
            {
                "aspect": AspectKey.GAMEPLAY.value,
                "sentiment": SentimentLabel.NEUTRAL.value,
                "snippet": "roguelikes simply are not my cup of tea",
            },
        ],
    },
    {
        "review_id": "rev_034",
        "steam_app_id": 553850,
        "review_text": "Servers are having queue issues on weekends, but weekdays work fine. Gameplay is decent. Mixed feelings overall.",
        "voted_up": False,  # Voted down despite neutral text
        "sentiment": SentimentLabel.NEUTRAL.value,
        "aspects": [
            {
                "aspect": AspectKey.MULTIPLAYER.value,
                "sentiment": SentimentLabel.NEUTRAL.value,
                "snippet": "Servers are having queue issues on weekends",
            },
            {
                "aspect": AspectKey.GAMEPLAY.value,
                "sentiment": SentimentLabel.NEUTRAL.value,
                "snippet": "Gameplay is decent",
            },
        ],
    },
    {
        "review_id": "rev_035",
        "steam_app_id": 1245620,
        "review_text": "Runs at 60 FPS capped. Default keybinds on keyboard are strange, but playing with a controller is acceptable.",
        "voted_up": True,
        "sentiment": SentimentLabel.NEUTRAL.value,
        "aspects": [
            {
                "aspect": AspectKey.PERFORMANCE.value,
                "sentiment": SentimentLabel.NEUTRAL.value,
                "snippet": "Runs at 60 FPS capped",
            },
            {
                "aspect": AspectKey.GAMEPLAY.value,
                "sentiment": SentimentLabel.NEUTRAL.value,
                "snippet": "playing with a controller is acceptable",
            },
        ],
    },
    {
        "review_id": "rev_036",
        "steam_app_id": 292030,
        "review_text": "A standard open world fantasy RPG. Has good voice lines and lots of question marks on the map. It does what it sets out to do.",
        "voted_up": True,
        "sentiment": SentimentLabel.NEUTRAL.value,
        "aspects": [
            {
                "aspect": AspectKey.CONTENT.value,
                "sentiment": SentimentLabel.NEUTRAL.value,
                "snippet": "lots of question marks on the map",
            },
            {
                "aspect": AspectKey.AUDIO.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "good voice lines",
            },
        ],
    },
    {
        "review_id": "rev_037",
        "steam_app_id": 2357570,
        "review_text": "Meh, okay. Nothing special.",
        "voted_up": True,
        "sentiment": SentimentLabel.NEUTRAL.value,
        "aspects": [],
    },
    {
        "review_id": "rev_038",
        "steam_app_id": 2357570,
        "review_text": "Has potential if the developers deliver the promised roadmap. As of now, it sits right in the middle.",
        "voted_up": True,
        "sentiment": SentimentLabel.NEUTRAL.value,
        "aspects": [
            {
                "aspect": AspectKey.SUPPORT_UPDATES.value,
                "sentiment": SentimentLabel.NEUTRAL.value,
                "snippet": "promised roadmap",
            },
        ],
    },
    # Duplicate / near-duplicate clusters to test leakage prevention
    {
        "review_id": "rev_039",
        "steam_app_id": 553850,
        "review_text": "Fix the servers already! Game is unplayable on weekends.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.MULTIPLAYER.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Fix the servers already",
            },
        ],
    },
    {
        "review_id": "rev_040",  # Exact duplicate text
        "steam_app_id": 553850,
        "review_text": "Fix the servers already! Game is unplayable on weekends.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.MULTIPLAYER.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Fix the servers already",
            },
        ],
    },
    {
        "review_id": "rev_041",  # Near duplicate text
        "steam_app_id": 553850,
        "review_text": "Fix the servers already! The game is unplayable on weekends.",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.MULTIPLAYER.value,
                "sentiment": SentimentLabel.NEGATIVE.value,
                "snippet": "Fix the servers already",
            },
        ],
    },
    {
        "review_id": "rev_042",
        "steam_app_id": 1145360,
        "review_text": "Instant buy. Do not hesitate.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.PRICE_VALUE.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Instant buy",
            },
        ],
    },
    {
        "review_id": "rev_043",  # Exact duplicate text
        "steam_app_id": 1145360,
        "review_text": "Instant buy. Do not hesitate.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [
            {
                "aspect": AspectKey.PRICE_VALUE.value,
                "sentiment": SentimentLabel.POSITIVE.value,
                "snippet": "Instant buy",
            },
        ],
    },
    # Non-trainable and foreign language reviews to verify quality and language filtering
    {
        "review_id": "rev_044",  # Foreign - Russian
        "steam_app_id": 1091500,
        "review_text": "Отличная игра, прекрасный сюжет и потрясающая графика в Найт-Сити.",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [],
    },
    {
        "review_id": "rev_045",  # Foreign - Simplified Chinese
        "steam_app_id": 1091500,
        "review_text": "画面非常震撼，剧情也很有代入感，很喜欢夜之城的氛围！",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [],
    },
    {
        "review_id": "rev_046",  # Foreign - Korean
        "steam_app_id": 1145360,
        "review_text": "로그라이크 장르 중에서 최고의 완성도를 보여줍니다. 강추!",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [],
    },
    {
        "review_id": "rev_047",  # Non-trainable - Spam / ASCII art copypasta
        "steam_app_id": 1091500,
        "review_text": "⠀⠀⠀⠀⠀⢀⣤⠤⠤⠤⠤⠤⠤⠤⢤⣤⣀⠀⠀⠀⠀\n⠀⠀⠀⠀⢰⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⢻⣆⠀⠀⠀\n░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░\nShrek was here 10/10",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [],
    },
    {
        "review_id": "rev_048",  # Non-trainable - Empty text after trim
        "steam_app_id": 1091500,
        "review_text": "    \n\t  \n  ",
        "voted_up": True,
        "sentiment": SentimentLabel.POSITIVE.value,
        "aspects": [],
    },
    {
        "review_id": "rev_049",  # Non-trainable - Insufficient evidence (period only)
        "steam_app_id": 1091500,
        "review_text": "...",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [],
    },
    {
        "review_id": "rev_050",  # Non-trainable - Heart / profanity flood
        "steam_app_id": 1091500,
        "review_text": "♥♥♥♥♥♥♥♥♥♥♥♥♥♥♥♥♥♥♥♥",
        "voted_up": False,
        "sentiment": SentimentLabel.NEGATIVE.value,
        "aspects": [],
    },
]


def build_benchmarks() -> None:
    """Builds benchmark dataset partitions, manifests, quality reports, and experiment specs."""
    print("Initializing SteamScoop DatasetBuilder pipeline...")
    builder = DatasetBuilder(random_seed=42)

    # 1. Process all raw reviews
    print(f"Processing {len(BENCHMARK_RAW_REVIEWS)} benchmark candidates...")
    processed_items = builder.process_raw_reviews(BENCHMARK_RAW_REVIEWS, target_language="en")

    # 2. Split into group-stratified Train / Val / Test (filter trainable en only)
    splits, manifest = builder.create_group_stratified_splits(
        items=processed_items,
        dataset_id="steamscoop-sentiment-benchmark-v1",
        version="v1.0.0",
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
        filter_trainable_only=True,
    )

    # Output directory
    output_dir = PROJECT_ROOT / "data" / "benchmarks" / "steamscoop_sentiment_v1"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 3. Write split JSONL files
    for split_name, items in splits.items():
        file_path = output_dir / f"{split_name}.jsonl"
        with open(file_path, "w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(dict(item), ensure_ascii=False) + "\n")
        print(f"Wrote {len(items)} examples to {file_path}")

    # 4. Write dataset manifest
    manifest_path = output_dir / "dataset_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(manifest.model_dump_json(indent=2))
    print(f"Wrote dataset manifest to {manifest_path}")

    # 5. Generate and write baseline experiment configurations
    exp_dir = PROJECT_ROOT / "data" / "benchmarks" / "experiments"
    exp_dir.mkdir(parents=True, exist_ok=True)

    # Baseline Sentiment: TF-IDF + Logistic Regression
    sentiment_exp = ExperimentConfig(
        experiment_name="baseline-sentiment-tfidf-logreg",
        experiment_id="exp-sent-001",
        task="sentiment",
        dataset_version="v1.0.0",
        dataset_manifest_path="data/benchmarks/steamscoop_sentiment_v1/dataset_manifest.json",
        preprocessing_version="v1.0.0",
        random_seed=42,
        hyperparameters={
            "tfidf": TFIDFHyperparameters(max_features=5000, ngram_range=(1, 2)).model_dump(),
            "classifier": LinearClassifierHyperparameters(
                classifier_type="logistic_regression",
                c_regularization=1.0,
                class_weight="balanced",
            ).model_dump(),
        },
        metrics_tracked=["macro_f1", "weighted_f1", "accuracy", "per_class_f1"],
        acceptance_criteria={"min_macro_f1": 0.75, "min_accuracy": 0.75},
        metadata={"model_family": "classical_baseline", "tier": "mvp_baseline"},
    )
    sentiment_exp_path = exp_dir / "baseline_sentiment_tfidf.json"
    with open(sentiment_exp_path, "w", encoding="utf-8") as f:
        f.write(sentiment_exp.model_dump_json(indent=2))
    print(f"Wrote baseline sentiment experiment config to {sentiment_exp_path}")

    # Baseline ABSA: One-vs-Rest TF-IDF + Linear Classifiers
    absa_exp = ExperimentConfig(
        experiment_name="baseline-absa-multilabel-tfidf",
        experiment_id="exp-absa-001",
        task="absa",
        dataset_version="v1.0.0",
        dataset_manifest_path="data/benchmarks/steamscoop_sentiment_v1/dataset_manifest.json",
        preprocessing_version="v1.0.0",
        random_seed=42,
        hyperparameters={
            "tfidf": TFIDFHyperparameters(max_features=8000, ngram_range=(1, 2)).model_dump(),
            "classifier": LinearClassifierHyperparameters(
                classifier_type="linear_svc",
                c_regularization=0.5,
                class_weight="balanced",
            ).model_dump(),
            "num_aspects": 12,
        },
        metrics_tracked=["macro_aspect_f1", "micro_aspect_f1", "aspect_polarity_accuracy"],
        acceptance_criteria={"min_macro_aspect_f1": 0.65},
        metadata={"model_family": "classical_baseline", "tier": "mvp_baseline"},
    )
    absa_exp_path = exp_dir / "baseline_absa_tfidf.json"
    with open(absa_exp_path, "w", encoding="utf-8") as f:
        f.write(absa_exp.model_dump_json(indent=2))
    print(f"Wrote baseline ABSA experiment config to {absa_exp_path}")

    # Baseline Topic Modeling: NMF
    topic_exp = ExperimentConfig(
        experiment_name="baseline-topic-nmf",
        experiment_id="exp-topic-001",
        task="topic",
        dataset_version="v1.0.0",
        dataset_manifest_path="data/benchmarks/steamscoop_sentiment_v1/dataset_manifest.json",
        preprocessing_version="v1.0.0",
        random_seed=42,
        hyperparameters={
            "topic_model": TopicModelHyperparameters(
                method="nmf", num_topics=8, max_features=3000
            ).model_dump(),
        },
        metrics_tracked=["topic_diversity", "npmi_coherence", "mean_pairwise_jaccard"],
        acceptance_criteria={"min_topic_diversity": 0.70},
        metadata={"model_family": "nmf_baseline", "tier": "mvp_baseline"},
    )
    topic_exp_path = exp_dir / "baseline_topic_nmf.json"
    with open(topic_exp_path, "w", encoding="utf-8") as f:
        f.write(topic_exp.model_dump_json(indent=2))
    print(f"Wrote baseline topic experiment config to {topic_exp_path}")

    # 6. Generate Data Quality Report Summary
    reporter = DataQualityReporter()
    summary = reporter.generate_report(processed_items)
    print("\n--- Data Quality Summary ---")
    print(f"Total Evaluated: {summary.total_evaluated}")
    print(f"Trainable English Items: {summary.trainable_count} ({summary.trainable_percentage}%)")
    print(f"Quality Statuses: {dict(summary.status_counts)}")
    print(f"Duplicate Rate: {summary.duplicate_rate:.2%}")
    print(f"Unique Clusters: {summary.unique_clusters_count}")
    print(f"Train Split: {len(splits['train'])} items")
    print(f"Validation Split: {len(splits['validation'])} items")
    print(f"Test Split: {len(splits['test'])} items")
    print("Benchmark generation completed successfully.")


if __name__ == "__main__":
    build_benchmarks()
