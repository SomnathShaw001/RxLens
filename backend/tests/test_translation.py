"""Tests for translation service and language detection."""
import pytest
from app.services.translation import detect_language, translate_to_english


def test_english_detection():
    assert detect_language("Take 1 tablet daily") == "en"


def test_hindi_detection():
    text = "यह दवा खाने के बाद लें"  # Hindi (Devanagari)
    lang = detect_language(text)
    assert lang == "hi"


def test_tamil_detection():
    text = "இந்த மருந்தை தினமும் எடுக்கவும்"  # Tamil
    lang = detect_language(text)
    assert lang == "ta"


def test_english_passthrough():
    """translate_to_english should return the same string if source_lang is 'en'."""
    import asyncio
    result = asyncio.run(translate_to_english("Take daily", source_lang="en"))
    assert result == "Take daily"


def test_empty_string_passthrough():
    """Empty text should pass through without error."""
    import asyncio
    result = asyncio.run(translate_to_english("", source_lang="hi"))
    assert result == ""
