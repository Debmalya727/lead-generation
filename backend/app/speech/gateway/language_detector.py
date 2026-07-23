"""
LanguageDetector — Detects spoken language and confidence score.
"""
from typing import Tuple, Optional
import logging

logger = logging.getLogger("backend.speech.gateway.language")


class LanguageDetector:
    """Identifies primary spoken language from transcript or audio header."""

    def detect_language(self, transcript: str, hinted_language: Optional[str] = None) -> Tuple[str, float]:
        """Detect language ISO code and confidence score."""
        if hinted_language:
            return hinted_language, 0.99

        # Basic language detection heuristics
        text_lower = transcript.lower()
        if any(w in text_lower for w in ["hola", "gracias", "por favor", "buenos"]):
            return "es", 0.98
        elif any(w in text_lower for w in ["bonjour", "merci", "oui"]):
            return "fr", 0.97
        elif any(w in text_lower for w in ["danke", "guten", "tag"]):
            return "de", 0.97
        else:
            return "en", 0.99


language_detector = LanguageDetector()
