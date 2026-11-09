"""Unit tests for ReviewLanguageDetector according to ML_SPECIFICATION.md Section 4.6."""

from app.ml.language_detector import (
    ALL_RECOGNIZED_LANGUAGES,
    LANGUAGE_DETECTOR_VERSION,
    PRIMARY_SUPPORTED_LANGUAGES,
    ReviewLanguageDetector,
)


def test_detector_version_and_supported_languages() -> None:
    detector = ReviewLanguageDetector()
    assert detector.version == LANGUAGE_DETECTOR_VERSION
    assert "en" in PRIMARY_SUPPORTED_LANGUAGES
    assert "es" in ALL_RECOGNIZED_LANGUAGES


def test_detect_english_text() -> None:
    detector = ReviewLanguageDetector()
    text = (
        "This game is absolutely fantastic. The combat mechanics are polished, "
        "the graphics are stunning with ray tracing, and the story kept me hooked for hours."
    )
    result = detector.detect(text)
    assert result.language == "en"
    assert result.confidence >= 0.70
    assert result.is_uncertain is False


def test_detect_cyrillic_russian() -> None:
    detector = ReviewLanguageDetector()
    text = "Отличная игра, прекрасный сюжет и потрясающая графика в Найт-Сити."
    result = detector.detect(text)
    assert result.language == "ru"
    assert result.confidence >= 0.80
    assert result.is_uncertain is False


def test_detect_cjk_chinese() -> None:
    detector = ReviewLanguageDetector()
    text = "画面非常震撼，剧情也很有代入感，很喜欢夜之城的氛围！"
    result = detector.detect(text)
    assert result.language == "zh"
    assert result.confidence >= 0.80
    assert result.is_uncertain is False


def test_detect_hangul_korean() -> None:
    detector = ReviewLanguageDetector()
    text = "로그라이크 장르 중에서 최고의 완성도를 보여줍니다. 강력 추천합니다!"
    result = detector.detect(text)
    assert result.language == "ko"
    assert result.confidence >= 0.80
    assert result.is_uncertain is False


def test_detect_kana_japanese() -> None:
    detector = ReviewLanguageDetector()
    text = "ストーリーが最高で音楽も素晴らしい。絶対に遊ぶべき名作です。"
    result = detector.detect(text)
    assert result.language == "ja"
    assert result.confidence >= 0.80
    assert result.is_uncertain is False


def test_detect_spanish() -> None:
    detector = ReviewLanguageDetector()
    text = "Es un juego muy bueno con una historia increible y una banda sonora fantastica."
    result = detector.detect(text)
    assert result.language == "es"
    assert result.confidence >= 0.65
    assert result.is_uncertain is False


def test_detect_german() -> None:
    detector = ReviewLanguageDetector()
    text = "Das Spiel ist wirklich gut und macht viel Spass mit Freunden."
    result = detector.detect(text)
    assert result.language == "de"
    assert result.confidence >= 0.65
    assert result.is_uncertain is False


def test_low_confidence_uncertain_handling() -> None:
    detector = ReviewLanguageDetector(confidence_threshold=0.65)
    # Very short ambiguous text: should be marked uncertain
    result = detector.detect("ok")
    assert result.is_uncertain is True

    # Pure symbol / numbers
    result_sym = detector.detect("12345 67890 !@#$%")
    assert result_sym.is_uncertain is True
    assert result_sym.confidence < 0.65


def test_empty_string_detection() -> None:
    detector = ReviewLanguageDetector()
    result = detector.detect("")
    assert result.language == "unknown"
    assert result.confidence == 0.0
    assert result.is_uncertain is True
