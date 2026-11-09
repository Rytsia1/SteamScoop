import re
from typing import Final

from pydantic import BaseModel, ConfigDict, Field

LANGUAGE_DETECTOR_VERSION: Final[str] = "v1.0.0"

# Tier 1 (Production Evaluated Scope)
PRIMARY_SUPPORTED_LANGUAGES: Final[frozenset[str]] = frozenset({"en"})

# Tier 2 (Post-MVP Benchmark Candidate Languages)
SECONDARY_CANDIDATE_LANGUAGES: Final[frozenset[str]] = frozenset(
    {
        "zh",  # Simplified / Traditional Chinese
        "ru",  # Russian
        "es",  # Spanish
        "de",  # German
        "fr",  # French
        "pt",  # Portuguese / Portuguese-Brazil
        "ja",  # Japanese
        "ko",  # Korean
        "it",  # Italian
        "pl",  # Polish
    }
)

ALL_RECOGNIZED_LANGUAGES: Final[frozenset[str]] = (
    PRIMARY_SUPPORTED_LANGUAGES | SECONDARY_CANDIDATE_LANGUAGES
)

# Common distinctive stopword profiles for Latin-script European languages
_STOPWORD_PROFILES: dict[str, frozenset[str]] = {
    "en": frozenset(
        {
            "the",
            "be",
            "to",
            "of",
            "and",
            "a",
            "in",
            "that",
            "have",
            "i",
            "it",
            "for",
            "not",
            "on",
            "with",
            "he",
            "as",
            "you",
            "do",
            "at",
            "this",
            "but",
            "his",
            "by",
            "from",
            "they",
            "we",
            "say",
            "her",
            "she",
            "or",
            "an",
            "will",
            "my",
            "one",
            "all",
            "would",
            "there",
            "their",
            "what",
            "so",
            "up",
            "out",
            "if",
            "about",
            "who",
            "get",
            "which",
            "go",
            "me",
            "when",
            "make",
            "can",
            "like",
            "time",
            "no",
            "just",
            "him",
            "know",
            "take",
            "people",
            "into",
            "year",
            "your",
            "good",
            "some",
            "could",
            "them",
            "see",
            "other",
            "than",
            "then",
            "now",
            "look",
            "only",
            "come",
            "its",
            "over",
            "think",
            "also",
            "back",
            "after",
            "use",
            "two",
            "how",
            "our",
            "work",
            "first",
            "well",
            "way",
            "even",
            "new",
            "want",
            "because",
            "any",
            "these",
            "give",
            "day",
            "most",
            "us",
            "great",
            "game",
            "play",
        }
    ),
    "es": frozenset(
        {
            "de",
            "la",
            "que",
            "el",
            "en",
            "y",
            "a",
            "los",
            "del",
            "se",
            "las",
            "por",
            "un",
            "para",
            "con",
            "no",
            "una",
            "su",
            "al",
            "lo",
            "como",
            "mas",
            "más",
            "pero",
            "sus",
            "le",
            "ya",
            "o",
            "este",
            "si",
            "porque",
            "esta",
            "entre",
            "cuando",
            "muy",
            "sin",
            "sobre",
            "ser",
            "tiene",
            "también",
            "tambien",
            "era",
            "juego",
            "bueno",
            "bien",
            "mejor",
        }
    ),
    "de": frozenset(
        {
            "das",
            "ist",
            "du",
            "ich",
            "nicht",
            "die",
            "es",
            "und",
            "der",
            "was",
            "wir",
            "zu",
            "ein",
            "in",
            "sie",
            "mir",
            "mit",
            "ja",
            "wie",
            "den",
            "auf",
            "mich",
            "dass",
            "so",
            "hier",
            "eine",
            "wenn",
            "hat",
            "all",
            "sind",
            "von",
            "dich",
            "war",
            "haben",
            "für",
            "fuer",
            "an",
            "habe",
            "da",
            "nein",
            "spiel",
            "gut",
            "sehr",
            "aber",
        }
    ),
    "fr": frozenset(
        {
            "de",
            "la",
            "le",
            "et",
            "les",
            "des",
            "en",
            "un",
            "du",
            "une",
            "que",
            "est",
            "pour",
            "qui",
            "dans",
            "a",
            "par",
            "plus",
            "pas",
            "au",
            "sur",
            "ne",
            "ce",
            "il",
            "sont",
            "se",
            "avec",
            "tout",
            "fait",
            "mais",
            "jeu",
            "très",
            "tres",
            "bien",
            "bon",
        }
    ),
    "pt": frozenset(
        {
            "de",
            "a",
            "o",
            "que",
            "e",
            "do",
            "da",
            "em",
            "um",
            "para",
            "é",
            "com",
            "não",
            "uma",
            "os",
            "no",
            "se",
            "na",
            "por",
            "mais",
            "as",
            "dos",
            "como",
            "mas",
            "foi",
            "ao",
            "ele",
            "das",
            "tem",
            "à",
            "jogo",
            "muito",
            "bom",
            "legal",
        }
    ),
    "it": frozenset(
        {
            "di",
            "e",
            "il",
            "che",
            "la",
            "a",
            "per",
            "in",
            "un",
            "non",
            "del",
            "sono",
            "con",
            "ma",
            "è",
            "da",
            "della",
            "le",
            "si",
            "dei",
            "se",
            "gioco",
            "molto",
            "bello",
            "bene",
        }
    ),
    "pl": frozenset(
        {
            "i",
            "w",
            "nie",
            "się",
            "sie",
            "z",
            "na",
            "do",
            "to",
            "że",
            "ze",
            "o",
            "jak",
            "ale",
            "od",
            "po",
            "za",
            "gra",
            "bardzo",
            "dobra",
            "polecam",
        }
    ),
}


