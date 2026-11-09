"""Unit tests for ReviewQualityAssessor according to ML_SPECIFICATION.md Section 4.5."""

from app.ml.quality import QUALITY_ENGINE_VERSION, QualityStatus, ReviewQualityAssessor


def test_quality_assessor_version() -> None:
    assessor = ReviewQualityAssessor()
    assert assessor.version == QUALITY_ENGINE_VERSION


def test_empty_text_assessment() -> None:
    assessor = ReviewQualityAssessor()
    assessment = assessor.assess("   \t  \n ")
    assert assessment.status == QualityStatus.EMPTY_TEXT
    assert assessment.is_trainable is False
    assert assessment.reason_code == "TEXT_EMPTY_OR_WHITESPACE"


def test_insufficient_evidence_single_symbol() -> None:
    assessor = ReviewQualityAssessor()
    assessment = assessor.assess("...")
    assert assessment.status == QualityStatus.INSUFFICIENT_EVIDENCE
    assert assessment.is_trainable is False
    assert assessment.reason_code == "NO_ALPHABETIC_CONTENT"


def test_insufficient_evidence_heart_profanity_flood() -> None:
    assessor = ReviewQualityAssessor()
    assessment = assessor.assess("♥♥♥♥♥♥♥♥♥♥♥♥♥♥♥♥♥♥♥♥")
    assert assessment.status == QualityStatus.INSUFFICIENT_EVIDENCE
    assert assessment.is_trainable is False


def test_spam_copypasta_ascii_art() -> None:
    assessor = ReviewQualityAssessor()
    ascii_art = "░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░\nShrek was here 10/10"
    assessment = assessor.assess(ascii_art)
    assert assessment.status == QualityStatus.SPAM_COPYPASTA
    assert assessment.is_trainable is False
    assert assessment.reason_code == "SPAM_ASCII_ART_DETECTED"


def test_preserves_valid_short_reviews() -> None:
    assessor = ReviewQualityAssessor()
    valid_short = ["Masterpiece", "Total garbage", "Not recommended", "Instant buy", "Trash"]
    for text in valid_short:
        res = assessor.assess(text)
        assert res.status == QualityStatus.VALID, f"Failed for '{text}': got {res.status}"
        assert res.is_trainable is True


def test_preserves_valid_long_reviews() -> None:
    assessor = ReviewQualityAssessor()
    text = (
        "The story is phenomenal, voice acting is top tier, and combat mechanics feel crisp. "
        "However, post-launch performance on PC was stuttery before the latest update."
    )
    res = assessor.assess(text)
    assert res.status == QualityStatus.VALID
    assert res.is_trainable is True
    assert res.reason_code is None


def test_language_uncertainty_flag() -> None:
    assessor = ReviewQualityAssessor()
    res = assessor.assess("ok fine", is_language_uncertain=True)
    assert res.status == QualityStatus.LANGUAGE_UNCERTAIN
    assert res.is_trainable is False
