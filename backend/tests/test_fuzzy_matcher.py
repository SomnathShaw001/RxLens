import pytest
from app.services.fuzzy_matcher import FuzzyDrugMatcher


def test_fuzzy_matcher_typo_resolution():
    matcher = FuzzyDrugMatcher()

    # TRD Section 4 example: "crocim" resolves to "Crocin"
    matched, ratio = matcher.match_drug("crocim")
    assert matched is not None
    assert matched["brand"] == "Crocin"
    assert matched["salt"] == "Paracetamol"
    assert ratio >= 0.80

    # Misspelled Augmentin
    matched, ratio = matcher.match_drug("augmntin")
    assert matched is not None
    assert matched["brand"] == "Augmentin"


def test_strength_validation():
    matcher = FuzzyDrugMatcher()
    matched, _ = matcher.match_drug("Crocin")
    assert matched is not None

    # Valid strength
    assert matcher.validate_drug_and_strength(matched, "500 mg") is True
    assert matcher.validate_drug_and_strength(matched, "650mg") is True

    # Invalid strength (hallucination guard)
    assert matcher.validate_drug_and_strength(matched, "30 mg") is False
    assert matcher.validate_drug_and_strength(matched, "9999 mg") is False
