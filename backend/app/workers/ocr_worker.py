import logging
from typing import Optional
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.prescriptions import Prescription, PrescriptionField
from app.models.medications import Medication
from app.services.gemini_ocr import GeminiOCRService
from app.services.fuzzy_matcher import FuzzyDrugMatcher
from app.services.confidence_engine import ConfidenceEngine
from app.services.translation import translate_to_english, detect_language

logger = logging.getLogger(__name__)


async def process_prescription_job(
    prescription_id: str,
    image_path: str,
    lang_hint: str = "en",
    is_handwritten: bool = True
):
    """
    Full async OCR pipeline:
    1. Extract with Gemini multimodal OCR
    2. Detect & translate to English
    3. Fuzzy-match drug names against reference DB
    4. Score confidence with TRD Section 10 formula
    5. Gate: auto-accept or flag for human review
    6. Persist all fields and medications
    """
    logger.info(f"Processing prescription {prescription_id}")
    matcher = FuzzyDrugMatcher()

    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Prescription).where(Prescription.id == prescription_id)
            )
            prescription = result.scalar_one_or_none()
            if not prescription:
                logger.error(f"Prescription {prescription_id} not found")
                return

            prescription.status = "processing"
            await session.commit()

            # Step 1: Gemini OCR extraction
            extraction = await GeminiOCRService.extract_prescription_data(
                image_path=image_path,
                lang_hint=lang_hint
            )

            # Step 2: Translate full transcription if non-English
            full_text = extraction.get("full_transcription_en", "")
            detected_lang = extraction.get("detected_language", lang_hint or "en")
            if detected_lang != "en":
                full_text = await translate_to_english(full_text, detected_lang)

            medications_data = extraction.get("medications", [])
            field_scores = []
            field_reviews = []

            # Step 3-5: Process each medication entity
            for med in medications_data:
                raw_drug = med.get("drug_name", "")
                strength = med.get("strength", "")
                dose = med.get("dosage", "")
                freq = med.get("frequency", "")
                duration = med.get("duration", "")
                route = med.get("route", "")
                raw_text = med.get("raw_text", "")
                ocr_signal = float(med.get("estimated_confidence", 0.8))

                # Translate non-English drug names
                if detected_lang != "en" and raw_drug:
                    raw_drug = await translate_to_english(raw_drug, detected_lang)

                # Fuzzy match against drug reference database
                matched_drug, fuzzy_ratio = matcher.match_drug(raw_drug)
                drug_matched = matched_drug is not None
                normalized_name = matched_drug["brand"] if matched_drug else raw_drug
                salt = matched_drug["salt"] if matched_drug else None
                rxcui = matched_drug["rxcui"] if matched_drug else None

                # Validate strength existence in reference
                pair_valid = matcher.validate_drug_and_strength(matched_drug, strength)

                # TRD Section 10 confidence scoring
                score, needs_review = ConfidenceEngine.calculate_field_score(
                    ocr_signal=ocr_signal,
                    fuzzy_match_score=fuzzy_ratio,
                    self_consistency=0.9 if drug_matched else 0.5,
                    field_validity=1.0 if pair_valid else 0.0,
                    is_handwritten=is_handwritten,
                    drug_matched_in_db=drug_matched,
                    pair_valid_in_db=pair_valid
                )

                field_scores.append(score)
                field_reviews.append(needs_review)

                # Persist field record
                field = PrescriptionField(
                    prescription_id=prescription_id,
                    type="medication",
                    raw_text=raw_text or f"{raw_drug} {strength}",
                    translated_text=f"{normalized_name} {strength}",
                    value=f"{normalized_name} | {strength} | {dose} | {freq} | {duration} | {route}",
                    confidence=score,
                    bbox=[0, 0, 100, 100],
                    verified=not needs_review
                )
                session.add(field)

                # Persist medication entity
                medication = Medication(
                    profile_id=prescription.profile_id,
                    prescription_id=prescription_id,
                    drug_name=normalized_name,
                    rxcui=rxcui,
                    salt=salt,
                    strength=strength,
                    dose=dose,
                    frequency=freq,
                    duration=duration,
                    route=route
                )
                session.add(medication)

            # Step 6: Aggregate and persist final prescription state
            overall_score, any_needs_review = ConfidenceEngine.calculate_prescription_overall(
                field_scores, field_reviews
            )

            prescription.overall_confidence = overall_score
            prescription.needs_review = any_needs_review
            prescription.status = "completed"

            await session.commit()
            logger.info(f"Prescription {prescription_id} completed — confidence={overall_score:.1f}, needs_review={any_needs_review}")

        except Exception as e:
            logger.exception(f"Error processing prescription {prescription_id}: {e}")
            await session.rollback()
            try:
                result = await session.execute(
                    select(Prescription).where(Prescription.id == prescription_id)
                )
                p = result.scalar_one_or_none()
                if p:
                    p.status = "failed"
                    await session.commit()
            except Exception:
                pass
