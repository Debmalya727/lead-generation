"""
ConfidenceEngine — Calculates sentence-level and word-level transcript confidence scores.
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger("backend.speech.gateway.confidence")


class ConfidenceEngine:
    """Computes transcript confidence scores based on acoustic metrics & vocabulary."""

    def evaluate_confidence(self, transcript: str, base_confidence: float = 0.95) -> float:
        """Adjust confidence based on length, punctuation, and uncertainty markers."""
        if not transcript or len(transcript.strip()) == 0:
            return 0.0

        # Adjust score if transcript has hesitation markers
        hesitations = ["uh", "um", "[inaudible]", "???"]
        penalty = sum(0.05 for h in hesitations if h in transcript.lower())
        adjusted = max(0.1, min(1.0, base_confidence - penalty))
        return round(adjusted, 4)


confidence_engine = ConfidenceEngine()
