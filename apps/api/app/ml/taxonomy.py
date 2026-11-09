from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SentimentLabel(StrEnum):
    """Target sentiment label space according to ML_SPECIFICATION.md Section 2.3."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class AspectKey(StrEnum):
    """Controlled aspect taxonomy machine keys according to ML_SPECIFICATION.md Section 6.3."""

    GAMEPLAY = "gameplay"
    STORY = "story"
    GRAPHICS = "graphics"
    AUDIO = "audio"
    PERFORMANCE = "performance"
    CONTENT = "content"
    MULTIPLAYER = "multiplayer"
    MONETIZATION = "monetization"
    PRICE_VALUE = "price_value"
    SUPPORT_UPDATES = "support_updates"
    ACCESSIBILITY = "accessibility"
    OTHER = "other"


class AspectDefinition(BaseModel):
    """Metadata definition for a controlled aspect in the SteamScoop taxonomy."""

    model_config = ConfigDict(frozen=True)

    key: AspectKey
    display_name: str
    description: str
    scope_examples: list[str]
    seed_keywords: list[str]


# Authoritative controlled taxonomy mapping (Taxonomy Version 1.0.0)
ASPECT_TAXONOMY: dict[AspectKey, AspectDefinition] = {
    AspectKey.GAMEPLAY: AspectDefinition(
        key=AspectKey.GAMEPLAY,
        display_name="Gameplay",
        description=(
            "Core mechanics, combat responsiveness, movement, controls, game feel, and balance."
        ),
        scope_examples=[
            "combat mechanics",
            "character movement",
            "difficulty curve",
            "boss fights",
            "skill tree design",
        ],
        seed_keywords=[
            "gameplay",
            "combat",
            "controls",
            "mechanics",
            "movement",
            "gunplay",
            "boss",
            "difficulty",
            "clunky",
            "responsive",
        ],
    ),
    AspectKey.STORY: AspectDefinition(
        key=AspectKey.STORY,
        display_name="Story & Narrative",
        description=(
            "Plot, characters, lore, worldbuilding, dialogue, voice writing, "
            "and storytelling pacing."
        ),
        scope_examples=[
            "main questline",
            "character development",
            "dialogue choices",
            "lore depth",
            "emotional payoff",
        ],
        seed_keywords=[
            "story",
            "plot",
            "narrative",
            "character",
            "lore",
            "dialogue",
            "writing",
            "ending",
            "voice acting",
            "cutscenes",
        ],
    ),
    AspectKey.GRAPHICS: AspectDefinition(
        key=AspectKey.GRAPHICS,
        display_name="Graphics & Visuals",
        description=(
            "Visual quality, art direction, lighting, animation fidelity, UI aesthetics, "
            "and visual atmosphere."
        ),
        scope_examples=[
            "art style",
            "lighting effects",
            "animation quality",
            "texture detail",
            "character models",
        ],
        seed_keywords=[
            "graphics",
            "visuals",
            "art",
            "animation",
            "textures",
            "lighting",
            "gorgeous",
            "ugly",
            "beautiful",
            "models",
        ],
    ),
    AspectKey.AUDIO: AspectDefinition(
        key=AspectKey.AUDIO,
        display_name="Audio & Music",
        description=(
            "Soundtrack (OST), ambient audio, sound effects (SFX), "
            "voice acting performances, and audio mixing."
        ),
        scope_examples=[
            "original soundtrack",
            "weapon sound effects",
            "voice acting delivery",
            "atmospheric audio design",
        ],
        seed_keywords=[
            "soundtrack",
            "music",
            "audio",
            "ost",
            "sound",
            "sfx",
            "voice acting",
            "composer",
            "earrape",
            "banger",
        ],
    ),
    AspectKey.PERFORMANCE: AspectDefinition(
        key=AspectKey.PERFORMANCE,
        display_name="Performance & Stability",
        description=(
            "Framerate (FPS), stuttering, hardware optimization, crashes, "
            "game-breaking bugs, and glitches."
        ),
        scope_examples=[
            "frame rate stability",
            "desktop crashes",
            "stuttering on high-end hardware",
            "memory leaks",
            "glitches",
        ],
        seed_keywords=[
            "performance",
            "fps",
            "lag",
            "stutter",
            "crash",
            "crashes",
            "bug",
            "bugs",
            "optimization",
            "glitch",
            "freeze",
        ],
    ),
    AspectKey.CONTENT: AspectDefinition(
        key=AspectKey.CONTENT,
        display_name="Content & Replayability",
        description=(
            "Volume of content, campaign duration, replay value, map variety, "
            "side activities, and endgame loop."
        ),
        scope_examples=[
            "hours of content",
            "replayability",
            "level variety",
            "endgame activities",
            "modding support",
        ],
        seed_keywords=[
            "content",
            "replayability",
            "short",
            "length",
            "hours",
            "endgame",
            "variety",
            "repetitive",
            "replay",
            "grind",
        ],
    ),
    AspectKey.MULTIPLAYER: AspectDefinition(
        key=AspectKey.MULTIPLAYER,
        display_name="Multiplayer & Online",
        description=(
            "Netcode, server stability, matchmaking quality, co-op experience, "
            "PvP balance, and online community."
        ),
        scope_examples=[
            "co-op connection",
            "matchmaking queue times",
            "server ping / tickrate",
            "ranked PvP balance",
            "toxic playerbase",
        ],
        seed_keywords=[
            "multiplayer",
            "coop",
            "co-op",
            "pvp",
            "servers",
            "netcode",
            "matchmaking",
            "ping",
            "cheaters",
            "friends",
        ],
    ),
    AspectKey.MONETIZATION: AspectDefinition(
        key=AspectKey.MONETIZATION,
        display_name="Monetization",
        description=(
            "Microtransactions (MTX), battle passes, pay-to-win mechanics, "
            "gacha mechanics, and DLC practices."
        ),
        scope_examples=[
            "aggressive microtransactions",
            "pay-to-win items",
            "battle pass progression",
            "overpriced cosmetics",
        ],
        seed_keywords=[
            "microtransactions",
            "mtx",
            "battle pass",
            "pay to win",
            "p2w",
            "dlc",
            "lootbox",
            "greed",
            "cosmetics",
            "cash grab",
        ],
    ),
    AspectKey.PRICE_VALUE: AspectDefinition(
        key=AspectKey.PRICE_VALUE,
        display_name="Price & Value",
        description=(
            "Base retail price justification, sale discount value, perceived value for money spent."
        ),
        scope_examples=[
            "worth full price",
            "wait for a sale",
            "overpriced for what it offers",
            "fantastic value per dollar",
        ],
        seed_keywords=[
            "price",
            "worth",
            "cost",
            "sale",
            "cheap",
            "expensive",
            "value",
            "overpriced",
            "dollars",
            "cents",
        ],
    ),
    AspectKey.SUPPORT_UPDATES: AspectDefinition(
        key=AspectKey.SUPPORT_UPDATES,
        display_name="Support & Updates",
        description=(
            "Post-launch patches, developer communication, transparency, "
            "roadmap execution, and long-term support."
        ),
        scope_examples=[
            "developer responsiveness",
            "frequency of patches",
            "abandoned early access",
            "community interaction",
        ],
        seed_keywords=[
            "updates",
            "patch",
            "patches",
            "developers",
            "devs",
            "support",
            "roadmap",
            "abandoned",
            "fixes",
            "early access",
        ],
    ),
    AspectKey.ACCESSIBILITY: AspectDefinition(
        key=AspectKey.ACCESSIBILITY,
        display_name="Accessibility & Usability",
        description=(
            "Subtitle customization, colorblind filters, key remapping, "
            "motion sickness options, difficulty settings."
        ),
        scope_examples=[
            "custom keybinds",
            "colorblind modes",
            "motion sickness toggles",
            "subtitles readability",
            "font sizing",
        ],
        seed_keywords=[
            "accessibility",
            "subtitles",
            "colorblind",
            "keybinds",
            "motion sickness",
            "fov",
            "font size",
            "rebind",
            "options",
        ],
    ),
    AspectKey.OTHER: AspectDefinition(
        key=AspectKey.OTHER,
        display_name="Other Game Aspects",
        description=(
            "Relevant game-related considerations not covered above "
            "(e.g., third-party launcher, anti-cheat, OS support)."
        ),
        scope_examples=[
            "anti-cheat system issues (e.g. kernel drivers)",
            "external launcher requirements (EA, Ubisoft)",
            "Linux / Steam Deck compatibility",
        ],
        seed_keywords=[
            "launcher",
            "anticheat",
            "anti-cheat",
            "denuvo",
            "steam deck",
            "linux",
            "proton",
            "drm",
        ],
    ),
}


class AspectAnnotation(BaseModel):
    """Single aspect mention and polarity annotation."""

    model_config = ConfigDict(frozen=True)

    aspect: AspectKey
    sentiment: SentimentLabel
    evidence_span: str | None = Field(
        default=None,
        description="Exact substring from review text supporting this aspect judgment",
    )
    start_char: int | None = Field(
        default=None,
        ge=0,
        description="Start character index of evidence in normalized text",
    )
    end_char: int | None = Field(
        default=None,
        ge=0,
        description="End character index of evidence in normalized text",
    )


class LabeledReviewRecord(BaseModel):
    """Complete annotated review record with ground-truth sentiment and aspect annotations."""

    model_config = ConfigDict(frozen=True)

    review_id: str = Field(description="Unique review identifier")
    steam_app_id: int = Field(description="Steam Application ID")
    raw_text: str = Field(description="Original verbatim Steam user review text")
    normalized_text: str = Field(description="Normalized review text used for NLP inputs")
    language: str = Field(default="en", description="Detected or annotated language")
    voted_up: bool = Field(description="Steam source recommendation signal (not ground truth)")
    sentiment: SentimentLabel = Field(description="Ground-truth overall text sentiment label")
    aspects: list[AspectAnnotation] = Field(
        default_factory=list,
        description="Aspect mentions and aspect-level polarity",
    )
    is_sarcastic: bool = Field(
        default=False, description="Flag indicating presence of sarcasm/irony"
    )
    annotator_id: str | None = Field(
        default=None,
        description="Internal pseudonymous annotator identifier",
    )
    annotation_round: int = Field(
        default=1, description="Annotation iteration or adjudication round"
    )
    notes: str | None = Field(default=None, description="Adjudicator notes or difficulty tags")
    metadata_: dict[str, Any] = Field(
        default_factory=dict,
        description="Auxiliary provenance metadata (e.g. playtime, timestamps)",
    )
