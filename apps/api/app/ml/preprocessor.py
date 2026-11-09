import html
import re
import unicodedata
from typing import Final

from pydantic import BaseModel, ConfigDict, Field

PREPROCESSOR_VERSION: Final[str] = "v1.0.0"

# Matches URLs (http, https, www, steam community links)
_URL_PATTERN = re.compile(
    r"(?:https?://|www\.)[^\s/$.?#].[^\s]*",
    re.IGNORECASE,
)

# BBCode formatting tags commonly present in Steam reviews: [b], [/b], [h1], [code], etc.
_BBCODE_PATTERN = re.compile(
    r"\[/?(?:b|i|u|url|strike|spoiler|h1|h2|h3|noparse|hr|code|quote|list|\*)(?:=[^\]]*)?\]",
    re.IGNORECASE,
)

# Excessive whitespace and blank lines
_EXCESSIVE_NEWLINES = re.compile(r"\n{3,}")
_MULTIPLE_SPACES = re.compile(r"[^\S\r\n]+")

# Zero-width / control characters (except newline, tab)
_INVISIBLE_CHARS = re.compile(
    r"[\u200B-\u200D\uFEFF\u200E\u200F\u0000-\u0008\u000B\u000C\u000E-\u001F]"
)


class ProcessedText(BaseModel):
    """Immutable result of text preprocessing for model training and inference."""

    model_config = ConfigDict(frozen=True)

    original_text: str = Field(description="Unaltered verbatim raw input text")
    normalized_text: str = Field(description="Normalized text meeting the model contract")
    version: str = Field(default=PREPROCESSOR_VERSION, description="Preprocessing engine version")
    char_count: int = Field(ge=0, description="Character count of normalized text")
    word_count: int = Field(ge=0, description="Word count (whitespace-separated tokens)")
    is_truncated: bool = Field(default=False, description="True if text exceeded max_length")
    has_url: bool = Field(default=False, description="True if URLs were detected and masked")
    has_bbcode: bool = Field(default=False, description="True if BBCode tags were stripped")


class ReviewPreprocessor:
    """Resilient text preprocessing engine implementing SteamScoop normalization policy.

    Guarantees:
    - Verbatim raw text preservation.
    - Deterministic Unicode NFC normalization.
    - Safe HTML entity unescaping.
    - Configurable URL masking (`[URL]`) and BBCode stripping.
    - Casing, emojis, punctuation, and negation preservation for transformer semantics.
    - Bounded length truncation with explicit audit flags.
    """

    def __init__(
        self,
        max_chars: int = 4096,
        mask_urls: bool = True,
        url_placeholder: str = "[URL]",
        strip_bbcode: bool = True,
        version: str = PREPROCESSOR_VERSION,
    ) -> None:
        self.max_chars = max_chars
        self.mask_urls = mask_urls
        self.url_placeholder = url_placeholder
        self.strip_bbcode = strip_bbcode
        self.version = version

    def process(self, text: str | None) -> ProcessedText:
        """Preprocess review text into a normalized representation."""
        if text is None:
            return ProcessedText(
                original_text="",
                normalized_text="",
                version=self.version,
                char_count=0,
                word_count=0,
                is_truncated=False,
            )

        original = text

        # 1. Unicode NFC normalization
        norm = unicodedata.normalize("NFC", text)

        # 2. Strip zero-width and unprintable control characters
        norm = _INVISIBLE_CHARS.sub("", norm)

        # 3. HTML Entity decoding (e.g. &amp; -> &, &#39; -> ')
        norm = html.unescape(norm)

        # 4. Standardize line endings (\r\n -> \n, \r -> \n)
        norm = norm.replace("\r\n", "\n").replace("\r", "\n")

        # 5. Handle BBCode markup (Steam user reviews support [b], [h1], etc.)
        has_bbcode = bool(_BBCODE_PATTERN.search(norm))
        if self.strip_bbcode and has_bbcode:
            norm = _BBCODE_PATTERN.sub(" ", norm)

        # 6. Handle URLs
        has_url = bool(_URL_PATTERN.search(norm))
        if self.mask_urls and has_url:
            norm = _URL_PATTERN.sub(self.url_placeholder, norm)

        # 7. Collapse excessive horizontal spaces and blank lines
        norm = _MULTIPLE_SPACES.sub(" ", norm)
        norm = _EXCESSIVE_NEWLINES.sub("\n\n", norm)
        norm = norm.strip()

        # 8. Length truncation policy
        is_truncated = False
        if len(norm) > self.max_chars:
            norm = norm[: self.max_chars].rstrip()
            is_truncated = True

        words = norm.split()
        return ProcessedText(
            original_text=original,
            normalized_text=norm,
            version=self.version,
            char_count=len(norm),
            word_count=len(words),
            is_truncated=is_truncated,
            has_url=has_url,
            has_bbcode=has_bbcode,
        )
