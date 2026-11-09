"""Unit tests for ReviewPreprocessor according to ML_SPECIFICATION.md Section 4.5."""

from app.ml.preprocessor import PREPROCESSOR_VERSION, ReviewPreprocessor


def test_preprocessor_version_and_defaults() -> None:
    preprocessor = ReviewPreprocessor()
    assert preprocessor.version == PREPROCESSOR_VERSION
    assert preprocessor.max_chars == 4096


def test_unicode_nfc_normalization() -> None:
    preprocessor = ReviewPreprocessor()
    # Decomposed e + acute accent (e\u0301) should become composed é (\u00e9)
    decomposed = "cafe\u0301"
    res = preprocessor.process(decomposed)
    assert res.normalized_text == "café"
    assert res.original_text == decomposed


def test_html_entity_unescaping() -> None:
    preprocessor = ReviewPreprocessor()
    text = "Great game &amp; smooth combat &lt;10/10&gt; &quot;masterpiece&quot;"
    res = preprocessor.process(text)
    assert res.normalized_text == 'Great game & smooth combat <10/10> "masterpiece"'


def test_bbcode_stripping() -> None:
    preprocessor = ReviewPreprocessor()
    bbcode_text = (
        "[h1]Best Game Ever[/h1]\n"
        "[b]Pros:[/b]\n"
        "[list]\n"
        "[*] Amazing graphics\n"
        "[*] [spoiler]Secret boss is hard[/spoiler]\n"
        "[/list]\n"
        "[quote]Must buy[/quote]"
    )
    res = preprocessor.process(bbcode_text)
    assert "[h1]" not in res.normalized_text
    assert "[/h1]" not in res.normalized_text
    assert "[b]" not in res.normalized_text
    assert "[spoiler]" not in res.normalized_text
    assert "Best Game Ever" in res.normalized_text
    assert "Secret boss is hard" in res.normalized_text
    assert "Must buy" in res.normalized_text


def test_url_masking() -> None:
    preprocessor = ReviewPreprocessor()
    text = "Check out our guide at https://steamcommunity.com/sharedfiles/filedetails/?id=12345 or http://example.org"
    res = preprocessor.process(text)
    assert "https://steamcommunity.com" not in res.normalized_text
    assert "http://example.org" not in res.normalized_text
    assert "[URL]" in res.normalized_text


def test_invisible_and_control_character_stripping() -> None:
    preprocessor = ReviewPreprocessor()
    # Text with null byte, bell char, and vertical tab, but keeping standard newline
    text = "Clean\x00 text\x07 with\x0b preserved\nnewline"
    res = preprocessor.process(text)
    assert "\x00" not in res.normalized_text
    assert "\x07" not in res.normalized_text
    assert "\x0b" not in res.normalized_text
    assert res.normalized_text == "Clean text with preserved\nnewline"


def test_whitespace_and_excessive_newline_collapsing() -> None:
    preprocessor = ReviewPreprocessor()
    text = "Line 1\r\n\r\n\r\n\r\n\r\nLine 2    with     spaces"
    res = preprocessor.process(text)
    assert "\r" not in res.normalized_text
    assert res.normalized_text == "Line 1\n\nLine 2 with spaces"


def test_character_truncation_and_flag() -> None:
    preprocessor = ReviewPreprocessor(max_chars=50)
    long_text = "A" * 100
    res = preprocessor.process(long_text)
    assert len(res.normalized_text) == 50
    assert res.char_count == 50
    assert res.is_truncated is True
    assert len(res.original_text) == 100


def test_empty_and_whitespace_only_text() -> None:
    preprocessor = ReviewPreprocessor()
    res = preprocessor.process("   \t  \n  ")
    assert res.normalized_text == ""
    assert res.char_count == 0
    assert res.word_count == 0
    assert res.is_truncated is False
