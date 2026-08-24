"""
Translation Tool — MCP tool stub.

Provides multilingual banking support via translation API.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# Language names
LANGUAGES = {
    "en": "English", "es": "Spanish", "fr": "French", "de": "German",
    "zh": "Chinese", "ar": "Arabic", "hi": "Hindi", "pt": "Portuguese",
    "ja": "Japanese", "ko": "Korean", "it": "Italian", "ru": "Russian",
}


async def detect_language(text: str) -> dict:
    """Detect the language of input text."""
    logger.info("Detecting language for text: %s...", text[:50])

    # Stub: simple heuristic detection
    text_lower = text.lower()
    if any(w in text_lower for w in ["the", "is", "are", "what", "how"]):
        detected = "en"
    elif any(w in text_lower for w in ["el", "la", "los", "como", "que"]):
        detected = "es"
    elif any(w in text_lower for w in ["le", "la", "les", "comment", "que"]):
        detected = "fr"
    elif any(w in text_lower for w in ["der", "die", "das", "wie", "was"]):
        detected = "de"
    elif any(w in text_lower for w in ["什么", "怎么", "如何"]):
        detected = "zh"
    else:
        detected = "en"

    return {
        "detected_language": detected,
        "language_name": LANGUAGES.get(detected, "Unknown"),
        "confidence": 0.95,
        "supported": detected in LANGUAGES,
    }


async def translate_text(
    text: str,
    source_language: str,
    target_language: str,
) -> dict:
    """Translate text between languages."""
    logger.info("Translating from %s to %s", source_language, target_language)

    # Stub: return translated placeholder
    result = {
        "translation_id": str(uuid.uuid4()),
        "original_text": text,
        "translated_text": f"[Translated from {LANGUAGES.get(source_language, source_language)} to {LANGUAGES.get(target_language, target_language)}] {text}",
        "source_language": source_language,
        "target_language": target_language,
        "confidence": 0.92,
        "translated_at": datetime.utcnow().isoformat(),
    }

    logger.info("Translation complete: %s → %s", source_language, target_language)
    return result


async def get_supported_languages() -> dict:
    """Get list of supported languages."""
    return {
        "languages": [{"code": k, "name": v} for k, v in LANGUAGES.items()],
        "count": len(LANGUAGES),
    }