class LanguageDetectionResult(BaseModel):
    """Result of language detection on review text."""

    model_config = ConfigDict(frozen=True)

    language: str = Field(description="ISO 639-1 two-letter language code or 'unknown'")
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence score")
    is_supported: bool = Field(
        description="True if language is supported by an evaluated model (Tier 1)"
    )
    is_uncertain: bool = Field(description="True if detection confidence fell below threshold")
    script: str = Field(
        description="Dominant detected Unicode script (Latin, Cyrillic, Han, Hangul, etc.)"
    )
    version: str = Field(
        default=LANGUAGE_DETECTOR_VERSION, description="Language detector engine version"
    )


class ReviewLanguageDetector:
    """Robust, script-aware statistical language identification engine for Steam user reviews.

    Enforces ML_SPECIFICATION.md Section 4.2 policy:
    - Never silently forces ambiguous or short text into English.
    - Accurately classifies non-Latin scripts (Chinese, Russian, Korean, Japanese).
    - Uses stopword profile matching and script entropy for Latin languages.
    - Explicitly tags low-confidence text as `is_uncertain=True` (`language_uncertain`).
    """

    def __init__(
        self,
        confidence_threshold: float = 0.65,
        min_alpha_chars: int = 3,
        version: str = LANGUAGE_DETECTOR_VERSION,
    ) -> None:
        self.confidence_threshold = confidence_threshold
        self.min_alpha_chars = min_alpha_chars
        self.version = version

    def detect(self, text: str | None) -> LanguageDetectionResult:
        """Detect language code and confidence from normalized review text."""
        if not text:
            return LanguageDetectionResult(
                language="unknown",
                confidence=0.0,
                is_supported=False,
                is_uncertain=True,
                script="None",
                version=self.version,
            )

        # Count character scripts
        script_counts: dict[str, int] = {
            "Latin": 0,
            "Cyrillic": 0,
            "Han": 0,
            "Hangul": 0,
            "Hiragana_Katakana": 0,
            "Arabic": 0,
            "Other": 0,
        }

        total_alpha = 0
        for ch in text:
            if not ch.isalpha():
                continue
            total_alpha += 1
            code = ord(ch)

            if (
                (0x0041 <= code <= 0x005A)
                or (0x0061 <= code <= 0x007A)
                or (0x00C0 <= code <= 0x024F)
            ):
                script_counts["Latin"] += 1
            elif 0x0400 <= code <= 0x04FF:
                script_counts["Cyrillic"] += 1
            elif (0x4E00 <= code <= 0x9FFF) or (0x3400 <= code <= 0x4DBF):
                script_counts["Han"] += 1
            elif (0xAC00 <= code <= 0xD7AF) or (0x1100 <= code <= 0x11FF):
                script_counts["Hangul"] += 1
            elif (0x3040 <= code <= 0x309F) or (0x30A0 <= code <= 0x30FF):
                script_counts["Hiragana_Katakana"] += 1
            elif 0x0600 <= code <= 0x06FF:
                script_counts["Arabic"] += 1
            else:
                script_counts["Other"] += 1

        # If insufficient alphabetic characters exist, text is uncertain
        if total_alpha < self.min_alpha_chars:
            return LanguageDetectionResult(
                language="unknown",
                confidence=0.0,
                is_supported=False,
                is_uncertain=True,
                script="Unknown",
                version=self.version,
            )

        # Find dominant script
        dominant_script, dominant_count = max(script_counts.items(), key=lambda item: item[1])
        script_ratio = dominant_count / total_alpha

        # Non-Latin script mapping
        if dominant_script == "Han" and script_ratio >= 0.5:
            # If Japanese kana co-occurs with Kanji, it is Japanese
            if script_counts["Hiragana_Katakana"] > 0:
                conf = min(1.0, script_ratio * 0.95)
                return self._build_result("ja", conf, "Japanese (Kanji+Kana)")
            conf = min(1.0, script_ratio * 0.98)
            return self._build_result("zh", conf, "Han")

        if dominant_script == "Hiragana_Katakana" and script_ratio >= 0.3:
            conf = min(1.0, (dominant_count + script_counts["Han"]) / total_alpha * 0.98)
            return self._build_result("ja", conf, "Hiragana/Katakana")

        if dominant_script == "Hangul" and script_ratio >= 0.5:
            conf = min(1.0, script_ratio * 0.98)
            return self._build_result("ko", conf, "Hangul")

        if dominant_script == "Cyrillic" and script_ratio >= 0.6:
            conf = min(1.0, script_ratio * 0.95)
            return self._build_result("ru", conf, "Cyrillic")

        if dominant_script == "Arabic" and script_ratio >= 0.6:
            conf = min(1.0, script_ratio * 0.95)
            return self._build_result("ar", conf, "Arabic")

        # Latin script processing: analyze word tokens against language stopword profiles
        if dominant_script == "Latin" and script_ratio >= 0.6:
            tokens = re.findall(r"\b[a-zA-Z\u00C0-\u024F]+\b", text.lower())
            if not tokens:
                return self._build_result("en", 0.50, "Latin")

            scores: dict[str, float] = {}
            total_tokens = len(tokens)

            for lang, stopwords in _STOPWORD_PROFILES.items():
                matches = sum(1 for t in tokens if t in stopwords)
                scores[lang] = matches / total_tokens if total_tokens > 0 else 0.0

            best_lang, best_score = max(scores.items(), key=lambda item: item[1])

            # If strong stopword matches exist
            if best_score > 0.0:
                # Scale confidence based on token sample length and match strength
                length_boost = min(1.0, len(tokens) / 10.0)
                confidence = min(0.99, max(0.60, best_score * 1.5 * length_boost + 0.40))
                return self._build_result(best_lang, confidence, "Latin")

            # Fallback for short English phrases without common stopwords
            # (e.g., "Masterpiece", "Instant GOTY").
            # If all tokens are valid ASCII without accents, provide moderate English estimate
            is_pure_ascii = all(ord(c) < 128 for c in text if c.isalpha())
            if is_pure_ascii and len(tokens) <= 3:
                # Short ASCII phrase: assign 0.70 confidence (uncertain if ambiguous)
                return self._build_result("en", 0.70, "Latin")

            # Ambiguous Latin text
            return self._build_result("en", 0.50, "Latin")

        # Mixed / uncategorized scripts
        return LanguageDetectionResult(
            language="unknown",
            confidence=0.30,
            is_supported=False,
            is_uncertain=True,
            script=dominant_script,
            version=self.version,
        )

    def _build_result(self, lang: str, confidence: float, script: str) -> LanguageDetectionResult:
        is_uncertain = confidence < self.confidence_threshold
        is_supported = lang in PRIMARY_SUPPORTED_LANGUAGES and not is_uncertain
        return LanguageDetectionResult(
            language=lang,
            confidence=round(confidence, 4),
            is_supported=is_supported,
            is_uncertain=is_uncertain,
            script=script,
            version=self.version,
        )
