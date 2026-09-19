import pytest
from app.services.confidence_engine import ConfidenceEngine


def test_confidence_formula_calculation():
    # 0.35*1.0 + 0.30*1.0 + 0.25*1.0 + 0.10*1.0 = 1.0 -> 100.0
    score, needs_review = ConfidenceEngine.calculate_field_score(
        ocr_signal=1.0,
        fuzzy_match_score=1.0,
        self_consistency=1.0,
        field_validity=1.0,
        is_handwritten=False,
        drug_matched_in_db=True,
        pair_valid_in_db=True,
    )
    assert score == 100.0
    assert needs_review is False


def test_printed_threshold_gate():
    # Printed prescription threshold is 85.
    # Score below 85 should force review.
    score, needs_review = ConfidenceEngine.calculate_field_score(
        ocr_signal=0.8,
        fuzzy_match_score=0.8,
        self_consistency=0.8,
        field_validity=1.0,
        is_handwritten=False, # printed
        drug_matched_in_db=True,
        pair_valid_in_db=True,
    )
    # Score = 100 * (0.35*0.8 + 0.30*0.8 + 0.25*0.8 + 0.10*1.0) = 100 * (0.28 + 0.24 + 0.20 + 0.10) = 82.0
    assert score == 82.0
    assert needs_review is True


def test_handwritten_threshold_gate():
    # Handwritten prescription threshold is 70.
    # Score: ocr=0.75, fuzzy=0.75, consistency=0.75, validity=1.0 -> 77.5 (>= 70 -> False)
    score, needs_review = ConfidenceEngine.calculate_field_score(
        ocr_signal=0.75,
        fuzzy_match_score=0.75,
        self_consistency=0.75,
        field_validity=1.0,
        is_handwritten=True,
        drug_matched_in_db=True,
        pair_valid_in_db=True,
    )
    assert score == 77.5
    assert needs_review is False


def test_unmatched_drug_forces_manual_review():
    # TRD Section 10.3: Drug name does not match any database entry -> Force manual review, whatever the score
    score, needs_review = ConfidenceEngine.calculate_field_score(
        ocr_signal=1.0,
        fuzzy_match_score=0.5,
        self_consistency=1.0,
        field_validity=0.0,
        is_handwritten=True,
        drug_matched_in_db=False, # unmatched
        pair_valid_in_db=False,
    )
    assert needs_review is True


def test_invalid_pair_forces_manual_review():
    # TRD Section 10.3: (drug, strength) pair does not exist -> Force manual review, whatever the score
    score, needs_review = ConfidenceEngine.calculate_field_score(
        ocr_signal=1.0,
        fuzzy_match_score=1.0,
        self_consistency=1.0,
        field_validity=0.0,
        is_handwritten=False,
        drug_matched_in_db=True,
        pair_valid_in_db=False, # invalid strength
    )
    assert needs_review is True
