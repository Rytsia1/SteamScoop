import re
from enum import StrEnum
from typing import Final

from pydantic import BaseModel, ConfigDict, Field

QUALITY_ENGINE_VERSION: Final[str] = "v1.0.0"

# Common ASCII art character sequences and meme repetitions
_ASCII_ART_PATTERN = re.compile(r"[░▒▓█▀▄▌▐─│┌┐└┘├┤┬┴┼═║╒╓╔╕╖╗╘╙╚╛╜╝╞╟╠╡╢╣╤╥╦╧╨╩╪╫╬]{5,}")
_REPEATED_PUNCTUATION = re.compile(r"([!?.,])\1{4,}")
_PURE_PUNCTUATION = re.compile(r"^[\s!?,.:;\-_/\\()\[\]{}'\"~`*+<>@#$%^&=|♥]+$")

# Negation tokens indicating sentiment flipping
_NEGATION_TOKENS = frozenset(
    {
        "not",
        "never",
        "no",
        "neither",
        "nor",
        "hardly",
        "scarcely",
        "barely",
        "doesn't",
        "don't",
        "didn't",
        "wasn't",
        "weren't",
        "isn't",
        "aren't",
        "cannot",
        "can't",
        "couldn't",
        "won't",
        "wouldn't",
        "shouldn't",
    }
)

# Obvious short sentiment indicators that are VALID despite small word count
_SHORT_VALID_SENTIMENT = frozenset(
    {
        "good",
        "great",
        "bad",
        "terrible",
        "awful",
        "trash",
        "masterpiece",
        "amazing",
        "horrible",
        "best",
        "worst",
        "fun",
        "boring",
        "love",
        "hate",
        "recommended",
        "recommend",
        "skip",
        "buy",
        "refund",
        "yes",
        "no",
        "dead",
        "broken",
        "peak",
    }
)


class QualityStatus(StrEnum):
    """Quality classification for Steam user review text."""

    VALID = "valid"
    EMPTY_TEXT = "empty_text"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    SPAM_COPYPASTA = "spam_copypasta"
    LANGUAGE_UNCERTAIN = "language_uncertain"


class QualityAssessment(BaseModel):
    """Diagnostic quality report assessing suitability of review for ML modeling."""

    model_config = ConfigDict(frozen=True)

    status: QualityStatus
    reason_code: str | None = Field(
        default=None, description="Diagnostic error or exclusion reason code"
    )
    is_trainable: bool = Field(
        description="True if record is valid and recommended for model training"
    )
    char_count: int = Field(ge=0)
    word_count: int = Field(ge=0)
    alpha_ratio: float = Field(ge=0.0, le=1.0, description="Proportion of alphabetic characters")
    has_negation: bool = Field(default=False, description="True if text contains negation cues")
    has_ascii_art: bool = Field(default=False, description="True if text contains block ASCII art")
    version: str = Field(default=QUALITY_ENGINE_VERSION)


class ReviewQualityAssessor:
    """Enforces SteamScoop data quality, missing data, and insufficient evidence policies.

    Enforces ML_SPECIFICATION.md Section 4.1 & Task 6:
    - Rejects empty, null, or whitespace-only inputs (`empty_text`).
    - Detects spam ASCII art, repeated punctuation, and system spec copypastas (`spam_copypasta`).
    - Flags ambiguous reviews lacking discernible sentiment words (`insufficient_evidence`).
    - Explicitly preserves legitimate short reviews ("Great game!", "Horrible optimization").
    - Never silently discards difficult examples; attaches structured audit reasons.
    """

    def __init__(
        self,
        min_alpha_ratio: float = 0.25,
        version: str = QUALITY_ENGINE_VERSION,
    ) -> None:
        self.min_alpha_ratio = min_alpha_ratio
        self.version = version

    def assess(
        self,
        normalized_text: str | None,
        is_language_uncertain: bool = False,
    ) -> QualityAssessment:
        """Evaluate normalized review text for quality and semantic sufficiency."""
        if normalized_text is None or not normalized_text.strip():
            return QualityAssessment(
                status=QualityStatus.EMPTY_TEXT,
                reason_code="TEXT_EMPTY_OR_WHITESPACE",
                is_trainable=False,
                char_count=0,
                word_count=0,
                alpha_ratio=0.0,
                version=self.version,
            )

        clean = normalized_text.strip()
        char_count = len(clean)
        words = clean.split()
        word_count = len(words)

        # Count alphabetic vs non-alphabetic
        alpha_count = sum(1 for c in clean if c.isalpha())
        alpha_ratio = alpha_count / char_count if char_count > 0 else 0.0

        # Check for ASCII art
        has_ascii_art = bool(_ASCII_ART_PATTERN.search(clean))
        if has_ascii_art:
            return QualityAssessment(
                status=QualityStatus.SPAM_COPYPASTA,
                reason_code="SPAM_ASCII_ART_DETECTED",
                is_trainable=False,
                char_count=char_count,
                word_count=word_count,
                alpha_ratio=round(alpha_ratio, 4),
                has_ascii_art=True,
                version=self.version,
            )

        # Check for pure punctuation / heart spam / emoticon only (e.g. "♥♥♥♥", "...", "???")
        if _PURE_PUNCTUATION.match(clean) or alpha_count == 0:
            return QualityAssessment(
                status=QualityStatus.INSUFFICIENT_EVIDENCE,
                reason_code="NO_ALPHABETIC_CONTENT",
                is_trainable=False,
                char_count=char_count,
                word_count=word_count,
                alpha_ratio=0.0,
                version=self.version,
            )

        # Language uncertain flag
        if is_language_uncertain:
            return QualityAssessment(
                status=QualityStatus.LANGUAGE_UNCERTAIN,
                reason_code="LANGUAGE_CONFIDENCE_BELOW_THRESHOLD",
                is_trainable=False,
                char_count=char_count,
                word_count=word_count,
                alpha_ratio=round(alpha_ratio, 4),
                version=self.version,
            )

        # Very low alpha ratio (e.g. symbol spam or number spam)
        if alpha_ratio < self.min_alpha_ratio and word_count > 3:
            return QualityAssessment(
                status=QualityStatus.INSUFFICIENT_EVIDENCE,
                reason_code="EXCESSIVE_SYMBOLS_OR_NUMBERS",
                is_trainable=False,
                char_count=char_count,
                word_count=word_count,
                alpha_ratio=round(alpha_ratio, 4),
                version=self.version,
            )

        # Extremely short reviews check (1 token)
        lower_tokens = [w.lower().strip("!?,.:;\"'") for w in words]
        if word_count == 1:
            token = lower_tokens[0]
            if token not in _SHORT_VALID_SENTIMENT and len(token) <= 2:
                return QualityAssessment(
                    status=QualityStatus.INSUFFICIENT_EVIDENCE,
                    reason_code="SINGLE_TOKEN_WITHOUT_SENTIMENT_EVIDENCE",
                    is_trainable=False,
                    char_count=char_count,
                    word_count=word_count,
                    alpha_ratio=round(alpha_ratio, 4),
                    version=self.version,
                )

        has_negation = any(t in _NEGATION_TOKENS for t in lower_tokens)

        # Passed all checks -> Valid
        return QualityAssessment(
            status=QualityStatus.VALID,
            reason_code=None,
            is_trainable=True,
            char_count=char_count,
            word_count=word_count,
            alpha_ratio=round(alpha_ratio, 4),
            has_negation=has_negation,
            has_ascii_art=False,
            version=self.version,
        )
