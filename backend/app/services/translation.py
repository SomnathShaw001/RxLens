"""
Translation service for multilingual prescription support.
Supports Hindi, Bengali, Tamil, Telugu, Kannada, Marathi, Gujarati via Bhashini/IndicTrans2.
Falls back to Gemini multimodal translation when Bhashini is not configured.
"""
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    from google import genai
    _genai_available = True
except ImportError:
    _genai_available = False

SUPPORTED_LANGUAGES = {
    "hi": "Hindi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "mr": "Marathi",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "ur": "Urdu",
    "ml": "Malayalam",
    "or": "Odia",
    "en": "English",
}


async def translate_to_english(text: str, source_lang: str = "auto") -> str:
    """
    Translates prescription text to English using Gemini as primary fallback.
    When BHASHINI_API_KEY is configured (Phase 3), routes through Bhashini/IndicTrans2.
    """
    if not text or text.strip() == "":
        return text

    # If already English or no translation needed, pass through
    if source_lang == "en":
        return text

    bhashini_key = getattr(settings, "BHASHINI_API_KEY", None)
    if bhashini_key:
        return await _translate_via_bhashini(text, source_lang)

    return await _translate_via_gemini(text, source_lang)


async def _translate_via_gemini(text: str, source_lang: str) -> str:
    """Translate using Gemini when Bhashini is not configured."""
    api_key = settings.GEMINI_API_KEY
    if not api_key or api_key == "your-gemini-api-key-here" or not _genai_available:
        logger.warning("Translation skipped — Gemini API not configured.")
        return text

    lang_name = SUPPORTED_LANGUAGES.get(source_lang, source_lang)
    try:
        client = genai.Client(api_key=api_key)
        prompt = (
            f"Translate the following medical prescription text from {lang_name} to English. "
            f"Preserve drug names, dosages, and medical terminology exactly as they are written. "
            f"Only output the English translation, nothing else.\n\n"
            f"Text: {text}"
        )
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini translation failed: {e}")
        return text


async def _translate_via_bhashini(text: str, source_lang: str) -> str:
    """
    Translate via ULCA/Bhashini NMT API.
    Full implementation added when BHASHINI_USER_ID and BHASHINI_API_KEY are configured.
    """
    # TODO: Implement Bhashini ULCA API call
    # POST https://dhruva-api.bhashini.gov.in/services/inference/pipeline
    logger.info("Bhashini translation placeholder — implement with ULCA credentials.")
    return await _translate_via_gemini(text, source_lang)


def detect_language(text: str) -> str:
    """
    Simple heuristic language detection based on Unicode ranges.
    Returns ISO 639-1 language code.
    """
    if not text:
        return "en"

    # Devanagari (Hindi, Marathi)
    devanagari = sum(1 for c in text if "\u0900" <= c <= "\u097F")
    # Bengali
    bengali = sum(1 for c in text if "\u0980" <= c <= "\u09FF")
    # Tamil
    tamil = sum(1 for c in text if "\u0B80" <= c <= "\u0BFF")
    # Telugu
    telugu = sum(1 for c in text if "\u0C00" <= c <= "\u0C7F")
    # Kannada
    kannada = sum(1 for c in text if "\u0C80" <= c <= "\u0CFF")
    # Gujarati
    gujarati = sum(1 for c in text if "\u0A80" <= c <= "\u0AFF")
    # Arabic/Urdu
    arabic = sum(1 for c in text if "\u0600" <= c <= "\u06FF")

    scores = {
        "hi": devanagari,
        "bn": bengali,
        "ta": tamil,
        "te": telugu,
        "kn": kannada,
        "gu": gujarati,
        "ur": arabic,
    }

    max_lang = max(scores, key=scores.get)
    if scores[max_lang] > 3:
        return max_lang

    return "en"
