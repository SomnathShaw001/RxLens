from typing import Dict, Any, Tuple
from app.core.config import settings


class ConfidenceEngine:
    """
    Implements the Confidence Scoring Algorithm defined in RxLens TRD Section 10:
    score = 100 * (0.35 * ocr + 0.30 * fuzzy + 0.25 * consistency + 0.10 * validity)

    Thresholds:
    - Printed prescription, field score below 85 -> Force manual review
    - Handwritten prescription, field score below 70 -> Force manual review
    - Drug name does not match any database entry -> Force manual review, whatever the score
    - (drug, strength) pair does not exist -> Force manual review, whatever the score
    """

    WEIGHT_OCR = 0.35
    WEIGHT_FUZZY = 0.30
    WEIGHT_CONSISTENCY = 0.25
    WEIGHT_VALIDITY = 0.10

    @classmethod
    def calculate_field_score(
        cls,
        ocr_signal: float,
        fuzzy_match_score: float,
        self_consistency: float,
        field_validity: float,
        is_handwritten: bool = True,
        drug_matched_in_db: bool = True,
        pair_valid_in_db: bool = True,
    ) -> Tuple[float, bool]:
        """
        Calculates confidence score (0-100) and returns (score, needs_review).
        """
        # Clamp inputs to [0.0, 1.0]
        ocr = max(0.0, min(1.0, float(ocr_signal)))
        fuzzy = max(0.0, min(1.0, float(fuzzy_match_score)))
        consistency = max(0.0, min(1.0, float(self_consistency)))
        validity = 1.0 if field_validity >= 1.0 else 0.0

        raw_score = 100.0 * (
            cls.WEIGHT_OCR * ocr
            + cls.WEIGHT_FUZZY * fuzzy
            + cls.WEIGHT_CONSISTENCY * consistency
            + cls.WEIGHT_VALIDITY * validity
        )
        score = round(raw_score, 2)

        # Section 10.3 Threshold rules
        threshold = (
            settings.CONFIDENCE_THRESHOLD_HANDWRITTEN
            if is_handwritten
            else settings.CONFIDENCE_THRESHOLD_PRINTED
        )

        needs_review = False

        # Rule 1: Below threshold
        if score < threshold:
            needs_review = True

        # Rule 2: Drug name does not match any database entry
        if not drug_matched_in_db:
            needs_review = True

        # Rule 3: (drug, strength) pair does not exist in reference data
        if not pair_valid_in_db:
            needs_review = True

        return score, needs_review

    @classmethod
    def calculate_prescription_overall(
        cls, field_scores: list[float], field_reviews: list[bool]
    ) -> Tuple[float, bool]:
        """
        Calculates the aggregate prescription confidence.
        If any critical field needs review, the prescription needs review.
        """
        if not field_scores:
            return 0.0, True

        avg_score = round(sum(field_scores) / len(field_scores), 2)
        needs_review = any(field_reviews)
        return avg_score, needs_review
